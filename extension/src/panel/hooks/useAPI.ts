// Typed HTTP client for the CoScribe backend API.

import type {
  ApproveResponse,
  ChatResponse,
  CreateSessionParams,
  DraftResponse,
  Outline,
  RefineResponse,
  SectionRefineResponse,
  WritingSession,
} from "../../types";

const BASE_URL = "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`API ${res.status}: ${body}`);
  }
  return res.json() as Promise<T>;
}

function post<T>(path: string, body?: unknown): Promise<T> {
  return request<T>(path, {
    method: "POST",
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
}

function get<T>(path: string): Promise<T> {
  return request<T>(path);
}

const api = {
  createSession(params: CreateSessionParams): Promise<WritingSession> {
    return post("/sessions", params);
  },

  getSession(id: string): Promise<WritingSession> {
    return get(`/sessions/${id}`);
  },

  generatePlan(sessionId: string): Promise<Outline> {
    return post(`/sessions/${sessionId}/plan`);
  },

  refinePlan(sessionId: string, message: string): Promise<RefineResponse> {
    return post(`/sessions/${sessionId}/plan/refine`, { message });
  },

  draftSection(sessionId: string, sectionIndex: number): Promise<DraftResponse> {
    return post(`/sessions/${sessionId}/sections/${sectionIndex}/draft`);
  },

  approveSection(
    sessionId: string,
    sectionIndex: number,
    text?: string,
  ): Promise<ApproveResponse> {
    return post(`/sessions/${sessionId}/sections/${sectionIndex}/approve`, {
      text: text ?? null,
    });
  },

  chatIntake(
    messages: { role: "user" | "assistant"; content: string }[],
  ): Promise<ChatResponse> {
    return post("/sessions/chat", { messages });
  },

  refineSectionDraft(
    sessionId: string,
    sectionIndex: number,
    message: string,
    currentDraft: string,
  ): Promise<SectionRefineResponse> {
    return post(`/sessions/${sessionId}/sections/${sectionIndex}/refine`, {
      message,
      current_draft: currentDraft,
    });
  },
};

export default api;
