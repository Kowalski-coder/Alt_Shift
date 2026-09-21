import asyncio
import ctypes
import fcntl
import os
from pathlib import Path
import pwd
import struct
import subprocess
import time

try:
    import decky_plugin
    logger = decky_plugin.logger
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("Alt_Shift")

# Linux uinput ioctl constants
UI_DEV_CREATE = 0x5501
UI_DEV_DESTROY = 0x5502
UI_SET_EVBIT = 0x40045564
UI_SET_KEYBIT = 0x40045565
UI_DEV_SETUP = 0x405c5503

EV_SYN = 0x00
EV_KEY = 0x01
SYN_REPORT = 0

KEY_LEFTSHIFT = 42
KEY_LEFTALT = 56

class InputId(ctypes.Structure):
    _fields_ = [
        ("bustype", ctypes.c_uint16),
        ("vendor", ctypes.c_uint16),
        ("product", ctypes.c_uint16),
        ("version", ctypes.c_uint16),
    ]

class UInputSetup(ctypes.Structure):
    _fields_ = [
        ("id", InputId),
        ("name", ctypes.c_char * 80),
        ("ff_effects_max", ctypes.c_uint32),
    ]

libc = None
try:
    libc = ctypes.CDLL("libc.so.6")
    libc.setenv.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int]
except Exception as e:
    logger.warning(f"Could not load libc.so.6: {e}")

# X11 / XKB ctypes definitions
libX11 = None
try:
    libX11 = ctypes.CDLL("libX11.so.6")

    class XkbStateRec(ctypes.Structure):
        _fields_ = [
            ("group", ctypes.c_ubyte),
            ("locked_group", ctypes.c_ubyte),
            ("base_group", ctypes.c_short),
            ("latched_group", ctypes.c_short),
            ("mods", ctypes.c_ubyte),
            ("base_mods", ctypes.c_ubyte),
            ("latched_mods", ctypes.c_ubyte),
            ("locked_mods", ctypes.c_ubyte),
            ("compat_state", ctypes.c_ubyte),
            ("grab_mods", ctypes.c_ubyte),
            ("compat_grab_mods", ctypes.c_ubyte),
            ("lookup_mods", ctypes.c_ubyte),
            ("compat_lookup_mods", ctypes.c_ubyte),
            ("ptr_buttons", ctypes.c_ushort),
        ]

    libX11.XOpenDisplay.argtypes = [ctypes.c_char_p]
    libX11.XOpenDisplay.restype = ctypes.c_void_p

    libX11.XkbGetState.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.POINTER(XkbStateRec)]
    libX11.XkbGetState.restype = ctypes.c_int

    libX11.XkbLockGroup.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_uint]
    libX11.XkbLockGroup.restype = ctypes.c_int

    libX11.XFlush.argtypes = [ctypes.c_void_p]
    libX11.XFlush.restype = ctypes.c_int

    libX11.XCloseDisplay.argtypes = [ctypes.c_void_p]
    libX11.XCloseDisplay.restype = ctypes.c_int
except Exception as e:
    logger.warning(f"Could not load libX11.so.6: {e}")

uinput_fd = -1
current_cached_kde_layout = -1
current_active_language = "us"
gamescope_wayland_layout = 0
last_is_desktop = None
kde_layout_map = {}

def get_user_info():
    username = os.environ.get("DECKY_USER")
    if not username:
        try:
            import decky_plugin
            if hasattr(decky_plugin, "DECKY_USER") and decky_plugin.DECKY_USER:
                username = decky_plugin.DECKY_USER
        except Exception:
            pass
    if not username:
        for p in Path("/run/user").glob("*"):
            if p.name.isdigit() and int(p.name) >= 1000:
                try:
                    username = pwd.getpwuid(int(p.name)).pw_name
                    break
                except Exception:
                    pass
    if not username:
        for p in Path("/home").glob("*"):
            if p.is_dir() and not p.name.startswith("."):
                try:
                    st = p.stat()
                    if st.st_uid >= 1000:
                        username = p.name
                        break
                except Exception:
                    pass
    if not username:
        try:
            username = pwd.getpwuid(1000).pw_name
        except Exception:
            username = "deck"

    try:
        pw = pwd.getpwnam(username)
        return pw.pw_name, pw.pw_uid, pw.pw_gid, pw.pw_dir
    except Exception:
        return username, 1000, 1000, f"/home/{username}"

def call_kde_dbus(member: str, sig: str = "", arg: str = ""):
    username, uid, gid, homedir = get_user_info()
    bus_path = f"/run/user/{uid}/bus"
    if not os.path.exists(bus_path):
        return False, ""

    env = {
        "HOME": homedir,
        "USER": username,
        "LOGNAME": username,
        "XDG_RUNTIME_DIR": f"/run/user/{uid}",
        "DBUS_SESSION_BUS_ADDRESS": f"unix:path={bus_path}",
        "PATH": "/usr/local/bin:/usr/bin:/bin"
    }

    kwargs = {"env": env, "capture_output": True, "text": True, "timeout": 0.4}
    if os.getuid() == 0:
        kwargs["user"] = uid
        kwargs["group"] = gid

    cmd = [
        "busctl", "--user", "call",
        "org.kde.keyboard", "/Layouts", "org.kde.KeyboardLayouts",
        member
    ]
    if sig and arg:
        cmd.extend([sig, arg])

    try:
        res = subprocess.run(cmd, **kwargs)
        if res.returncode == 0:
            return True, res.stdout.strip()
    except Exception:
        pass

    try:
        qcmd = ["qdbus", "org.kde.keyboard", "/Layouts", member]
        if arg:
            qcmd.append(arg)
        res = subprocess.run(qcmd, **kwargs)
        if res.returncode == 0:
            return True, res.stdout.strip()
    except Exception:
        pass

    return False, ""

def open_x11_display(dpy_str: str = ":0"):
    if not libX11:
        return None

    username, uid, gid, homedir = get_user_info()
    candidates = []
    for p in Path(f"/run/user/{uid}").glob("xauth*"):
        candidates.append(str(p))
    for p in Path("/run/user").glob("*/xauth*"):
        candidates.append(str(p))
    for p in Path("/tmp").glob("xauth*"):
        candidates.append(str(p))
    for p in Path("/home").glob("*/.Xauthority"):
        candidates.append(str(p))
    candidates.append(f"{homedir}/.Xauthority")

    current_xauth = os.environ.get("XAUTHORITY")
    if current_xauth:
        candidates.insert(0, current_xauth)

    for xauth in candidates:
        if not os.path.exists(xauth):
            continue
        try:
            if libc:
                libc.setenv(b"XAUTHORITY", xauth.encode("utf-8"), 1)
            os.environ["XAUTHORITY"] = xauth
            dpy = libX11.XOpenDisplay(dpy_str.encode("utf-8"))
            if dpy:
                return dpy
        except Exception:
            pass

    return None

def get_kde_target_layout(lang: str) -> int:
    global kde_layout_map
    try:
        ok, out = call_kde_dbus("getLayoutsList")
        if ok and "a(sss)" in out:
            import re
            matches = re.findall(r"\"([^\"]*)\"", out)
            layouts = [matches[i].lower() for i in range(0, len(matches), 3)]
            mapping = {}
            for idx, l in enumerate(layouts):
                if l.startswith("us") or l.startswith("en"):
                    mapping["us"] = idx
                elif l.startswith("ru"):
                    mapping["ru"] = idx
            if "us" in mapping:
                kde_layout_map["us"] = mapping["us"]
            if "ru" in mapping:
                kde_layout_map["ru"] = mapping["ru"]
    except Exception:
        pass
    return kde_layout_map.get(lang, 1 if lang == "ru" else 0)

def is_desktop_mode() -> bool:
    try:
        res = subprocess.run(["pgrep", "-f", "plasmashell|kwin_x11|kwin_wayland|kwin|startplasma"], capture_output=True, timeout=0.2)
        if res.returncode == 0:
            return True
        res_gs = subprocess.run(["pgrep", "-x", "gamescope"], capture_output=True, timeout=0.2)
        if res_gs.returncode == 0:
            return False
        return True
    except Exception:
        return False

def get_active_x11_group() -> int:
    if not libX11:
        return None

    displays = []
    if os.environ.get("DISPLAY"):
        displays.append(os.environ["DISPLAY"])
    for d in [":0", ":1"]:
        if d not in displays:
            displays.append(d)

    for dpy_str in displays:
        dpy = open_x11_display(dpy_str)
        if dpy:
            try:
                st = XkbStateRec()
                if libX11.XkbGetState(dpy, 0x0100, ctypes.byref(st)) == 0:
                    grp = st.group
                    libX11.XCloseDisplay(dpy)
                    return grp
                libX11.XCloseDisplay(dpy)
            except Exception:
                pass
    return None

def set_x11_layout_group(lang: str) -> bool:
    if not libX11:
        return False

    target_group = 1 if lang == "ru" else 0
    displays = []
    if os.environ.get("DISPLAY"):
        displays.append(os.environ["DISPLAY"])
    for d in [":0", ":1"]:
        if d not in displays:
            displays.append(d)

    success = False
    for dpy_str in displays:
        dpy = open_x11_display(dpy_str)
        if dpy:
            try:
                st = XkbStateRec()
                if libX11.XkbGetState(dpy, 0x0100, ctypes.byref(st)) == 0:
                    if st.group != target_group:
                        libX11.XkbLockGroup(dpy, 0x0100, target_group)
                        libX11.XFlush(dpy)
                    success = True
                libX11.XCloseDisplay(dpy)
            except Exception as e:
                logger.debug(f"X11 display {dpy_str} error: {e}")
    return success

def init_uinput_device():
    global uinput_fd
    if uinput_fd >= 0:
        return
    try:
        fd = os.open("/dev/uinput", os.O_WRONLY | os.O_NONBLOCK)
        fcntl.ioctl(fd, UI_SET_EVBIT, EV_KEY)
        fcntl.ioctl(fd, UI_SET_KEYBIT, KEY_LEFTALT)
        fcntl.ioctl(fd, UI_SET_KEYBIT, KEY_LEFTSHIFT)

        setup = UInputSetup()
        setup.id.bustype = 0x03
        setup.id.vendor = 0x28de
        setup.id.product = 0x1205
        setup.id.version = 1
        setup.name = b"SteamDeck-AltShift-Trigger"

        fcntl.ioctl(fd, UI_DEV_SETUP, setup)
        fcntl.ioctl(fd, UI_DEV_CREATE)
        uinput_fd = fd
        logger.info("UInput layout switch trigger initialized.")
    except Exception as e:
        logger.error(f"Failed to create UInput trigger: {e}")

def destroy_uinput_device():
    global uinput_fd
    if uinput_fd >= 0:
        try:
            fcntl.ioctl(uinput_fd, UI_DEV_DESTROY)
            os.close(uinput_fd)
        except Exception:
            pass
        uinput_fd = -1

def emit_raw_event(type_, code, val):
    global uinput_fd
    if uinput_fd < 0:
        init_uinput_device()
    if uinput_fd < 0:
        return
    t = time.time()
    sec = int(t)
    usec = int((t - sec) * 1_000_000)
    data = struct.pack("qqHHi", sec, usec, type_, code, val)
    os.write(uinput_fd, data)

def emit_alt_shift():
    emit_raw_event(EV_KEY, KEY_LEFTALT, 1)
    emit_raw_event(EV_SYN, SYN_REPORT, 0)
    time.sleep(0.005)
    emit_raw_event(EV_KEY, KEY_LEFTSHIFT, 1)
    emit_raw_event(EV_SYN, SYN_REPORT, 0)
    time.sleep(0.01)
    emit_raw_event(EV_KEY, KEY_LEFTSHIFT, 0)
    emit_raw_event(EV_SYN, SYN_REPORT, 0)
    time.sleep(0.005)
    emit_raw_event(EV_KEY, KEY_LEFTALT, 0)
    emit_raw_event(EV_SYN, SYN_REPORT, 0)

def sync_layout(lang: str):
    global current_cached_kde_layout, current_active_language, gamescope_wayland_layout, last_is_desktop
    target_idx = 1 if (lang == "ru" or lang == 1) else 0
    lang_str = "ru" if target_idx == 1 else "us"

    in_desktop = is_desktop_mode()

    if last_is_desktop is not None and last_is_desktop != in_desktop:
        current_cached_kde_layout = -1
        gamescope_wayland_layout = 0
        current_active_language = "us"
        logger.info(f"Mode changed: Desktop={in_desktop}. Gamescope Wayland state reset to 0 (US)")
    last_is_desktop = in_desktop

    if in_desktop:
        current_active_language = lang_str
        try:
            kde_target = get_kde_target_layout(lang_str)
            if current_cached_kde_layout != kde_target:
                ok, out = call_kde_dbus("setLayout", "u", str(kde_target))
                if ok:
                    current_cached_kde_layout = kde_target
                    logger.info(f"KDE DBus: setLayout({kde_target}) -> {lang_str}")
        except Exception as e:
            logger.debug(f"KDE layout sync error: {e}")
        set_x11_layout_group(lang_str)
    else:
        set_x11_layout_group(lang_str)
        active_grp = get_active_x11_group()
        if active_grp is not None and active_grp != target_idx:
            logger.info(f"Gamescope: active group is {active_grp}, target is {target_idx} ({lang_str}), syncing via Alt+Shift")
            emit_alt_shift()
            gamescope_wayland_layout = target_idx
        elif gamescope_wayland_layout != target_idx:
            logger.info(f"Gamescope: switching Wayland layout from {gamescope_wayland_layout} to {target_idx} ({lang_str})")
            emit_alt_shift()
            gamescope_wayland_layout = target_idx
        current_active_language = lang_str

def auto_setup_system_xkb():
    try:
        # Cleanup any unwanted system config files
        for bad_path in [
            Path("/etc/X11/xorg.conf.d/00-keyboard.conf"),
            Path("/etc/environment.d/10-xkb.conf")
        ]:
            if bad_path.exists():
                try:
                    bad_path.unlink()
                except Exception:
                    pass

        username, uid, gid, homedir = get_user_info()

        # User configurations in /home/*
        for home in Path("/home").glob("*"):
            if home.is_dir() and not home.name.startswith("."):
                try:
                    stat = home.stat()
                    u_uid, u_gid = stat.st_uid, stat.st_gid

                    # User environment.d
                    env_d = home / ".config" / "environment.d"
                    env_d.mkdir(parents=True, exist_ok=True)
                    env_file = env_d / "10-xkb.conf"
                    env_file.write_text("XKB_DEFAULT_LAYOUT=us,ru\nXKB_DEFAULT_OPTIONS=grp:alt_shift_toggle\n", encoding="utf-8")
                    os.chown(str(env_d), u_uid, u_gid)
                    os.chown(str(env_file), u_uid, u_gid)

                    # User kxkbrc for KDE Plasma
                    kxkb_file = home / ".config" / "kxkbrc"
                    kxkb_content = "[Layout]\nDisplayNames=,\nLayoutList=us,ru\nShowFlag=false\nShowLayoutIndicator=false\nUse=true\nVariantList=,\n"
                    if kxkb_file.exists():
                        try:
                            lines = kxkb_file.read_text(encoding="utf-8", errors="ignore").splitlines()
                            new_lines = []
                            for l in lines:
                                if l.startswith("LayoutList="):
                                    val = l.split("=", 1)[1].strip()
                                    layouts = [x.strip() for x in val.split(",") if x.strip()]
                                    if "ru" not in layouts:
                                        layouts.append("ru")
                                    if "us" not in layouts:
                                        layouts.insert(0, "us")
                                    new_lines.append(f"LayoutList={','.join(layouts)}")
                                elif l.startswith("Use="):
                                    new_lines.append("Use=true")
                                elif l.startswith("ShowLayoutIndicator="):
                                    new_lines.append("ShowLayoutIndicator=false")
                                else:
                                    new_lines.append(l)
                            kxkb_content = "\n".join(new_lines) + "\n"
                        except Exception:
                            pass
                    kxkb_file.write_text(kxkb_content, encoding="utf-8")
                    os.chown(str(kxkb_file), u_uid, u_gid)
                except Exception as e:
                    logger.debug(f"User home config error: {e}")

        # Dynamic systemd user env & KWin reload
        user_env = {
            "HOME": homedir,
            "USER": username,
            "LOGNAME": username,
            "XDG_RUNTIME_DIR": f"/run/user/{uid}",
            "DBUS_SESSION_BUS_ADDRESS": f"unix:path=/run/user/{uid}/bus",
            "PATH": "/usr/local/bin:/usr/bin:/bin"
        }
        kwargs = {"env": user_env, "timeout": 0.5}
        if os.getuid() == 0:
            kwargs["user"] = uid
            kwargs["group"] = gid
        try:
            subprocess.run(["systemctl", "--user", "set-environment", "XKB_DEFAULT_LAYOUT=us,ru", "XKB_DEFAULT_OPTIONS=grp:alt_shift_toggle"], **kwargs)
            subprocess.run(["dbus-update-activation-environment", "--systemd", "XKB_DEFAULT_LAYOUT=us,ru", "XKB_DEFAULT_OPTIONS=grp:alt_shift_toggle"], **kwargs)
            subprocess.run(["busctl", "--user", "call", "org.kde.KWin", "/KWin", "org.kde.KWin", "reconfigure"], **kwargs)
        except Exception:
            pass

    except Exception as e:
        logger.warning(f"Could not auto-setup XKB: {e}")


class Plugin:
    async def sync_layout(self, lang: str = "us"):
        sync_layout(lang)
        return {
            "success": True,
            "active_language": current_active_language,
            "is_desktop": is_desktop_mode(),
            "gamescope_wayland_layout": gamescope_wayland_layout,
            "x11_group": get_active_x11_group()
        }

    async def reset_game_mode(self):
        global gamescope_wayland_layout, current_active_language
        gamescope_wayland_layout = 0
        current_active_language = "us"
        sync_layout("us")
        return {"success": True, "active_language": "us"}

    async def get_active_layout(self):
        return {
            "active_language": current_active_language,
            "is_desktop": is_desktop_mode(),
            "gamescope_wayland_layout": gamescope_wayland_layout,
            "x11_group": get_active_x11_group()
        }

    async def _main(self):
        global current_active_language, gamescope_wayland_layout
        current_active_language = "us"
        gamescope_wayland_layout = 0
        auto_setup_system_xkb()
        init_uinput_device()
        logger.info("Alt_Shift plugin backend loaded cleanly.")

    async def _unload(self):
        destroy_uinput_device()
        logger.info("Alt_Shift plugin backend unloaded.")
