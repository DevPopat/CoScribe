import React from "react";
import type { EditorStatus as EditorStatusType } from "../../types";

interface EditorStatusProps {
  status: EditorStatusType;
}

const DOT_COLORS: Record<string, string> = {
  rich: "green",
  plain: "orange",
  none: "red",
};

export default function EditorStatus({ status }: EditorStatusProps) {
  const color = DOT_COLORS[status.tier] ?? "red";
  const label = status.detected
    ? `${status.element} (${status.tier})`
    : "No editor detected";

  return (
    <div className="editor-status" data-testid="editor-status">
      <span
        className="editor-status-dot"
        data-testid="editor-status-dot"
        style={{
          display: "inline-block",
          width: 8,
          height: 8,
          borderRadius: "50%",
          backgroundColor: color,
          marginRight: 6,
        }}
      />
      <span data-testid="editor-status-label">{label}</span>
    </div>
  );
}
