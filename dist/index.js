(function (deckyFrontendLib, React) {
  'use strict';

  function _interopDefaultLegacy (e) { return e && typeof e === 'object' && 'default' in e ? e : { 'default': e }; }

  var React__default = /*#__PURE__*/_interopDefaultLegacy(React);

  var DefaultContext = {
    color: undefined,
    size: undefined,
    className: undefined,
    style: undefined,
    attr: undefined
  };
  var IconContext = React__default["default"].createContext && /*#__PURE__*/React__default["default"].createContext(DefaultContext);

  var _excluded = ["attr", "size", "title"];
  function _objectWithoutProperties(e, t) { if (null == e) return {}; var o, r, i = _objectWithoutPropertiesLoose(e, t); if (Object.getOwnPropertySymbols) { var n = Object.getOwnPropertySymbols(e); for (r = 0; r < n.length; r++) o = n[r], -1 === t.indexOf(o) && {}.propertyIsEnumerable.call(e, o) && (i[o] = e[o]); } return i; }
  function _objectWithoutPropertiesLoose(r, e) { if (null == r) return {}; var t = {}; for (var n in r) if ({}.hasOwnProperty.call(r, n)) { if (-1 !== e.indexOf(n)) continue; t[n] = r[n]; } return t; }
  function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
  function ownKeys(e, r) { var t = Object.keys(e); if (Object.getOwnPropertySymbols) { var o = Object.getOwnPropertySymbols(e); r && (o = o.filter(function (r) { return Object.getOwnPropertyDescriptor(e, r).enumerable; })), t.push.apply(t, o); } return t; }
  function _objectSpread(e) { for (var r = 1; r < arguments.length; r++) { var t = null != arguments[r] ? arguments[r] : {}; r % 2 ? ownKeys(Object(t), !0).forEach(function (r) { _defineProperty(e, r, t[r]); }) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(t)) : ownKeys(Object(t)).forEach(function (r) { Object.defineProperty(e, r, Object.getOwnPropertyDescriptor(t, r)); }); } return e; }
  function _defineProperty(e, r, t) { return (r = _toPropertyKey(r)) in e ? Object.defineProperty(e, r, { value: t, enumerable: !0, configurable: !0, writable: !0 }) : e[r] = t, e; }
  function _toPropertyKey(t) { var i = _toPrimitive(t, "string"); return "symbol" == typeof i ? i : i + ""; }
  function _toPrimitive(t, r) { if ("object" != typeof t || !t) return t; var e = t[Symbol.toPrimitive]; if (void 0 !== e) { var i = e.call(t, r || "default"); if ("object" != typeof i) return i; throw new TypeError("@@toPrimitive must return a primitive value."); } return ("string" === r ? String : Number)(t); }
  function Tree2Element(tree) {
    return tree && tree.map((node, i) => /*#__PURE__*/React__default["default"].createElement(node.tag, _objectSpread({
      key: i
    }, node.attr), Tree2Element(node.child)));
  }
  function GenIcon(data) {
    return props => /*#__PURE__*/React__default["default"].createElement(IconBase, _extends({
      attr: _objectSpread({}, data.attr)
    }, props), Tree2Element(data.child));
  }
  function IconBase(props) {
    var elem = conf => {
      var attr = props.attr,
        size = props.size,
        title = props.title,
        svgProps = _objectWithoutProperties(props, _excluded);
      var computedSize = size || conf.size || "1em";
      var className;
      if (conf.className) className = conf.className;
      if (props.className) className = (className ? className + " " : "") + props.className;
      return /*#__PURE__*/React__default["default"].createElement("svg", _extends({
        stroke: "currentColor",
        fill: "currentColor",
        strokeWidth: "0"
      }, conf.attr, attr, svgProps, {
        className: className,
        style: _objectSpread(_objectSpread({
          color: props.color || conf.color
        }, conf.style), props.style),
        height: computedSize,
        width: computedSize,
        xmlns: "http://www.w3.org/2000/svg"
      }), title && /*#__PURE__*/React__default["default"].createElement("title", null, title), props.children);
    };
    return IconContext !== undefined ? /*#__PURE__*/React__default["default"].createElement(IconContext.Consumer, null, conf => elem(conf)) : elem(DefaultContext);
  }

  // THIS FILE IS AUTO GENERATED
  function FaKeyboard (props) {
    return GenIcon({"tag":"svg","attr":{"viewBox":"0 0 576 512"},"child":[{"tag":"path","attr":{"d":"M528 448H48c-26.51 0-48-21.49-48-48V112c0-26.51 21.49-48 48-48h480c26.51 0 48 21.49 48 48v288c0 26.51-21.49 48-48 48zM128 180v-40c0-6.627-5.373-12-12-12H76c-6.627 0-12 5.373-12 12v40c0 6.627 5.373 12 12 12h40c6.627 0 12-5.373 12-12zm96 0v-40c0-6.627-5.373-12-12-12h-40c-6.627 0-12 5.373-12 12v40c0 6.627 5.373 12 12 12h40c6.627 0 12-5.373 12-12zm96 0v-40c0-6.627-5.373-12-12-12h-40c-6.627 0-12 5.373-12 12v40c0 6.627 5.373 12 12 12h40c6.627 0 12-5.373 12-12zm96 0v-40c0-6.627-5.373-12-12-12h-40c-6.627 0-12 5.373-12 12v40c0 6.627 5.373 12 12 12h40c6.627 0 12-5.373 12-12zm96 0v-40c0-6.627-5.373-12-12-12h-40c-6.627 0-12 5.373-12 12v40c0 6.627 5.373 12 12 12h40c6.627 0 12-5.373 12-12zm-336 96v-40c0-6.627-5.373-12-12-12h-40c-6.627 0-12 5.373-12 12v40c0 6.627 5.373 12 12 12h40c6.627 0 12-5.373 12-12zm96 0v-40c0-6.627-5.373-12-12-12h-40c-6.627 0-12 5.373-12 12v40c0 6.627 5.373 12 12 12h40c6.627 0 12-5.373 12-12zm96 0v-40c0-6.627-5.373-12-12-12h-40c-6.627 0-12 5.373-12 12v40c0 6.627 5.373 12 12 12h40c6.627 0 12-5.373 12-12zm96 0v-40c0-6.627-5.373-12-12-12h-40c-6.627 0-12 5.373-12 12v40c0 6.627 5.373 12 12 12h40c6.627 0 12-5.373 12-12zm-336 96v-40c0-6.627-5.373-12-12-12H76c-6.627 0-12 5.373-12 12v40c0 6.627 5.373 12 12 12h40c6.627 0 12-5.373 12-12zm288 0v-40c0-6.627-5.373-12-12-12H172c-6.627 0-12 5.373-12 12v40c0 6.627 5.373 12 12 12h232c6.627 0 12-5.373 12-12zm96 0v-40c0-6.627-5.373-12-12-12h-40c-6.627 0-12 5.373-12 12v40c0 6.627 5.373 12 12 12h40c6.627 0 12-5.373 12-12z"},"child":[]}]})(props);
  }

  const RU_REGEX = /[а-яёА-ЯЁ]/;
  const LATIN_REGEX = /[a-zA-Z]/;
  let layoutCheckInterval = null;
  let lastDetectedLang = null;
  function findActiveInput() {
      function searchDoc(doc) {
          try {
              let active = doc.activeElement;
              while (active) {
                  if (active.shadowRoot && active.shadowRoot.activeElement) {
                      active = active.shadowRoot.activeElement;
                  }
                  else if (active.tagName === "IFRAME") {
                      try {
                          const frameDoc = active.contentDocument;
                          if (frameDoc && frameDoc.activeElement) {
                              active = frameDoc.activeElement;
                          }
                          else {
                              break;
                          }
                      }
                      catch (e) {
                          break;
                      }
                  }
                  else {
                      break;
                  }
              }
              if (active && (active.tagName === "INPUT" || active.tagName === "TEXTAREA" || active.isContentEditable)) {
                  return active;
              }
          }
          catch (e) { }
          return null;
      }
      let el = searchDoc(document);
      if (el)
          return el;
      try {
          if (window.top && window.top !== window && window.top.document) {
              el = searchDoc(window.top.document);
              if (el)
                  return el;
          }
      }
      catch (e) { }
      return null;
  }
  function detectVisibleKeyboardLayout() {
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
                          if (foundRu >= 2)
                              return "ru";
                      }
                      else if (LATIN_REGEX.test(text)) {
                          foundUs++;
                          if (foundUs >= 5 && foundRu === 0)
                              return "us";
                      }
                  }
              }
              if (foundRu > 0)
                  return "ru";
              if (foundUs > 0)
                  return "us";
          }
      }
      catch (e) { }
      return null;
  }
  function startLayoutObserver(serverApi) {
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
          }
          catch (e) { }
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
  function installHook(serverApi) {
      try {
          const steamClient = window.SteamClient;
          const nativeFn = window._orig_sendText_native || (steamClient?.Input?.ControllerKeyboardSendText);
          if (nativeFn) {
              window._orig_sendText_native = nativeFn;
              steamClient.Input.ControllerKeyboardSendText = function (text) {
                  try {
                      if (RU_REGEX.test(text)) {
                          lastDetectedLang = "ru";
                          serverApi.callPluginMethod("sync_layout", { lang: "ru" });
                      }
                      else if (LATIN_REGEX.test(text)) {
                          lastDetectedLang = "us";
                          serverApi.callPluginMethod("sync_layout", { lang: "us" });
                      }
                      const active = findActiveInput();
                      if (active) {
                          const doc = active.ownerDocument || document;
                          if (text === "\x02" || text === "\x08" || text === "Backspace") {
                              doc.execCommand("delete", false, undefined);
                          }
                          else if (text === "\r" || text === "\n" || text === "\x03" || text === "Enter") {
                              const enterEvt = new KeyboardEvent("keydown", { key: "Enter", code: "Enter", keyCode: 13, which: 13, bubbles: true });
                              active.dispatchEvent(enterEvt);
                          }
                          else if (text && text.length > 0 && text.charCodeAt(0) >= 32) {
                              doc.execCommand("insertText", false, text);
                          }
                      }
                      else {
                          serverApi.callPluginMethod("send_key", { text });
                      }
                  }
                  catch (err) {
                      console.error("[Wayland OSK Fix] sendText error:", err);
                  }
              };
              console.log("[Wayland OSK Fix] Installed KeyboardSendText hook successfully.");
          }
      }
      catch (e) {
          console.error("[Wayland OSK Fix] Hook installation failed:", e);
      }
  }
  function uninstallHook() {
      try {
          stopLayoutObserver();
          const steamClient = window.SteamClient;
          if (window._orig_sendText_native && steamClient?.Input) {
              steamClient.Input.ControllerKeyboardSendText = window._orig_sendText_native;
              console.log("[Wayland OSK Fix] Uninstalled hook.");
          }
      }
      catch (e) {
          console.error("[Wayland OSK Fix] Uninstall error:", e);
      }
  }
  const Content = () => {
      return (React__default["default"].createElement(deckyFrontendLib.PanelSection, null,
          React__default["default"].createElement(deckyFrontendLib.PanelSectionRow, null,
              React__default["default"].createElement("div", { style: { lineHeight: "1.45", color: "#dcdedf", fontSize: "0.95em", padding: "4px 0" } }, "\u041F\u043B\u0430\u0433\u0438\u043D \u043F\u0435\u0440\u0435\u0445\u0432\u0430\u0442\u044B\u0432\u0430\u0435\u0442 \u0432\u0432\u043E\u0434 \u044D\u043A\u0440\u0430\u043D\u043D\u043E\u0439 \u043A\u043B\u0430\u0432\u0438\u0430\u0442\u0443\u0440\u044B \u0438 \u0430\u0432\u0442\u043E\u043C\u0430\u0442\u0438\u0447\u0435\u0441\u043A\u0438 \u0441\u0438\u043D\u0445\u0440\u043E\u043D\u0438\u0437\u0438\u0440\u0443\u0435\u0442 \u0441\u0438\u0441\u0442\u0435\u043C\u043D\u0443\u044E \u0440\u0430\u0441\u043A\u043B\u0430\u0434\u043A\u0443 \u0432 \u043E\u043A\u0440\u0443\u0436\u0435\u043D\u0438\u0438 Wayland \u0438 Game Mode")),
          React__default["default"].createElement(deckyFrontendLib.PanelSectionRow, null,
              React__default["default"].createElement("div", { style: { fontSize: "0.85em", color: "#8f98a0", marginTop: "12px", lineHeight: "1.4" } }, "\u0412\u044B \u043C\u043E\u0436\u0435\u0442\u0435 \u0441\u043A\u0440\u044B\u0442\u044C \u043F\u043B\u0430\u0433\u0438\u043D \u0432 \u043D\u0430\u0441\u0442\u0440\u043E\u0439\u043A\u0430\u0445 Decky Loader, \u043E\u043D \u043F\u0440\u043E\u0434\u043E\u043B\u0436\u0438\u0442 \u0440\u0430\u0431\u043E\u0442\u0430\u0442\u044C \u0432 \u0444\u043E\u043D\u0435"))));
  };
  var index = deckyFrontendLib.definePlugin((serverApi) => {
      installHook(serverApi);
      startLayoutObserver(serverApi);
      return {
          title: React__default["default"].createElement("div", { className: deckyFrontendLib.staticClasses.Title }, "Wayland OSK Fix"),
          content: React__default["default"].createElement(Content, null),
          icon: React__default["default"].createElement(FaKeyboard, null),
          onDismount() {
              uninstallHook();
          },
      };
  });

  return index;

})(DFL, SP_REACT);
