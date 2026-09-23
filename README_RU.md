# Alt_Shift

<div align="center">

**Плагин для Decky Loader: исправление ввода экранной клавиатуры Steam (OSK) в Wayland и Game Mode**

[ English ](README.md) • [ Русский ](README_RU.md)

[![Decky Loader](https://img.shields.io/badge/Decky_Loader-Plugin-00adff?style=for-the-badge&logo=steamdeck&logoColor=white)](https://deckyloader.ru/)
[![GitHub Release](https://img.shields.io/github/v/release/Kowalski-coder/Alt_Shift?style=for-the-badge&color=green)](https://github.com/Kowalski-coder/Alt_Shift/releases)
[![License](https://img.shields.io/badge/License-BSD_3--Clause-blue?style=for-the-badge)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-SteamOS_%7C_Arch_Wayland-orange?style=for-the-badge)](https://archlinux.org/)

</div>

Плагин для каталога **[Decky Loader](https://deckyloader.ru/)**, полностью исправляющий ввод с виртуальной экранной клавиатуры Steam (OSK) в окружении **Wayland / X11** (KDE Plasma Desktop Mode) и **Game Mode (Gamescope)** на SteamOS и других arch-based дистрибутивах.

---

## 📌 В чём была проблема?

Родной движок виртуальной клавиатуры Steam (`steamui.so`) эмулирует нажатия клавиш через устаревший протокол X11 `XTestFakeKeyEvent`.
В современных Wayland-сессиях:
1. **Блокировка ввода в нативные Wayland-окна:** Wayland-композиторы (KWin Wayland, Gamescope) изолируют окна от синтетических событий XTest, из-за чего экранная клавиатура в ряде приложений не печатает вообще либо печатает цифры (`'1'`) вместо букв.
2. **Отсутствие русской раскладки в X11/XKB:** При попытке напечатать русский символ `XKeysymToKeycode` завершается с ошибкой и подставляет keycode 2 (`KEY_1`).
3. **Дублирование и троение символов:** При попытке стандартной трансляции клавиши дублировались (по 2-3 одинаковых символа на одно нажатие).
4. **Рассинхронизация языка:** Переключение раскладки на экранной клавиатуре не передавалось системному композитору.

---

## ✨ Возможности плагина

- ⌨️ **Аппаратный ввод через Linux `/dev/uinput`:** Прямая трансляция нажатий клавиш через виртуальное ядровое устройство ввода (`evdev`). Работает в любых Wayland и XWayland окнах, играх и терминале.
- 🎯 **Одиночный и чистый ввод:** Перехват вызовов `SteamClient.Input.ControllerKeyboardSendText` в интерфейсе Steam CEF и подавление дублирования (никакого двоения или троения символов).
- 🔄 **Автоматическая динамическая синхронизация раскладок:**
  - **Режим рабочего стола (KDE Plasma):** Мгновенное переключение раскладок через системную шину D-Bus (`org.kde.keyboard /Layouts`) с динамическим определением индексов языков.
  - **Игровой режим (Gamescope):** Синхронизация раскладки при вводе символов.
- 🇷🇺 **Полная поддержка русской раскладки:** Корректный ввод всех 33 букв русского алфавита в строчном и заглавном регистрах, знаков препинания, цифр и спецклавиш (`Backspace`, `Enter`, `Tab`, стрелки, `Escape`).
- ⚡ **Работа сразу из коробки (Zero-Reboot Setup):** Плагин при загрузке автоматически конфигурирует системные переменные окружения XKB и службы KDE на лету — перезагрузка устройства после установки не требуется.
- 🎛 **Минималистичный интерфейс:** Не перегружает меню Quick Access Menu (QAM). Плагин можно скрыть в настройках Decky Loader — он продолжит работать в фоне.

---

## 📦 Установка

1. Скачайте релизный архив **`Alt_Shift.zip`** со страницы **[GitHub Releases](https://github.com/Kowalski-coder/Alt_Shift/releases)**.
2. На Steam Deck откройте меню **Decky Loader** (кнопка `...`).
3. Нажмите на **значок шестерёнки** (Настройки Decky Loader) -> вкладка **Разработчик (Developer)**.
4. Выберите **«Установить плагин из ZIP»** и укажите скачанный архив `Alt_Shift.zip`.

---

## 🛠 Сборка из исходников

Для сборки проекта требуются **Node.js** и **pnpm** (или npm):

```bash
# Клонировать репозиторий
git clone https://github.com/Kowalski-coder/Alt_Shift.git
cd Alt_Shift

# Установить зависимости
pnpm install

# Собрать фронтенд
pnpm run build

# Упаковать релизный ZIP-архив
rm -rf /tmp/decky-pack && mkdir -p /tmp/decky-pack/Alt_Shift/dist
cp dist/index.js /tmp/decky-pack/Alt_Shift/dist/
cp main.py plugin.json package.json README.md README_RU.md LICENSE /tmp/decky-pack/Alt_Shift/
(cd /tmp/decky-pack && zip -r ~/Alt_Shift.zip Alt_Shift)
```

---

## 📁 Структура проекта

```text
Alt_Shift/
├── dist/
│   └── index.js           # Скомпилированный фронтенд (Decky IIFE bundle)
├── src/
│   └── index.tsx          # Исходный код хука Steam CEF и QAM интерфейса
├── main.py                # Python бэкенд (uinput драйвер, D-Bus XKB синхронизация)
├── plugin.json            # Манифест плагина для Decky Loader
├── package.json           # Описание пакета и скрипты сборки
├── tsconfig.json          # Конфигурация TypeScript
├── rollup.config.js       # Конфигурация бандлера Rollup
├── LICENSE                # Лицензия BSD-3-Clause
├── README.md              # Документация (English - Default)
└── README_RU.md           # Документация (Русский)
```

---

## 👤 Автор и лицензия

- **Автор:** [Kowalski](https://github.com/Kowalski-coder)
- **Лицензия:** [BSD-3-Clause](LICENSE)
