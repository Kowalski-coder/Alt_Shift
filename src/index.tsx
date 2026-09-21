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

function detectVisibleKeyboardLayout(): "ru" | "us" | null {
  try {
    const docs = [document];
    if (window.top && window.top !== window && window.top.document) {
      docs.push(window.top.document);
    }

    for (const doc of docs) {
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
  }, 250);

  const clickHandler = () => {
    setTimeout(() => {
      const detected = detectVisibleKeyboardLayout();
      if (detected && detected !== lastDetectedLang) {
        lastDetectedLang = detected;
        serverApi.callPluginMethod("sync_layout", { lang: detected });
      }
    }, 30);
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
            if (lastDetectedLang !== "ru") {
              lastDetectedLang = "ru";
              serverApi.callPluginMethod("sync_layout", { lang: "ru" });
            }
          } else if (LATIN_REGEX.test(text)) {
            if (lastDetectedLang !== "us") {
              lastDetectedLang = "us";
              serverApi.callPluginMethod("sync_layout", { lang: "us" });
            }
          }
        } catch (err) {
          console.error("[Alt_Shift] sync_layout error:", err);
        }
        // ALWAYS pass through to Steam native function
        return nativeFn.apply(this, arguments);
      };
      console.log("[Alt_Shift] Installed KeyboardSendText hook successfully with native pass-through.");
    }
  } catch (e) {
    console.error("[Alt_Shift] Hook installation failed:", e);
  }
}

function uninstallHook() {
  try {
    stopLayoutObserver();
    const steamClient = (window as any).SteamClient;
    if ((window as any)._orig_sendText_native && steamClient?.Input) {
      steamClient.Input.ControllerKeyboardSendText = (window as any)._orig_sendText_native;
      console.log("[Alt_Shift] Uninstalled hook.");
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
          Плагин отслеживает ввод экранной клавиатуры и автоматически синхронизирует системную раскладку в Desktop Mode и Game Mode.
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
  serverApi.callPluginMethod("reset_game_mode", {});
  installHook(serverApi);
  startLayoutObserver(serverApi);

  return {
    title: <div className={staticClasses.Title}>Alt_Shift</div>,
    content: <Content />,
    icon: <FaKeyboard />,
    onDismount() {
      uninstallHook();
    },
  };
});
