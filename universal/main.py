import asyncio
import ctypes
import fcntl
import json
import logging
import os
from pathlib import Path
import pwd
import re
import struct
import subprocess
import time
from typing import Dict, List, Optional, Tuple

try:
    import decky_plugin
    logger = decky_plugin.logger
except ImportError:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("Alt_Shift_Universal")

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
KEY_RIGHTSHIFT = 54
KEY_LEFTALT = 56
KEY_SPACE = 57
KEY_102ND = 86
KEY_RIGHTALT = 100
KEY_UP = 103
KEY_LEFT = 105
KEY_RIGHT = 106
KEY_DOWN = 108

# Standard US Latin mapping (QWERTY)
CHAR_TO_EVDEV: Dict[str, Tuple[int, bool]] = {
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

    # Special / Symbols (Always typed in US layout)
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

# Standard Cyrillic mapping (ЙЦУКЕН)
CYRILLIC_TO_EVDEV: Dict[str, Tuple[int, bool]] = {
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

CYRILLIC_SYMBOLS: Dict[str, Tuple[int, bool]] = {
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

STEAM_LAYOUT_ID_MAP: Dict[int, str] = {
    0: "us", 1: "bg", 2: "zh", 3: "zh", 4: "cz", 5: "dk", 6: "fi", 7: "fr",
    8: "de", 9: "gr", 10: "hu", 11: "it", 12: "ja", 13: "kr", 14: "no",
    15: "pl", 16: "pt", 17: "ro", 18: "ru", 19: "es", 20: "se", 21: "th", 22: "tr",
    23: "tr", 24: "ua", 25: "vn", 26: "us", 27: "us", 28: "gb"
}

# State management
uinput_fd = -1
current_cached_kde_layout = -1
gamescope_active_layout = 0  # 0: US, 1: National/Cyrillic
last_key_time = 0
last_key_text = None
kde_layout_map: Dict[str, int] = {"us": 0, "ru": 1}
steam_detected_layouts: List[str] = ["us", "ru"]
last_vdf_mtime = 0
last_input_was_cyrillic = False

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

    cmd = [
        "busctl", "--user", "call",
        "org.kde.keyboard", "/Layouts", "org.kde.KeyboardLayouts",
        member
    ]
    if sig and arg:
        cmd.extend([sig, arg])

    kwargs = {"env": env, "capture_output": True, "text": True, "timeout": 0.4}
    if os.getuid() == 0:
        kwargs["user"] = uid
        kwargs["group"] = gid

    try:
        res = subprocess.run(cmd, **kwargs)
        if res.returncode == 0:
            return True, res.stdout.strip()
    except Exception:
        pass

    return False, ""

def get_steam_selected_layouts() -> List[str]:
    """Extracts keyboard layout IDs from Steam localconfig.vdf."""
    global steam_detected_layouts, last_vdf_mtime
    _, _, _, homedir = get_user_info()
    steam_roots = [
        Path(homedir) / ".local" / "share" / "Steam",
        Path(homedir) / ".steam" / "steam",
    ]

    selected: List[str] = []
    for root in steam_roots:
        if not root.exists():
            continue
        for vdf in root.glob("userdata/*/config/localconfig.vdf"):
            try:
                st = vdf.stat()
                if st.st_mtime > last_vdf_mtime:
                    last_vdf_mtime = st.st_mtime
                content = vdf.read_text(encoding="utf-8", errors="ignore")
                m = re.search(r'selectedLayouts[^\[]*\[([0-9,\s]*)\]', content)
                if m:
                    ids_str = m.group(1).strip()
                    if ids_str:
                        ids = [int(x.strip()) for x in ids_str.split(",") if x.strip().isdigit()]
                        for lid in ids:
                            if lid in STEAM_LAYOUT_ID_MAP:
                                xkb = STEAM_LAYOUT_ID_MAP[lid]
                                if xkb not in selected:
                                    selected.append(xkb)
            except Exception:
                pass

    if not selected:
        selected = ["us", "ru"]
    if "us" in selected:
        selected.remove("us")
    selected.insert(0, "us")

    steam_detected_layouts = selected
    return selected

def detect_kde_layout_indices():
    """Detects indices of all layouts currently registered in KDE Plasma D-Bus."""
    global kde_layout_map
    try:
        ok, out = call_kde_dbus("getLayoutsList")
        if ok and out:
            tokens = re.findall(r'"([^"]*)"', out)
            layouts = [tokens[i].lower() for i in range(0, len(tokens), 3) if i < len(tokens)]
            indices = {}
            for idx, lay in enumerate(layouts):
                indices[lay] = idx
            if indices:
                kde_layout_map = indices
                logger.debug(f"Detected KDE layout indices: {kde_layout_map}")
    except Exception as e:
        logger.debug(f"detect_kde_layout_indices error: {e}")

def auto_setup_system_xkb():
    """Ensures XKB and KDE configs include Steam layouts (up to 4 XKB limit) without restarting session."""
    try:
        steam_lays = get_steam_selected_layouts()
        if "us" not in steam_lays:
            steam_lays.insert(0, "us")
        
        # XKB protocol allows a maximum of 4 layout groups simultaneously
        active_4_lays = steam_lays[:4]
        layout_str = ",".join(active_4_lays)
        commas_str = "," * (len(active_4_lays) - 1)
        options_str = "grp:alt_shift_toggle"

        username, uid, gid, homedir = get_user_info()

        for home in Path("/home").glob("*"):
            if home.is_dir() and not home.name.startswith("."):
                try:
                    stat = home.stat()
                    u_uid, u_gid = stat.st_uid, stat.st_gid

                    env_d = home / ".config" / "environment.d"
                    env_d.mkdir(parents=True, exist_ok=True)
                    env_file = env_d / "10-xkb.conf"
                    env_file.write_text(f"XKB_DEFAULT_LAYOUT={layout_str}\nXKB_DEFAULT_OPTIONS={options_str}\n", encoding="utf-8")
                    os.chown(str(env_d), u_uid, u_gid)
                    os.chown(str(env_file), u_uid, u_gid)

                    kxkb_file = home / ".config" / "kxkbrc"
                    kxkb_content = (
                        f"[Layout]\n"
                        f"DisplayNames={commas_str}\n"
                        f"LayoutList={layout_str}\n"
                        f"Options={options_str}\n"
                        f"ResetOldOptions=true\n"
                        f"ShowFlag=false\n"
                        f"ShowLayoutIndicator=false\n"
                        f"Use=true\n"
                        f"VariantList={commas_str}\n"
                    )
                    kxkb_file.write_text(kxkb_content, encoding="utf-8")
                    os.chown(str(kxkb_file), u_uid, u_gid)
                except Exception:
                    pass

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
            subprocess.run(["systemctl", "--user", "set-environment", f"XKB_DEFAULT_LAYOUT={layout_str}", f"XKB_DEFAULT_OPTIONS={options_str}"], **kwargs)
            subprocess.run(["dbus-update-activation-environment", "--systemd", f"XKB_DEFAULT_LAYOUT={layout_str}", f"XKB_DEFAULT_OPTIONS={options_str}"], **kwargs)
            subprocess.run(["setxkbmap", "-layout", layout_str, "-option", options_str], **kwargs)
            subprocess.run(["busctl", "--user", "call", "org.kde.KWin", "/KWin", "org.kde.KWin", "reconfigure"], **kwargs)
            subprocess.run(["busctl", "--user", "call", "org.kde.kded6", "/kded", "org.kde.kded6", "reconfigure"], **kwargs)
            subprocess.run(["busctl", "--user", "call", "org.kde.kded5", "/kded", "org.kde.kded5", "reconfigure"], **kwargs)
        except Exception:
            pass

        detect_kde_layout_indices()

    except Exception as e:
        logger.warning(f"Could not auto-setup XKB: {e}")

def sync_layout(target_layout_name: str):
    """Synchronizes system layout to target (e.g. 'us', 'ru', 'ua', 'de', 'dk', 'fi', 'se', 'no', 'es', 'fr', 'pl', 'cz', 'hu', 'tr')."""
    global current_cached_kde_layout, gamescope_active_layout

    # 1. Desktop Mode (KDE Plasma D-Bus)
    if target_layout_name in kde_layout_map:
        kde_target = kde_layout_map[target_layout_name]
    elif target_layout_name == "us":
        kde_target = kde_layout_map.get("us", 0)
    else:
        # Fallback to us rather than an arbitrary foreign layout
        kde_target = kde_layout_map.get("us", 0)

    ok, out = call_kde_dbus("setLayout", "u", str(kde_target))
    if ok:
        if current_cached_kde_layout != kde_target:
            current_cached_kde_layout = kde_target
            time.sleep(0.012)
            logger.info(f"Switched KDE layout to index {kde_target} ('{target_layout_name}')")
        return

    # 2. Game Mode (Gamescope Wayland) - Strict 2-mode toggle (0: US, 1: National/Cyrillic)
    target_gamescope_mode = 0 if target_layout_name == "us" else 1
    if gamescope_active_layout != target_gamescope_mode:
        emit_raw_event(EV_KEY, KEY_LEFTALT, 1)
        emit_raw_event(EV_KEY, KEY_LEFTSHIFT, 1)
        emit_raw_event(EV_SYN, SYN_REPORT, 0)
        time.sleep(0.005)
        emit_raw_event(EV_KEY, KEY_LEFTSHIFT, 0)
        emit_raw_event(EV_KEY, KEY_LEFTALT, 0)
        emit_raw_event(EV_SYN, SYN_REPORT, 0)
        time.sleep(0.015)
        gamescope_active_layout = target_gamescope_mode
        logger.info(f"Toggled Gamescope layout to mode {target_gamescope_mode}")

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
        setup.name = b"SteamDeck-OSK-Universal-Bridge"

        fcntl.ioctl(fd, UI_DEV_SETUP, setup)
        fcntl.ioctl(fd, UI_DEV_CREATE)
        uinput_fd = fd
        logger.info("Universal UInput device initialized successfully.")
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
        time.sleep(0.003)

    emit_raw_event(EV_KEY, keycode, 1)
    emit_raw_event(EV_SYN, SYN_REPORT, 0)
    time.sleep(0.008)
    emit_raw_event(EV_KEY, keycode, 0)
    emit_raw_event(EV_SYN, SYN_REPORT, 0)

    if shift:
        time.sleep(0.003)
        emit_raw_event(EV_KEY, KEY_LEFTSHIFT, 0)
        emit_raw_event(EV_SYN, SYN_REPORT, 0)

def emit_altgr_keypress(keycode: int, shift: bool = False):
    """Emits AltGr (Right Alt) combination."""
    emit_raw_event(EV_KEY, KEY_RIGHTALT, 1)
    if shift:
        emit_raw_event(EV_KEY, KEY_LEFTSHIFT, 1)
    emit_raw_event(EV_SYN, SYN_REPORT, 0)
    time.sleep(0.004)

    emit_raw_event(EV_KEY, keycode, 1)
    emit_raw_event(EV_SYN, SYN_REPORT, 0)
    time.sleep(0.008)
    emit_raw_event(EV_KEY, keycode, 0)
    emit_raw_event(EV_SYN, SYN_REPORT, 0)

    if shift:
        emit_raw_event(EV_KEY, KEY_LEFTSHIFT, 0)
    emit_raw_event(EV_KEY, KEY_RIGHTALT, 0)
    emit_raw_event(EV_SYN, SYN_REPORT, 0)

def resolve_character_target(ch: str) -> Optional[Tuple[str, int, bool, bool]]:
    """Resolves any character into (target_layout, keycode, shift, is_altgr) using live active layouts."""
    # 1. German Umlauts & specific symbols
    if ch in ('ä', 'Ä', 'ö', 'Ö', 'ü', 'Ü', 'ß', 'ẞ'):
        # ä / Ä: on KEY_APOSTROPHE in de, fi, se
        if ch in ('ä', 'Ä'):
            shift = (ch == 'Ä')
            for lay in ['fi', 'se', 'de']:
                if lay in kde_layout_map:
                    return (lay, KEY_APOSTROPHE, shift, False)
            return ("de", KEY_APOSTROPHE, shift, False)

        # ö / Ö: on KEY_SEMICOLON in de, fi, se, hu, tr
        elif ch in ('ö', 'Ö'):
            shift = (ch == 'Ö')
            for lay in ['fi', 'se', 'de', 'hu', 'tr']:
                if lay in kde_layout_map:
                    return (lay, KEY_SEMICOLON, shift, False)
            return ("de", KEY_SEMICOLON, shift, False)

        # ü / Ü: on KEY_LEFTBRACE in de, cz / KEY_MINUS in hu / KEY_RIGHTBRACE in tr
        elif ch in ('ü', 'Ü'):
            shift = (ch == 'Ü')
            if "hu" in kde_layout_map:
                return ("hu", KEY_MINUS, shift, False)
            elif "tr" in kde_layout_map:
                return ("tr", KEY_RIGHTBRACE, shift, False)
            return ("de", KEY_LEFTBRACE, shift, False)

        # ß / ẞ: on KEY_MINUS in de
        elif ch in ('ß', 'ẞ'):
            return ("de", KEY_MINUS, (ch == 'ẞ'), False)

    # 2. Nordic Nordic characters (å, æ, ø, §, ½, ¤)
    elif ch in ('å', 'Å'):
        shift = (ch == 'Å')
        for lay in ['fi', 'se', 'dk', 'no']:
            if lay in kde_layout_map:
                return (lay, KEY_LEFTBRACE, shift, False)
        return ("dk", KEY_LEFTBRACE, shift, False)

    elif ch in ('æ', 'Æ'):
        shift = (ch == 'Æ')
        if "dk" in kde_layout_map:
            return ("dk", KEY_SEMICOLON, shift, False)
        elif "no" in kde_layout_map:
            return ("no", KEY_APOSTROPHE, shift, False)
        return ("dk", KEY_SEMICOLON, shift, False)

    elif ch in ('ø', 'Ø'):
        shift = (ch == 'Ø')
        if "dk" in kde_layout_map:
            return ("dk", KEY_APOSTROPHE, shift, False)
        elif "no" in kde_layout_map:
            return ("no", KEY_SEMICOLON, shift, False)
        return ("dk", KEY_APOSTROPHE, shift, False)

    elif ch == '§':
        if "fi" in kde_layout_map or "se" in kde_layout_map:
            return ("fi" if "fi" in kde_layout_map else "se", KEY_GRAVE, False, False)
        elif "dk" in kde_layout_map:
            return ("dk", KEY_GRAVE, True, False)
        elif "no" in kde_layout_map:
            return ("no", KEY_GRAVE, True, False)
        return ("de", KEY_3, True, False)

    elif ch == '½':
        if "dk" in kde_layout_map:
            return ("dk", KEY_GRAVE, False, False)
        elif "fi" in kde_layout_map or "se" in kde_layout_map:
            return ("fi" if "fi" in kde_layout_map else "se", KEY_GRAVE, True, False)
        return ("dk", KEY_GRAVE, False, False)

    elif ch == '°':
        return ("de", KEY_GRAVE, True, False)

    elif ch == '^':
        return ("de", KEY_GRAVE, False, False)

    elif ch == '¤':
        return ("fi" if "fi" in kde_layout_map else "se", KEY_4, False, True)

    # 3. Spanish (ñ, Ñ, ¡, ¿, º, ª)
    elif ch in ('ñ', 'Ñ'):
        return ("es", KEY_SEMICOLON, (ch == 'Ñ'), False)
    elif ch == '¡':
        return ("es", KEY_EQUAL, False, False)
    elif ch == '¿':
        return ("es", KEY_MINUS, True, False)
    elif ch == 'º':
        return ("es", KEY_GRAVE, False, False)
    elif ch == 'ª':
        return ("es", KEY_GRAVE, True, False)

    # 4. Ukrainian specific (і, ї, є, ґ, ₴)
    elif ch in ('і', 'І'):
        return ("ua" if "ua" in kde_layout_map else "ru", KEY_S, (ch == 'І'), False)
    elif ch in ('ї', 'Ї'):
        return ("ua" if "ua" in kde_layout_map else "ru", KEY_RIGHTBRACE, (ch == 'Ї'), False)
    elif ch in ('є', 'Є'):
        return ("ua" if "ua" in kde_layout_map else "ru", KEY_APOSTROPHE, (ch == 'Є'), False)
    elif ch in ('ґ', 'Ґ'):
        return ("ua" if "ua" in kde_layout_map else "ru", KEY_BACKSLASH, (ch == 'Ґ'), False)
    elif ch == '₴':
        return ("ua", KEY_GRAVE, True, False)

    # 5. French accented letters (é, è, ç, à, ù)
    elif ch in ('é', 'É'):
        return ("fr", KEY_2, (ch == 'É'), False)
    elif ch in ('è', 'È'):
        return ("fr", KEY_7, (ch == 'È'), False)
    elif ch in ('ç', 'Ç'):
        return ("fr", KEY_9, (ch == 'Ç'), False)
    elif ch in ('à', 'À'):
        return ("fr", KEY_0, (ch == 'À'), False)
    elif ch in ('ù', 'Ù'):
        return ("fr", KEY_APOSTROPHE, (ch == 'Ù'), False)

    # 6. Polish AltGr letters (ą, ć, ę, ł, ń, ó, ś, ź, ż)
    elif ch in ('ą', 'Ą'): return ("pl", KEY_A, (ch == 'Ą'), True)
    elif ch in ('ć', 'Ć'): return ("pl", KEY_C, (ch == 'Ć'), True)
    elif ch in ('ę', 'Ę'): return ("pl", KEY_E, (ch == 'Ę'), True)
    elif ch in ('ł', 'Ł'): return ("pl", KEY_L, (ch == 'Ł'), True)
    elif ch in ('ń', 'Ń'): return ("pl", KEY_N, (ch == 'Ń'), True)
    elif ch in ('ó', 'Ó'): return ("pl", KEY_O, (ch == 'Ó'), True)
    elif ch in ('ś', 'Ś'): return ("pl", KEY_S, (ch == 'Ś'), True)
    elif ch in ('ź', 'Ź'): return ("pl", KEY_X, (ch == 'Ź'), True)
    elif ch in ('ż', 'Ż'): return ("pl", KEY_Z, (ch == 'Ż'), True)

    # 7. Czech letters
    elif ch in ('ě', 'Ě'): return ("cz", KEY_2, (ch == 'Ě'), False)
    elif ch in ('š', 'Š'): return ("cz", KEY_3, (ch == 'Š'), False)
    elif ch in ('č', 'Č'): return ("cz", KEY_4, (ch == 'Č'), False)
    elif ch in ('ř', 'Ř'): return ("cz", KEY_5, (ch == 'Ř'), False)
    elif ch in ('ž', 'Ž'): return ("cz", KEY_6, (ch == 'Ž'), False)
    elif ch in ('ý', 'Ý'): return ("cz", KEY_7, (ch == 'Ý'), False)
    elif ch in ('á', 'Á'): return ("cz", KEY_8, (ch == 'Á'), False)
    elif ch in ('í', 'Í'): return ("cz", KEY_9, (ch == 'Í'), False)
    elif ch in ('ů', 'Ů'): return ("cz", KEY_SEMICOLON, (ch == 'Ů'), False)
    elif ch in ('ú', 'Ú'): return ("cz", KEY_LEFTBRACE, (ch == 'Ú'), False)

    # 8. Hungarian letters
    elif ch in ('ő', 'Ő'): return ("hu", KEY_LEFTBRACE, (ch == 'Ő'), False)
    elif ch in ('ű', 'Ű'): return ("hu", KEY_BACKSLASH, (ch == 'Ű'), False)

    # 9. Turkish letters
    elif ch in ('ğ', 'Ğ'): return ("tr", KEY_LEFTBRACE, (ch == 'Ğ'), False)
    elif ch in ('ş', 'Ş'): return ("tr", KEY_SEMICOLON, (ch == 'Ş'), False)
    elif ch in ('ı', 'I'): return ("tr", KEY_I, (ch == 'I'), False)

    # 10. Standard Cyrillic Russian letters
    elif ch in CYRILLIC_TO_EVDEV:
        target = "ru" if "ru" in kde_layout_map else ("ua" if "ua" in kde_layout_map else ("bg" if "bg" in kde_layout_map else "ru"))
        kc, shift = CYRILLIC_TO_EVDEV[ch]
        return (target, kc, shift, False)

    # 11. Standard US Latin & Symbols
    elif ch in CHAR_TO_EVDEV:
        kc, shift = CHAR_TO_EVDEV[ch]
        return ("us", kc, shift, False)

    return None

async def auto_background_watcher():
    """Background watcher that automatically detects mode transitions and Steam layout changes."""
    last_check_time = 0
    while True:
        try:
            await asyncio.sleep(2.5)
            username, uid, gid, homedir = get_user_info()
            bus_path = Path(f"/run/user/{uid}/bus")
            if bus_path.exists():
                steam_roots = [
                    Path(homedir) / ".local" / "share" / "Steam",
                    Path(homedir) / ".steam" / "steam",
                ]
                for root in steam_roots:
                    if not root.exists():
                        continue
                    for vdf in root.glob("userdata/*/config/localconfig.vdf"):
                        try:
                            st = vdf.stat()
                            if st.st_mtime > last_check_time:
                                last_check_time = st.st_mtime
                                auto_setup_system_xkb()
                                logger.info("Background watcher: auto-synced Steam layouts to KDE live.")
                        except Exception:
                            pass
        except asyncio.CancelledError:
            break
        except Exception:
            pass



class Plugin:
    watcher_task: Optional[asyncio.Task] = None

    async def get_layouts_info(self):
        """Returns detected active layouts to frontend."""
        detect_kde_layout_indices()
        get_steam_selected_layouts()
        return {
            "active_layouts": steam_detected_layouts,
            "kde_indices": kde_layout_map,
        }

    async def sync_layouts(self):
        """Forces live sync from Steam into system XKB and KDE configs."""
        auto_setup_system_xkb()
        return {
            "success": True,
            "active_layouts": steam_detected_layouts,
            "kde_indices": kde_layout_map,
        }

    async def send_key(self, text: str = ""):
        global last_key_time, last_key_text, last_input_was_cyrillic
        if not text:
            return {"success": False}

        now = time.time()
        if text not in ['\x02', '\x08', '\r', '\n', '\t', 'Backspace', 'Enter', 'Tab'] and text == last_key_text and (now - last_key_time) < 0.015:
            return {"success": True, "debounced": True}
        last_key_text = text
        last_key_time = now

        # 1. Special Control Keys (Backspace, Enter, Tab, Arrows, Esc)
        if text in SPECIAL_KEYS:
            emit_keypress(SPECIAL_KEYS[text], False)
            return {"success": True}

        # 2. Iterate each character in text
        for ch in text:
            if ch in SPECIAL_KEYS:
                emit_keypress(SPECIAL_KEYS[ch], False)
                continue

            # Check if this is Cyrillic punctuation in active Cyrillic context
            if last_input_was_cyrillic and ch in CYRILLIC_SYMBOLS:
                target_lay = "ru" if "ru" in kde_layout_map else ("ua" if "ua" in kde_layout_map else "us")
                sync_layout(target_lay)
                kc, shift = CYRILLIC_SYMBOLS[ch]
                emit_keypress(kc, shift)
                continue

            # Resolve character to exact active layout and keycode
            res = resolve_character_target(ch)
            if res:
                target_lay, kc, shift, is_altgr = res
                last_input_was_cyrillic = (target_lay in ("ru", "ua", "bg"))
                sync_layout(target_lay)
                if is_altgr:
                    emit_altgr_keypress(kc, shift)
                else:
                    emit_keypress(kc, shift)

        return {"success": True}

    async def _main(self):
        auto_setup_system_xkb()
        init_uinput_device()
        self.watcher_task = asyncio.create_task(auto_background_watcher())
        logger.info("Alt_Shift Universal background watcher & backend loaded cleanly.")

    async def _unload(self):
        if self.watcher_task:
            self.watcher_task.cancel()
        destroy_uinput_device()
        logger.info("Alt_Shift Universal backend unloaded.")
