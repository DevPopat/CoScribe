// React hook managing the full writing session lifecycle.
// Handles intake chat, outline planning, section drafting/refining, and approval.
// State is persisted to chrome.storage.local (or localStorage fallback) via useLocalStorage.

import { useCallback, useEffect, useState } from "react";
import type {
  CreateSessionParams,
  Outline,
  WritingSession,
} from "../../types";
import api from "./useAPI";
import useLocalStorage from "./useLocalStorage";

export interface RefinementMessage {
  role: "user" | "assistant";
  content: string;
}

type Message = RefinementMessage;
type CurrentView = "chat" | "draft";

export interface UseSessionReturn {
  // Core session state
  session: WritingSession | null;
  outline: Outline | null;
  currentSectionIndex: number;
  currentView: CurrentView;
  isLoading: boolean;
  error: string | null;
  // Chat state
  chatHistory: Message[];
  sectionChats: Record<number, Message[]>;
  // Outline refinement state
  refinementHistory: RefinementMessage[];
  isRefining: boolean;
  outlineChanged: boolean;
  // Actions
  sendChatMessage: (message: string) => Promise<void>;
  startSession: (params: CreateSessionParams) => Promise<void>;
  draftSection: (index: number) => Promise<void>;
  approveSection: (index: number, text?: string) => Promise<void>;
  refineOutline: (message: string) => Promise<void>;
  refineSectionDraft: (sectionIndex: number, message: string) => Promise<void>;
  clearOutlineChanged: () => void;
}

export default function useSession(): UseSessionReturn {
  const storage = useLocalStorage();

  const [session, setSession] = useState<WritingSession | null>(null);
  const [outline, setOutline] = useState<Outline | null>(null);
  const [currentSectionIndex, setCurrentSectionIndex] = useState(0);
  const [currentView, setCurrentView] = useState<CurrentView>("chat");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [chatHistory, setChatHistory] = useState<Message[]>([]);
  const [sectionChats, setSectionChats] = useState<Record<number, Message[]>>({});
  const [refinementHistory, setRefinementHistory] = useState<RefinementMessage[]>([]);
  const [isRefining, setIsRefining] = useState(false);
  const [outlineChanged, setOutlineChanged] = useState(false);

  // Restore persisted state on mount
  useEffect(() => {
    const saved = storage.load();
    if (!saved) return;
    if (saved.session_id) setSession((s) => s ?? ({ id: saved.session_id } as WritingSession));
    if (saved.outline) setOutline(saved.outline);
    if (saved.chat_history) setChatHistory(saved.chat_history);
    if (saved.section_chats) setSectionChats(saved.section_chats);
    if (saved.current_section != null) setCurrentSectionIndex(saved.current_section);
    if (saved.current_view) setCurrentView(saved.current_view as CurrentView);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Persist state whenever key fields change
  useEffect(() => {
    storage.save({
      session_id: session?.id ?? null,
      chat_history: chatHistory,
      outline,
      section_chats: sectionChats,
      section_drafts: Object.fromEntries(
        (outline?.sections ?? [])
          .map((s, i) => [i, s.draft ?? ""])
          .filter(([, d]) => d !== ""),
      ),
      current_view: currentView,
      current_section: currentSectionIndex,
    });
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [session, outline, chatHistory, sectionChats, currentView, currentSectionIndex]);

  // -- Intake chat ---------------------------------------------------------------

  const sendChatMessage = useCallback(
    async (message: string) => {
      setIsLoading(true);
      setError(null);
      const userMsg: Message = { role: "user", content: message };
      const updatedHistory = [...chatHistory, userMsg];
      setChatHistory(updatedHistory);
      try {
        const response = await api.chatIntake(updatedHistory);
        const assistantMsg: Message = { role: "assistant", content: response.reply };
        setChatHistory((prev) => [...prev, assistantMsg]);

        if (response.ready && response.extracted) {
          const { topic, audience, notes, writing_samples, reference_urls } = response.extracted;
          const created = await api.createSession({
            topic,
            audience,
            notes,
            writing_samples,
            reference_urls,
          });
          setSession(created);
          const plan = await api.generatePlan(created.id);
          setOutline(plan);
          setSession((prev) =>
            prev ? { ...prev, status: "outline_ready", outline: plan } : prev,
          );
          setCurrentSectionIndex(0);
          setCurrentView("draft");
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : String(err));
      } finally {
        setIsLoading(false);
      }
    },
    [chatHistory],
  );

  // -- Legacy direct-start (kept for compatibility) ------------------------------

  const startSession = useCallback(async (params: CreateSessionParams) => {
    setIsLoading(true);
    setError(null);
    try {
      const created = await api.createSession(params);
      setSession(created);
      const plan = await api.generatePlan(created.id);
      setOutline(plan);
      setSession((prev) =>
        prev ? { ...prev, status: "outline_ready", outline: plan } : prev,
      );
      setCurrentSectionIndex(0);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setIsLoading(false);
    }
  }, []);

  // -- Section drafting ----------------------------------------------------------

  const draftSection = useCallback(
    async (index: number) => {
      if (!session) return;
      setIsLoading(true);
      setError(null);
      try {
        const { draft } = await api.draftSection(session.id, index);
        setOutline((prev) => {
          if (!prev) return prev;
          const sections = prev.sections.map((s, i) =>
            i === index ? { ...s, draft } : s,
          );
          return { ...prev, sections };
        });
        setSession((prev) =>
          prev && prev.status === "outline_ready"
            ? { ...prev, status: "drafting" }
            : prev,
        );
        setCurrentSectionIndex(index);
      } catch (err) {
        setError(err instanceof Error ? err.message : String(err));
      } finally {
        setIsLoading(false);
      }
    },
    [session],
  );

  // -- Section draft refinement --------------------------------------------------

  const refineSectionDraft = useCallback(
    async (sectionIndex: number, message: string) => {
      if (!session) return;
      setIsLoading(true);
      setError(null);
      const userMsg: Message = { role: "user", content: message };
      setSectionChats((prev) => ({
        ...prev,
        [sectionIndex]: [...(prev[sectionIndex] ?? []), userMsg],
      }));
      try {
        const currentDraft = outline?.sections[sectionIndex]?.draft ?? "";
        const response = await api.refineSectionDraft(
          session.id,
          sectionIndex,
          message,
          currentDraft,
        );
        setOutline((prev) => {
          if (!prev) return prev;
          const sections = prev.sections.map((s, i) => {
            if (i !== sectionIndex) return s;
            return {
              ...s,
              draft: response.draft,
              key_points: response.key_points ?? s.key_points,
              sources: response.sources ?? s.sources,
            };
          });
          return { ...prev, sections };
        });
        const assistantMsg: Message = { role: "assistant", content: response.reply };
        setSectionChats((prev) => ({
          ...prev,
          [sectionIndex]: [...(prev[sectionIndex] ?? []), assistantMsg],
        }));
      } catch (err) {
        setError(err instanceof Error ? err.message : String(err));
      } finally {
        setIsLoading(false);
      }
    },
    [session, outline],
  );

  // -- Section approval ----------------------------------------------------------

  const approveSection = useCallback(
    async (index: number, text?: string) => {
      if (!session) return;
      setIsLoading(true);
      setError(null);
      try {
        await api.approveSection(session.id, index, text);
        setOutline((prev) => {
          if (!prev) return prev;
          const sections = prev.sections.map((s, i) =>
            i === index ? { ...s, approved: true, draft: text ?? s.draft } : s,
          );
          const allApproved = sections.every((s) => s.approved);
          if (allApproved) {
            setSession((p) => (p ? { ...p, status: "complete" } : p));
          }
          return { ...prev, sections };
        });
      } catch (err) {
        setError(err instanceof Error ? err.message : String(err));
      } finally {
        setIsLoading(false);
      }
    },
    [session],
  );

  // -- Outline refinement --------------------------------------------------------

  const refineOutline = useCallback(
    async (message: string) => {
      if (!session) return;
      setIsRefining(true);
      setError(null);
      setRefinementHistory((prev) => [...prev, { role: "user", content: message }]);
      try {
        const { outline: updated, reply } = await api.refinePlan(session.id, message);
        setOutline(updated);
        setRefinementHistory((prev) => [...prev, { role: "assistant", content: reply }]);
        setOutlineChanged(true);
      } catch (err) {
        setError(err instanceof Error ? err.message : String(err));
      } finally {
        setIsRefining(false);
      }
    },
    [session],
  );

  const clearOutlineChanged = useCallback(() => {
    setOutlineChanged(false);
  }, []);

  return {
    session,
    outline,
    currentSectionIndex,
    currentView,
    isLoading,
    error,
    chatHistory,
    sectionChats,
    refinementHistory,
    isRefining,
    outlineChanged,
    sendChatMessage,
    startSession,
    draftSection,
    approveSection,
    refineOutline,
    refineSectionDraft,
    clearOutlineChanged,
  };
}
