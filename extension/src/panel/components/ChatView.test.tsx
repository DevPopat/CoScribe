import React from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi, describe, it, expect } from "vitest";
import ChatView from "./ChatView";
import type { Outline } from "../../types";

const outline: Outline = {
  title: "How to Bake Bread",
  brief: "A beginner guide.",
  tone_guidance: "Friendly",
  sections: [{ title: "Intro", key_points: ["Why bake?"], sources: [], draft: null, approved: false }],
};

const userMsg = { role: "user" as const, content: "Write about baking." };
const assistantMsg = { role: "assistant" as const, content: "Sure! Who is your audience?" };

describe("ChatView", () => {
  it("shows welcome message when chat history is empty", () => {
    render(<ChatView chatHistory={[]} outline={null} isLoading={false} onSend={() => {}} />);
    expect(screen.getByTestId("welcome-message")).toBeDefined();
  });

  it("does not show welcome message when history exists", () => {
    render(<ChatView chatHistory={[userMsg]} outline={null} isLoading={false} onSend={() => {}} />);
    expect(screen.queryByTestId("welcome-message")).toBeNull();
  });

  it("renders user messages", () => {
    render(<ChatView chatHistory={[userMsg]} outline={null} isLoading={false} onSend={() => {}} />);
    expect(screen.getByText("Write about baking.")).toBeDefined();
  });

  it("renders assistant messages", () => {
    render(<ChatView chatHistory={[assistantMsg]} outline={null} isLoading={false} onSend={() => {}} />);
    expect(screen.getByText("Sure! Who is your audience?")).toBeDefined();
  });

  it("user message bubble has data-role=user", () => {
    render(<ChatView chatHistory={[userMsg]} outline={null} isLoading={false} onSend={() => {}} />);
    expect(screen.getByTestId("message-0").getAttribute("data-role")).toBe("user");
  });

  it("assistant message bubble has data-role=assistant", () => {
    render(<ChatView chatHistory={[assistantMsg]} outline={null} isLoading={false} onSend={() => {}} />);
    expect(screen.getByTestId("message-0").getAttribute("data-role")).toBe("assistant");
  });

  it("shows OutlineCard inline when outline is provided", () => {
    render(<ChatView chatHistory={[assistantMsg]} outline={outline} isLoading={false} onSend={() => {}} />);
    expect(screen.getByTestId("outline-card")).toBeDefined();
  });

  it("does not show OutlineCard when outline is null", () => {
    render(<ChatView chatHistory={[userMsg]} outline={null} isLoading={false} onSend={() => {}} />);
    expect(screen.queryByTestId("outline-card")).toBeNull();
  });

  it("shows LoadingBubble when isLoading is true", () => {
    render(<ChatView chatHistory={[userMsg]} outline={null} isLoading={true} onSend={() => {}} />);
    expect(screen.getByTestId("loading-bubble")).toBeDefined();
  });

  it("does not show LoadingBubble when not loading", () => {
    render(<ChatView chatHistory={[userMsg]} outline={null} isLoading={false} onSend={() => {}} />);
    expect(screen.queryByTestId("loading-bubble")).toBeNull();
  });

  it("calls onSend with input text when send button clicked", async () => {
    const onSend = vi.fn();
    const user = userEvent.setup();
    render(<ChatView chatHistory={[]} outline={null} isLoading={false} onSend={onSend} />);
    await user.type(screen.getByRole("textbox"), "Hello there");
    await user.click(screen.getByRole("button", { name: /send/i }));
    expect(onSend).toHaveBeenCalledWith("Hello there");
  });

  it("clears the input after sending", async () => {
    const user = userEvent.setup();
    render(<ChatView chatHistory={[]} outline={null} isLoading={false} onSend={() => {}} />);
    const input = screen.getByRole("textbox");
    await user.type(input, "Hello");
    await user.click(screen.getByRole("button", { name: /send/i }));
    expect((input as HTMLInputElement).value).toBe("");
  });

  it("send button is disabled when input is empty", () => {
    render(<ChatView chatHistory={[]} outline={null} isLoading={false} onSend={() => {}} />);
    expect(screen.getByRole("button", { name: /send/i })).toHaveProperty("disabled", true);
  });
});
