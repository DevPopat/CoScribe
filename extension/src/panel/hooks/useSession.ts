// React hook managing the full writing session lifecycle.

import { useCallback, useState } from "react";
import type {
  CreateSessionParams,
  Outline,
  WritingSession,
} from "../../types";
import api from "./useAPI";

export interface UseSessionReturn {
  session: WritingSession | null;
  outline: Outline | null;
  currentSectionIndex: number;
  isLoading: boolean;
  error: string | null;
  startSession: (params: CreateSessionParams) => Promise<void>;
  draftSection: (index: number) => Promise<void>;
  approveSection: (index: number, text?: string) => Promise<void>;
}

export default function useSession(): UseSessionReturn {
  const [session, setSession] = useState<WritingSession | null>(null);
  const [outline, setOutline] = useState<Outline | null>(null);
  const [currentSectionIndex, setCurrentSectionIndex] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

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

  return {
    session,
    outline,
    currentSectionIndex,
    isLoading,
    error,
    startSession,
    draftSection,
    approveSection,
  };
}
