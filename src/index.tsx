import {
  definePlugin,
  DropdownItem,
  PanelSection,
  PanelSectionRow,
  ServerAPI,
  staticClasses
} from "decky-frontend-lib";
import React, { VFC, useState, useEffect } from "react";
import { FaKeyboard } from "react-icons/fa";

function findActiveInput(): HTMLElement | null {
  function searchDoc(doc: Document): HTMLElement | null {
    try {
      let active = doc.activeElement as HTMLElement | null;
      while (active) {
        if (active.shadowRoot && active.shadowRoot.activeElement) {
          active = active.shadowRoot.activeElement as HTMLElement;
        } else if (active.tagName === "IFRAME") {
          try {
            const frameDoc = (active as HTMLIFrameElement).contentDocument;
            if (frameDoc && frameDoc.activeElement) {
              active = frameDoc.activeElement as HTMLElement;
            } else {
              break;
            }
          } catch (e) {
            break;
          }
        } else {
          break;
        }
      }
      if (active && (active.tagName === "INPUT" || active.tagName === "TEXTAREA" || (active as any).isContentEditable)) {
        return active;
      }
    } catch (e) {}
    return null;
  }

  let el = searchDoc(document);
  if (el) return el;

  try {
    if (window.top && window.top !== window && window.top.document) {
      el = searchDoc(window.top.document);
      if (el) return el;
    }
  } catch (e) {}

  return null;
}

function installHook(serverApi: ServerAPI) {
  try {
    const steamClient = (window as any).SteamClient;
    const nativeFn = (window as any)._orig_sendText_native || (steamClient?.Input?.ControllerKeyboardSendText);
    if (nativeFn) {
      (window as any)._orig_sendText_native = nativeFn;
      steamClient.Input.ControllerKeyboardSendText = function (text: string) {
        try {
          const active = findActiveInput();
          if (active) {
            const doc = active.ownerDocument || document;
            if (text === "\x02" || text === "\x08" || text === "Backspace") {
              doc.execCommand("delete", false, undefined);
            } else if (text === "\r" || text === "\n" || text === "\x03" || text === "Enter") {
              const enterEvt = new KeyboardEvent("keydown", { key: "Enter", code: "Enter", keyCode: 13, which: 13, bubbles: true });
              active.dispatchEvent(enterEvt);
            } else if (text && text.length > 0 && text.charCodeAt(0) >= 32) {
              doc.execCommand("insertText", false, text);
            }
          } else {
            serverApi.callPluginMethod("send_key", { text });
          }
        } catch (err) {
          console.error("[Wayland OSK Fix] sendText error:", err);
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

const Content: VFC<{ serverApi: ServerAPI }> = ({ serverApi }) => {
  const [primaryLayout, setPrimaryLayout] = useState<string>("ru");

  useEffect(() => {
    serverApi.callPluginMethod("get_settings", {}).then((res) => {
      if (res?.success && res?.result?.primary_gamescope_layout) {
        setPrimaryLayout(res.result.primary_gamescope_layout);
      }
    });
  }, []);

  const handleLayoutChange = (opt: any) => {
    const val = opt.data;
    setPrimaryLayout(val);
    serverApi.callPluginMethod("set_settings", {
      settings: { primary_gamescope_layout: val }
    });
  };

  return (
    <PanelSection>
      <PanelSectionRow>
        <DropdownItem
          label="Раскладка в Game Mode"
          description="Порядок системных раскладок в игровом режиме"
          rgOptions={[
            { label: "Русская (по умолчанию)", data: "ru" },
            { label: "Английская", data: "us" },
          ]}
          selectedOption={primaryLayout}
          onChange={handleLayoutChange}
        />
      </PanelSectionRow>
      <PanelSectionRow>
        <div style={{ lineHeight: "1.45", color: "#8f98a0", fontSize: "0.85em", marginTop: "8px" }}>
          Плагин перехватывает ввод экранной клавиатуры и автоматически согласует системную раскладку
        </div>
      </PanelSectionRow>
    </PanelSection>
  );
};

export default definePlugin((serverApi: ServerAPI) => {
  installHook(serverApi);

  return {
    title: <div className={staticClasses.Title}>Wayland OSK Fix</div>,
    content: <Content serverApi={serverApi} />,
    icon: <FaKeyboard />,
    onDismount() {
      uninstallHook();
    },
  };
});
