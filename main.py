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

# Linux Keycodes
KEY_ESC = 1
KEY_1 = 2
KEY_2 = 3
KEY_3 = 4
KEY_4 = 5
KEY_5 = 6
KEY_6 = 7
KEY_7 = 8
KEY_8 = 9
KEY_9 = 10
KEY_0 = 11
KEY_MINUS = 12
KEY_EQUAL = 13
KEY_BACKSPACE = 14
KEY_TAB = 15
KEY_Q = 16
KEY_W = 17
KEY_E = 18
KEY_R = 19
KEY_T = 20
KEY_Y = 21
KEY_U = 22
KEY_I = 23
KEY_O = 24
KEY_P = 25
KEY_LEFTBRACE = 26
KEY_RIGHTBRACE = 27
KEY_ENTER = 28
KEY_LEFTCTRL = 29
KEY_A = 30
KEY_S = 31
KEY_D = 32
KEY_F = 33
KEY_G = 34
KEY_H = 35
KEY_J = 36
KEY_K = 37
KEY_L = 38
KEY_SEMICOLON = 39
KEY_APOSTROPHE = 40
KEY_GRAVE = 41
KEY_LEFTSHIFT = 42
KEY_BACKSLASH = 43
KEY_Z = 44
KEY_X = 45
KEY_C = 46
KEY_V = 47
KEY_B = 48
KEY_N = 49
KEY_M = 50
KEY_COMMA = 51
KEY_DOT = 52
KEY_SLASH = 53
KEY_LEFTALT = 56
KEY_SPACE = 57
KEY_UP = 103
KEY_LEFT = 105
KEY_RIGHT = 106
KEY_DOWN = 108

CHAR_TO_EVDEV = {
    # Lowercase Latin
    'a': (KEY_A, False), 'b': (KEY_B, False), 'c': (KEY_C, False),
    'd': (KEY_D, False), 'e': (KEY_E, False), 'f': (KEY_F, False),
    'g': (KEY_G, False), 'h': (KEY_H, False), 'i': (KEY_I, False),
    'j': (KEY_J, False), 'k': (KEY_K, False), 'l': (KEY_L, False),
    'm': (KEY_M, False), 'n': (KEY_N, False), 'o': (KEY_O, False),
    'p': (KEY_P, False), 'q': (KEY_Q, False), 'r': (KEY_R, False),
    's': (KEY_S, False), 't': (KEY_T, False), 'u': (KEY_U, False),
    'v': (KEY_V, False), 'w': (KEY_W, False), 'x': (KEY_X, False),
    'y': (KEY_Y, False), 'z': (KEY_Z, False),

    # Uppercase Latin
    'A': (KEY_A, True), 'B': (KEY_B, True), 'C': (KEY_C, True),
    'D': (KEY_D, True), 'E': (KEY_E, True), 'F': (KEY_F, True),
    'G': (KEY_G, True), 'H': (KEY_H, True), 'I': (KEY_I, True),
    'J': (KEY_J, True), 'K': (KEY_K, True), 'L': (KEY_L, True),
    'M': (KEY_M, True), 'N': (KEY_N, True), 'O': (KEY_O, True),
    'P': (KEY_P, True), 'Q': (KEY_Q, True), 'R': (KEY_R, True),
    'S': (KEY_S, True), 'T': (KEY_T, True), 'U': (KEY_U, True),
    'V': (KEY_V, True), 'W': (KEY_W, True), 'X': (KEY_X, True),
    'Y': (KEY_Y, True), 'Z': (KEY_Z, True),

    # Digits
    '1': (KEY_1, False), '2': (KEY_2, False), '3': (KEY_3, False),
    '4': (KEY_4, False), '5': (KEY_5, False), '6': (KEY_6, False),
    '7': (KEY_7, False), '8': (KEY_8, False), '9': (KEY_9, False),
    '0': (KEY_0, False),

    # Special / Symbols
    ' ': (KEY_SPACE, False),
    '-': (KEY_MINUS, False), '_': (KEY_MINUS, True),
    '=': (KEY_EQUAL, False), '+': (KEY_EQUAL, True),
    '[': (KEY_LEFTBRACE, False), '{': (KEY_LEFTBRACE, True),
    ']': (KEY_RIGHTBRACE, False), '}': (KEY_RIGHTBRACE, True),
    ';': (KEY_SEMICOLON, False), ':': (KEY_SEMICOLON, True),
    "'": (KEY_APOSTROPHE, False), '"': (KEY_APOSTROPHE, True),
    ',': (KEY_COMMA, False), '<': (KEY_COMMA, True),
    '.': (KEY_DOT, False), '>': (KEY_DOT, True),
    '/': (KEY_SLASH, False), '?': (KEY_SLASH, True),
    '`': (KEY_GRAVE, False), '~': (KEY_GRAVE, True),
    '!': (KEY_1, True), '@': (KEY_2, True), '#': (KEY_3, True),
    '$': (KEY_4, True), '%': (KEY_5, True), '^': (KEY_6, True),
    '&': (KEY_7, True), '*': (KEY_8, True), '(': (KEY_9, True),
    ')': (KEY_0, True), '\\': (KEY_BACKSLASH, False), '|': (KEY_BACKSLASH, True),
}

RU_TO_EVDEV = {
    'й': (KEY_Q, False), 'Й': (KEY_Q, True),
    'ц': (KEY_W, False), 'Ц': (KEY_W, True),
    'у': (KEY_E, False), 'У': (KEY_E, True),
    'к': (KEY_R, False), 'К': (KEY_R, True),
    'е': (KEY_T, False), 'Е': (KEY_T, True),
    'н': (KEY_Y, False), 'Н': (KEY_Y, True),
    'г': (KEY_U, False), 'Г': (KEY_U, True),
    'ш': (KEY_I, False), 'Ш': (KEY_I, True),
    'щ': (KEY_O, False), 'Щ': (KEY_O, True),
    'з': (KEY_P, False), 'З': (KEY_P, True),
    'х': (KEY_LEFTBRACE, False), 'Х': (KEY_LEFTBRACE, True),
    'ъ': (KEY_RIGHTBRACE, False), 'Ъ': (KEY_RIGHTBRACE, True),
    'ф': (KEY_A, False), 'Ф': (KEY_A, True),
    'ы': (KEY_S, False), 'Ы': (KEY_S, True),
    'в': (KEY_D, False), 'В': (KEY_D, True),
    'а': (KEY_F, False), 'А': (KEY_F, True),
    'п': (KEY_G, False), 'П': (KEY_G, True),
    'р': (KEY_H, False), 'Р': (KEY_H, True),
    'о': (KEY_J, False), 'О': (KEY_J, True),
    'л': (KEY_K, False), 'Л': (KEY_K, True),
    'д': (KEY_L, False), 'Д': (KEY_L, True),
    'ж': (KEY_SEMICOLON, False), 'Ж': (KEY_SEMICOLON, True),
    'э': (KEY_APOSTROPHE, False), 'Э': (KEY_APOSTROPHE, True),
    'я': (KEY_Z, False), 'Я': (KEY_Z, True),
    'ч': (KEY_X, False), 'Ч': (KEY_X, True),
    'с': (KEY_C, False), 'С': (KEY_C, True),
    'м': (KEY_V, False), 'М': (KEY_V, True),
    'и': (KEY_B, False), 'И': (KEY_B, True),
    'т': (KEY_N, False), 'Т': (KEY_N, True),
    'ь': (KEY_M, False), 'Ь': (KEY_M, True),
    'б': (KEY_COMMA, False), 'Б': (KEY_COMMA, True),
    'ю': (KEY_DOT, False), 'Ю': (KEY_DOT, True),
    'ё': (KEY_GRAVE, False), 'Ё': (KEY_GRAVE, True),
}

RU_SYMBOLS = {
    '.': (KEY_SLASH, False),
    ',': (KEY_SLASH, True),
    '?': (KEY_7, True),
    '!': (KEY_1, True),
    '"': (KEY_2, True),
    '№': (KEY_3, True),
    ';': (KEY_4, True),
    '%': (KEY_5, True),
    ':': (KEY_6, True),
    '*': (KEY_8, True),
    '(': (KEY_9, True),
    ')': (KEY_0, True),
    '_': (KEY_MINUS, True),
    '-': (KEY_MINUS, False),
    '=': (KEY_EQUAL, False),
    '+': (KEY_EQUAL, True),
    '/': (KEY_BACKSLASH, True),
    '\\': (KEY_BACKSLASH, False),
}

SPECIAL_KEYS = {
    'Backspace': KEY_BACKSPACE,
    '\x02': KEY_BACKSPACE,
    '\x08': KEY_BACKSPACE,
    '\x7f': KEY_BACKSPACE,
    'Enter': KEY_ENTER,
    '\r': KEY_ENTER,
    '\n': KEY_ENTER,
    '\x03': KEY_ENTER,
    '\x0a': KEY_ENTER,
    '\x0d': KEY_ENTER,
    'Tab': KEY_TAB,
    '\t': KEY_TAB,
    '\x09': KEY_TAB,
    'Escape': KEY_ESC,
    '\x1b': KEY_ESC,
    'ArrowLeft': KEY_LEFT,
    '\x04': KEY_LEFT,
    'ArrowRight': KEY_RIGHT,
    '\x05': KEY_RIGHT,
    'ArrowUp': KEY_UP,
    '\x06': KEY_UP,
    'ArrowDown': KEY_DOWN,
    '\x07': KEY_DOWN,
}

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
last_key_time = 0
last_key_text = None
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
        for k in range(1, 256):
            fcntl.ioctl(fd, UI_SET_KEYBIT, k)

        setup = UInputSetup()
        setup.id.bustype = 0x03
        setup.id.vendor = 0x28de
        setup.id.product = 0x1205
        setup.id.version = 1
        setup.name = b"SteamDeck-OSK-Wayland-Bridge"

        fcntl.ioctl(fd, UI_DEV_SETUP, setup)
        fcntl.ioctl(fd, UI_DEV_CREATE)
        uinput_fd = fd
        logger.info("Pure ctypes UInput device initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to create UInput device: {e}")

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

def emit_keypress(keycode: int, shift: bool = False):
    if shift:
        emit_raw_event(EV_KEY, KEY_LEFTSHIFT, 1)
        emit_raw_event(EV_SYN, SYN_REPORT, 0)
        time.sleep(0.005)

    emit_raw_event(EV_KEY, keycode, 1)
    emit_raw_event(EV_SYN, SYN_REPORT, 0)
    time.sleep(0.01)
    emit_raw_event(EV_KEY, keycode, 0)
    emit_raw_event(EV_SYN, SYN_REPORT, 0)

    if shift:
        time.sleep(0.005)
        emit_raw_event(EV_KEY, KEY_LEFTSHIFT, 0)
        emit_raw_event(EV_SYN, SYN_REPORT, 0)

def emit_alt_shift():
    emit_raw_event(EV_KEY, KEY_LEFTALT, 1)
    emit_raw_event(EV_KEY, KEY_LEFTSHIFT, 1)
    emit_raw_event(EV_SYN, SYN_REPORT, 0)
    time.sleep(0.005)
    emit_raw_event(EV_KEY, KEY_LEFTSHIFT, 0)
    emit_raw_event(EV_KEY, KEY_LEFTALT, 0)
    emit_raw_event(EV_SYN, SYN_REPORT, 0)
    time.sleep(0.02)

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
                    time.sleep(0.02)
        except Exception as e:
            logger.debug(f"KDE layout sync error: {e}")
        set_x11_layout_group(lang_str)
    else:
        set_x11_layout_group(lang_str)
        if gamescope_wayland_layout != target_idx:
            logger.info(f"Gamescope: switching Wayland layout from {gamescope_wayland_layout} to {target_idx} ({lang_str})")
            emit_alt_shift()
            gamescope_wayland_layout = target_idx
        current_active_language = lang_str

def auto_setup_system_xkb():
    try:
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

    async def send_key(self, text: str = ""):
        global last_key_time, last_key_text
        if not text:
            return {"success": False}

        now = time.time()
        if text not in ['\x02', '\x08', '\r', '\n', '\t', 'Backspace', 'Enter', 'Tab'] and text == last_key_text and (now - last_key_time) < 0.015:
            return {"success": True, "debounced": True}
        last_key_text = text
        last_key_time = now

        if text in SPECIAL_KEYS:
            emit_keypress(SPECIAL_KEYS[text], False)
            return {"success": True}

        for ch in text:
            if ch in SPECIAL_KEYS:
                emit_keypress(SPECIAL_KEYS[ch], False)
            elif ch in RU_TO_EVDEV:
                sync_layout("ru")
                keycode, shift = RU_TO_EVDEV[ch]
                emit_keypress(keycode, shift)
            elif ch in CHAR_TO_EVDEV:
                sync_layout("us")
                keycode, shift = CHAR_TO_EVDEV[ch]
                emit_keypress(keycode, shift)
            elif current_active_language == "ru" and ch in RU_SYMBOLS:
                sync_layout("ru")
                keycode, shift = RU_SYMBOLS[ch]
                emit_keypress(keycode, shift)

        return {"success": True}

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
