// Shared TypeScript types mirroring the backend data shapes.

export type SessionStatus =
  | "pending"
  | "planning"
  | "outline_ready"
  | "drafting"
  | "complete";

export interface Section {
  title: string;
  key_points: string[];
  draft: string | null;
  approved: boolean;
}

export interface Outline {
  title: string;
  brief: string;
  tone_guidance: string;
  sections: Section[];
}

export interface WritingSession {
  id: string;
  topic: string;
  audience: string;
  notes: string;
  writing_samples: string[];
  reference_urls: string[];
  status: SessionStatus;
  outline: Outline | null;
  refinement_history: { role: "user" | "assistant"; content: string }[];
}

export interface CreateSessionParams {
  topic: string;
  audience: string;
  notes?: string;
  writing_samples?: string[];
  reference_urls?: string[];
}

export interface RefineResponse {
  outline: Outline;
  reply: string;
}

export interface DraftResponse {
  draft: string;
}

export interface ApproveResponse {
  approved: boolean;
  section_index: number;
}

// Editor adapter types used by the content script.

export type EditorTier = "rich" | "plain" | "none";

export interface EditorStatus {
  detected: boolean;
  tier: EditorTier;
  element: string | null;
}
