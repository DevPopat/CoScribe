// Service worker for the CoScribe extension.
// Opens the side panel when the extension action icon is clicked.

chrome.action.onClicked.addListener((tab) => {
  if (tab.id !== undefined) {
    chrome.sidePanel.open({ tabId: tab.id });
  }
});
