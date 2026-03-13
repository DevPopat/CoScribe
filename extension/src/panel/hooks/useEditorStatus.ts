// Hook that polls the active tab's content script for editor detection status.

import { useEffect, useState } from "react";
import type { EditorStatus } from "../../types";

const DEFAULT_STATUS: EditorStatus = {
  detected: false,
  tier: "none",
  element: null,
};

export default function useEditorStatus(): EditorStatus {
  const [status, setStatus] = useState<EditorStatus>(DEFAULT_STATUS);

  useEffect(() => {
    let cancelled = false;

    async function poll() {
      try {
        const [tab] = await chrome.tabs.query({
          active: true,
          currentWindow: true,
        });
        if (!tab?.id) return;

        const response = await chrome.tabs.sendMessage(tab.id, {
          type: "DETECT_EDITOR",
        });
        if (!cancelled && response) {
          setStatus(response as EditorStatus);
        }
      } catch {
        // Content script not injected or tab not available
        if (!cancelled) setStatus(DEFAULT_STATUS);
      }
    }

    poll();
    const interval = setInterval(poll, 3000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  return status;
}
