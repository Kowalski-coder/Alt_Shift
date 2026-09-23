import {
  definePlugin,
  PanelSection,
  PanelSectionRow,
  ServerAPI,
  staticClasses
} from "decky-frontend-lib";
import React, { VFC, useEffect, useState } from "react";
import { FaKeyboard, FaGlobe, FaCheckCircle } from "react-icons/fa";

interface LayoutsInfo {
  active_layouts: string[];
  kde_indices: Record<string, number>;
}

const KeyboardIcon: any = FaKeyboard;
const GlobeIcon: any = FaGlobe;
const CheckIcon: any = FaCheckCircle;

function installHook(serverApi: ServerAPI) {
  try {
    const steamClient = (window as any).SteamClient;
    const nativeFn = (window as any)._orig_sendText_native || (steamClient?.Input?.ControllerKeyboardSendText);
    if (nativeFn) {
      (window as any)._orig_sendText_native = nativeFn;
      steamClient.Input.ControllerKeyboardSendText = function (text: string) {
        try {
          let active = document.activeElement as HTMLElement | null;
          while (active && active.shadowRoot && active.shadowRoot.activeElement) {
            active = active.shadowRoot.activeElement as HTMLElement;
          }

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
          console.error("[Alt_Shift_Universal] sendText error:", err);
          serverApi.callPluginMethod("send_key", { text });
        }
      };
      console.log("[Alt_Shift_Universal] Installed KeyboardSendText hook successfully.");
    }
  } catch (e) {
    console.error("[Alt_Shift_Universal] Hook installation failed:", e);
  }
}

function uninstallHook() {
  try {
    const steamClient = (window as any).SteamClient;
    if ((window as any)._orig_sendText_native && steamClient?.Input) {
      steamClient.Input.ControllerKeyboardSendText = (window as any)._orig_sendText_native;
      console.log("[Alt_Shift_Universal] Uninstalled hook.");
    }
  } catch (e) {
    console.error("[Alt_Shift_Universal] Uninstall error:", e);
  }
}

const Content: VFC = () => {
  return (
    <PanelSection>
      <PanelSectionRow>
        <div style={{ lineHeight: "1.45", color: "#dcdedf", fontSize: "0.95em", padding: "4px 0" }}>
          Универсальный ввод экранной клавиатуры (OSK) для любых раскладок Steam.
        </div>
      </PanelSectionRow>
      <PanelSectionRow>
        <div style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "0.85em", color: "#a1cd44", marginTop: "4px" }}>
          <CheckIcon />
          <span>Синхронизация ввода активна</span>
        </div>
      </PanelSectionRow>

      <PanelSectionRow>
        <div style={{ fontSize: "0.8em", color: "#8f98a0", marginTop: "12px", lineHeight: "1.4" }}>
          Плагин автоматически согласует символы экранной клавиатуры Steam с системой и играми.
        </div>
      </PanelSectionRow>
    </PanelSection>
  );
};

export default definePlugin((serverApi: ServerAPI) => {
  installHook(serverApi);

  return {
    title: <div className={staticClasses.Title}>Alt_Shift Universal</div>,
    content: <Content />,
    icon: <KeyboardIcon />,
    onDismount() {
      uninstallHook();
    },
  };
});
