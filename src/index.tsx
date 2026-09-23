import {
  definePlugin,
  PanelSection,
  PanelSectionRow,
  ServerAPI,
  staticClasses
} from "decky-frontend-lib";
import React, { VFC } from "react";
import { FaKeyboard } from "react-icons/fa";

function handleIncomingInput(text: string, serverApi: ServerAPI) {
  try {
    if (text === undefined || text === null || text === "") return;

    const isEnter = (
      text === "\x01" ||
      text === "\r" ||
      text === "\n" ||
      text === "\r\n" ||
      text === "\x03" ||
      text === "\x0a" ||
      text === "\x0d" ||
      text === "Enter" ||
      text === "Return" ||
      text === "Submit" ||
      text === "Done"
    );

    const isBackspace = (
      text === "\x02" ||
      text === "\x08" ||
      text === "\x7f" ||
      text === "Backspace" ||
      text === "Delete"
    );

    const payload = isEnter ? "Enter" : (isBackspace ? "Backspace" : text);
    serverApi.callPluginMethod("send_key", { text: payload });
  } catch (err) {
    console.error("[Alt_Shift] handleIncomingInput error:", err);
  }
}

function installHook(serverApi: ServerAPI) {
  try {
    const steamClient = (window as any).SteamClient;
    if (!steamClient?.Input) return;

    // 1. ControllerKeyboardSendText (typing text / enter)
    const nativeSendText = (window as any)._orig_sendText_native || steamClient.Input.ControllerKeyboardSendText;
    if (nativeSendText) {
      (window as any)._orig_sendText_native = nativeSendText;
      steamClient.Input.ControllerKeyboardSendText = function (text: string) {
        handleIncomingInput(text, serverApi);
      };
      console.log("[Alt_Shift] Hooked ControllerKeyboardSendText.");
    }

    // 2. ControllerKeyboardSetKeyState (Keycodes / Triggers like L2)
    const nativeSetKeyState = (window as any)._orig_setKeyState_native || steamClient.Input.ControllerKeyboardSetKeyState;
    if (nativeSetKeyState) {
      (window as any)._orig_setKeyState_native = nativeSetKeyState;
      steamClient.Input.ControllerKeyboardSetKeyState = function (key: any, bPressed: any) {
        if (bPressed === true || bPressed === 1 || bPressed === "1" || bPressed === undefined) {
          if (
            key === 13 ||
            key === 28 ||
            key === "13" ||
            key === "28" ||
            key === "Enter" ||
            key === "Return" ||
            key === "\n" ||
            key === "\r"
          ) {
            handleIncomingInput("Enter", serverApi);
          } else if (
            key === 8 ||
            key === 14 ||
            key === "8" ||
            key === "14" ||
            key === "Backspace" ||
            key === "\x08"
          ) {
            handleIncomingInput("Backspace", serverApi);
          } else if (key === 27 || key === 1 || key === "Escape" || key === "Esc") {
            handleIncomingInput("Escape", serverApi);
          } else if (key === 9 || key === 15 || key === "Tab") {
            handleIncomingInput("Tab", serverApi);
          }
        }
      };
      console.log("[Alt_Shift] Hooked ControllerKeyboardSetKeyState.");
    }

    // 3. ControllerKeyboardSubmit (L2 / Done / Submit button)
    const nativeSubmit = (window as any)._orig_submit_native || steamClient.Input.ControllerKeyboardSubmit;
    if (nativeSubmit) {
      (window as any)._orig_submit_native = nativeSubmit;
      steamClient.Input.ControllerKeyboardSubmit = function () {
        handleIncomingInput("Enter", serverApi);
        try {
          return nativeSubmit.apply(this, arguments);
        } catch (e) {}
      };
      console.log("[Alt_Shift] Hooked ControllerKeyboardSubmit.");
    }

    // 4. ControllerKeyboardSendKey (integer / string keycodes)
    const nativeSendKey = (window as any)._orig_sendKey_native || steamClient.Input.ControllerKeyboardSendKey;
    if (nativeSendKey) {
      (window as any)._orig_sendKey_native = nativeSendKey;
      steamClient.Input.ControllerKeyboardSendKey = function (key: any) {
        if (key === 13 || key === 28 || key === "Enter" || key === "\n" || key === "\r") {
          handleIncomingInput("Enter", serverApi);
        } else if (key === 8 || key === 14 || key === "Backspace") {
          handleIncomingInput("Backspace", serverApi);
        } else {
          handleIncomingInput(String(key), serverApi);
        }
      };
      console.log("[Alt_Shift] Hooked ControllerKeyboardSendKey.");
    }
  } catch (e) {
    console.error("[Alt_Shift] Hook installation failed:", e);
  }
}

function uninstallHook() {
  try {
    const steamClient = (window as any).SteamClient;
    if (steamClient?.Input) {
      if ((window as any)._orig_sendText_native) {
        steamClient.Input.ControllerKeyboardSendText = (window as any)._orig_sendText_native;
      }
      if ((window as any)._orig_setKeyState_native) {
        steamClient.Input.ControllerKeyboardSetKeyState = (window as any)._orig_setKeyState_native;
      }
      if ((window as any)._orig_submit_native) {
        steamClient.Input.ControllerKeyboardSubmit = (window as any)._orig_submit_native;
      }
      if ((window as any)._orig_sendKey_native) {
        steamClient.Input.ControllerKeyboardSendKey = (window as any)._orig_sendKey_native;
      }
      console.log("[Alt_Shift] Uninstalled hooks.");
    }
  } catch (e) {
    console.error("[Alt_Shift] Uninstall error:", e);
  }
}

const Content: VFC = () => {
  return (
    <PanelSection>
      <PanelSectionRow>
        <div style={{ lineHeight: "1.45", color: "#dcdedf", fontSize: "0.95em", padding: "4px 0" }}>
          Плагин перехватывает ввод экранной клавиатуры и автоматически синхронизирует раскладку в Wayland и Game Mode.
        </div>
      </PanelSectionRow>
      <PanelSectionRow>
        <div style={{ fontSize: "0.85em", color: "#8f98a0", marginTop: "12px", lineHeight: "1.4" }}>
          Вы можете скрыть плагин в настройках Decky Loader, он продолжит работать в фоне.
        </div>
      </PanelSectionRow>
    </PanelSection>
  );
};

export default definePlugin((serverApi: ServerAPI) => {
  installHook(serverApi);

  return {
    title: <div className={staticClasses.Title}>Alt_Shift</div>,
    content: <Content />,
    icon: <FaKeyboard />,
    onDismount() {
      uninstallHook();
    },
  };
});
