# Alt_Shift

<div align="center">

**Decky Loader plugin: Fixes Steam On-Screen Keyboard (OSK) input and layout switching in Wayland & Game Mode**

[ English ](README.md) • [ Русский ](README_RU.md)

[![Decky Loader](https://img.shields.io/badge/Decky_Loader-Plugin-00adff?style=for-the-badge&logo=steamdeck&logoColor=white)](https://deckyloader.ru/)
[![GitHub Release](https://img.shields.io/github/v/release/Kowalski-coder/Alt_Shift?style=for-the-badge&color=green)](https://github.com/Kowalski-coder/Alt_Shift/releases)
[![License](https://img.shields.io/badge/License-BSD_3--Clause-blue?style=for-the-badge)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-SteamOS_%7C_Arch_Wayland-orange?style=for-the-badge)](https://archlinux.org/)

</div>

A plugin for **[Decky Loader](https://deckyloader.ru/)** that resolves Steam virtual on-screen keyboard (OSK) input and layout switching issues in **Wayland / X11** (KDE Plasma Desktop Mode) and **Game Mode (Gamescope)** on SteamOS and other Arch-based distributions.

---

## 📌 Background: What was the issue?

Steam's native on-screen keyboard engine (`steamui.so`) emulates keystrokes using the legacy X11 protocol `XTestFakeKeyEvent`.
In modern Wayland sessions:
1. **Input blocked in native Wayland windows:** Wayland compositors (KWin Wayland, Gamescope) isolate client windows from synthetic XTest events, causing the OSK to fail to type or output unwanted numbers (`'1'`) instead of characters.
2. **Missing secondary layouts in X11/XKB:** Attempting to type non-Latin/Cyrillic characters causes `XKeysymToKeycode` failures resulting in keycode 2 (`KEY_1`).
3. **Double / Triple typing:** Naive injection attempts often result in duplicate or triplicate key presses per touch.
4. **Layout desynchronization:** Toggling language layouts on the virtual keyboard does not propagate to the system compositor.

---

## ✨ Features

- ⌨️ **Kernel-level hardware input via Linux `/dev/uinput`:** Direct keystroke injection through virtual kernel input device (`evdev`). Compatible with all Wayland and XWayland windows, games, and terminals.
- 🎯 **Clean single-strike input:** Intercepts `SteamClient.Input.ControllerKeyboardSendText` in Steam CEF to prevent character duplication.
- 🔄 **Dynamic layout synchronization:**
  - **Desktop Mode (KDE Plasma):** Instantaneous layout switching via D-Bus (`org.kde.keyboard /Layouts`) with dynamic layout index discovery.
  - **Game Mode (Gamescope):** Automatic layout synchronization upon character input.
- 🇷🇺 **Comprehensive Cyrillic support:** Correct input for all Cyrillic letters (uppercase and lowercase), punctuation, digits, and special keys (`Backspace`, `Enter`, `Tab`, arrows, `Escape`).
- ⚡ **Zero-Reboot Setup:** Automatically initializes system XKB environment and KDE daemon states on startup — no console reboot required after installation.
- 🎛 **Minimalist footprint:** No cluttered UI in Quick Access Menu (QAM). Can be hidden in Decky Loader settings while continuing to run in the background.

---

## 📦 Installation

1. Download the release archive **`Alt_Shift.zip`** from **[GitHub Releases](https://github.com/Kowalski-coder/Alt_Shift/releases)** (or [GitFlic Mirror](https://gitflic.ru/project/viktorkoval1997/alt_shift/release)).
2. On your Steam Deck, open the **Decky Loader** menu (`...` button).
3. Click the **Gear icon** (Decky Loader Settings) -> **Developer** tab.
4. Select **"Install plugin from ZIP"** and choose the downloaded `Alt_Shift.zip`.

---

## 🛠 Building from source

Requires **Node.js** and **pnpm** (or npm):

```bash
# Clone the repository
git clone https://github.com/Kowalski-coder/Alt_Shift.git
cd Alt_Shift

# Install dependencies
pnpm install

# Build frontend bundle
pnpm run build

# Package release ZIP archive
rm -rf /tmp/decky-pack && mkdir -p /tmp/decky-pack/Alt_Shift/dist
cp dist/index.js /tmp/decky-pack/Alt_Shift/dist/
cp main.py plugin.json package.json README.md README_RU.md LICENSE /tmp/decky-pack/Alt_Shift/
(cd /tmp/decky-pack && zip -r ~/Alt_Shift.zip Alt_Shift)
```

---

## 📁 Project Structure

```text
Alt_Shift/
├── dist/
│   └── index.js           # Compiled frontend (Decky IIFE bundle)
├── src/
│   └── index.tsx          # Steam CEF hook & QAM interface component
├── main.py                # Python backend (uinput driver, D-Bus XKB sync)
├── plugin.json            # Decky Loader plugin manifest
├── package.json           # Package description & build scripts
├── tsconfig.json          # TypeScript configuration
├── rollup.config.js       # Rollup bundler configuration
├── LICENSE                # BSD-3-Clause License
├── README.md              # Documentation (English)
└── README_RU.md           # Documentation (Russian)
```

---

## 👤 Author & License

- **Author:** [Kowalski](https://github.com/Kowalski-coder)
- **License:** [BSD-3-Clause](LICENSE)
