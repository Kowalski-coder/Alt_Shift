import {
  definePlugin,
  PanelSection,
  PanelSectionRow,
  ServerAPI,
  staticClasses
} from "decky-frontend-lib";
import React, { VFC } from "react";
import { FaKeyboard } from "react-icons/fa";

const RU_REGEX = /[а-яёА-ЯЁ]/;
const LATIN_REGEX = /[a-zA-Z]/;

let layoutCheckInterval: any = null;
let lastDetectedLang: string | null = null;

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

function detectVisibleKeyboardLayout(): "ru" | "us" | null {
  try {
    const docs = [document];
    if (window.top && window.top !== window && window.top.document) {
      docs.push(window.top.document);
    }

    for (const doc of docs) {
      // Look for keyboard key elements in DOM
      const keyElements = doc.querySelectorAll("button, div, span");
      let foundRu = 0;
      let foundUs = 0;

      for (let i = 0; i < keyElements.length; i++) {
        const text = keyElements[i].textContent?.trim();
        if (text && text.length === 1) {
          if (RU_REGEX.test(text)) {
            foundRu++;
            if (foundRu >= 2) return "ru";
          } else if (LATIN_REGEX.test(text)) {
            foundUs++;
            if (foundUs >= 5 && foundRu === 0) return "us";
          }
        }
      }
      if (foundRu > 0) return "ru";
      if (foundUs > 0) return "us";
    }
  } catch (e) {}
  return null;
}

function startLayoutObserver(serverApi: ServerAPI) {
  if (layoutCheckInterval) {
    clearInterval(layoutCheckInterval);
  }

  layoutCheckInterval = setInterval(() => {
    try {
      const detected = detectVisibleKeyboardLayout();
      if (detected && detected !== lastDetectedLang) {
        lastDetectedLang = detected;
        serverApi.callPluginMethod("sync_layout", { lang: detected });
      }
    } catch (e) {}
  }, 400);

  // Also listen for pointer clicks on document to react immediately on layout switch button tap
  const clickHandler = () => {
    setTimeout(() => {
      const detected = detectVisibleKeyboardLayout();
      if (detected && detected !== lastDetectedLang) {
        lastDetectedLang = detected;
        serverApi.callPluginMethod("sync_layout", { lang: detected });
      }
    }, 50);
  };
  window.addEventListener("pointerdown", clickHandler, { passive: true });
  window.addEventListener("click", clickHandler, { passive: true });
}

function stopLayoutObserver() {
  if (layoutCheckInterval) {
    clearInterval(layoutCheckInterval);
    layoutCheckInterval = null;
  }
}

function installHook(serverApi: ServerAPI) {
  try {
    const steamClient = (window as any).SteamClient;
    const nativeFn = (window as any)._orig_sendText_native || (steamClient?.Input?.ControllerKeyboardSendText);
    if (nativeFn) {
      (window as any)._orig_sendText_native = nativeFn;
      steamClient.Input.ControllerKeyboardSendText = function (text: string) {
        try {
          if (RU_REGEX.test(text)) {
            lastDetectedLang = "ru";
            serverApi.callPluginMethod("sync_layout", { lang: "ru" });
          } else if (LATIN_REGEX.test(text)) {
            lastDetectedLang = "us";
            serverApi.callPluginMethod("sync_layout", { lang: "us" });
          }

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
    stopLayoutObserver();
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
          Плагин перехватывает ввод экранной клавиатуры и автоматически синхронизирует системную раскладку в окружении Wayland и Game Mode
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
  startLayoutObserver(serverApi);

  return {
    title: <div className={staticClasses.Title}>Wayland OSK Fix</div>,
    content: <Content />,
    icon: <FaKeyboard />,
    onDismount() {
      uninstallHook();
    },
  };
});
