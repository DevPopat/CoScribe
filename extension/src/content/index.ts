// Content script injected into web pages.
// Listens for messages from the panel/background to insert text into editors.

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message.type === "PING") {
    sendResponse({ ok: true });
  }
});
