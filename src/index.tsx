import {
  definePlugin,
  PanelSection,
  PanelSectionRow,
  ServerAPI,
  staticClasses
} from "decky-frontend-lib";
import React, { VFC } from "react";
import { FaKeyboard } from "react-icons/fa";

function installHook(serverApi: ServerAPI) {
  try {
    const steamClient = (window as any).SteamClient;
    const nativeFn = (window as any)._orig_sendText_native || (steamClient?.Input?.ControllerKeyboardSendText);
    if (nativeFn) {
      (window as any)._orig_sendText_native = nativeFn;
      steamClient.Input.ControllerKeyboardSendText = function (text: string) {
        try {
          const active = document.activeElement as HTMLElement | null;
          const isInput = active && (active.tagName === "INPUT" || active.tagName === "TEXTAREA" || (active as any).isContentEditable);
          if (isInput) {
            if (text === "\x02" || text === "\x08" || text === "Backspace") {
              document.execCommand("delete", false, undefined);
            } else if (text === "\r" || text === "\n" || text === "\x03" || text === "Enter") {
              const enterEvt = new KeyboardEvent("keydown", { key: "Enter", code: "Enter", keyCode: 13, which: 13, bubbles: true });
              active.dispatchEvent(enterEvt);
            } else if (text && text.length > 0 && text.charCodeAt(0) >= 32) {
              document.execCommand("insertText", false, text);
            }
          } else {
            serverApi.callPluginMethod("send_key", { text });
          }
        } catch (err) {
          console.error("[Wayland OSK Fix] callPluginMethod error:", err);
        }
      };
      console.log("[Wayland OSK Fix] Installed KeyboardSendText hook successfully.");
    }
  } catch (e) {
    console.error("[Wayland OSK Fix] Hook installation failed:", e);
  }
}

function uninstallHook() {
  try {
    const steamClient = (window as any).SteamClient;
    if ((window as any)._orig_sendText_native && steamClient?.Input) {
      steamClient.Input.ControllerKeyboardSendText = (window as any)._orig_sendText_native;
      console.log("[Wayland OSK Fix] Uninstalled hook.");
    }
  } catch (e) {
    console.error("[Wayland OSK Fix] Uninstall error:", e);
  }
}

const Content: VFC = () => {
  return (
    <PanelSection>
      <PanelSectionRow>
        <div style={{ lineHeight: "1.45", color: "#dcdedf", fontSize: "0.95em", padding: "4px 0" }}>
          Плагин перехватывает ввод экранной клавиатуры и транслирует через uinput, а также автоматически синхронизирует переключение системной раскладки с экранной клавиатурой в окружении Wayland
        </div>
      </PanelSectionRow>
      <PanelSectionRow>
        <div style={{ fontSize: "0.85em", color: "#8f98a0", marginTop: "12px", lineHeight: "1.4" }}>
          Вы можете скрыть плагин в настройках Decky Loader, он продолжит работать в фоне
        </div>
      </PanelSectionRow>
    </PanelSection>
  );
};

export default definePlugin((serverApi: ServerAPI) => {
  installHook(serverApi);

  return {
    title: <div className={staticClasses.Title}>Wayland OSK Fix</div>,
    content: <Content />,
    icon: <FaKeyboard />,
    onDismount() {
      uninstallHook();
    },
  };
});
