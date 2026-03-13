import React, { useState } from "react";
import type { CreateSessionParams } from "../../types";

interface TopicFormProps {
  onSubmit: (params: CreateSessionParams) => void;
  isLoading: boolean;
}

export default function TopicForm({ onSubmit, isLoading }: TopicFormProps) {
  const [topic, setTopic] = useState("");
  const [audience, setAudience] = useState("");
  const [notes, setNotes] = useState("");
  const [writingSamples, setWritingSamples] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const samples = writingSamples
      .split("\n---\n")
      .map((s) => s.trim())
      .filter(Boolean);
    onSubmit({
      topic,
      audience,
      notes: notes || undefined,
      writing_samples: samples.length > 0 ? samples : undefined,
    });
  };

  return (
    <form onSubmit={handleSubmit}>
      <label>
        Topic
        <input
          type="text"
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          required
        />
      </label>

      <label>
        Audience
        <input
          type="text"
          value={audience}
          onChange={(e) => setAudience(e.target.value)}
          required
        />
      </label>

      <label>
        Notes
        <textarea
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
        />
      </label>

      <label>
        Writing samples (separate with ---)
        <textarea
          value={writingSamples}
          onChange={(e) => setWritingSamples(e.target.value)}
        />
      </label>

      <button type="submit" disabled={isLoading}>
        {isLoading ? "Planning…" : "Generate Plan"}
      </button>
    </form>
  );
}
