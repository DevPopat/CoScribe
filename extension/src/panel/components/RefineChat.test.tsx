import React from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi, describe, it, expect } from "vitest";
import RefineChat from "./RefineChat";

describe("RefineChat", () => {
  it("renders chat history messages", () => {
    const history = [
      { role: "user" as const, content: "Add a sourdough section" },
      { role: "assistant" as const, content: "Done, added sourdough starter section." },
    ];
    render(<RefineChat history={history} isRefining={false} onSend={() => {}} />);
    expect(screen.getByTestId("refine-msg-0").textContent).toContain("Add a sourdough section");
    expect(screen.getByTestId("refine-msg-1").textContent).toContain("Done, added sourdough");
  });

  it("shows loading indicator when refining", () => {
    render(<RefineChat history={[]} isRefining={true} onSend={() => {}} />);
    expect(screen.getByTestId("refine-loading")).toBeDefined();
  });

  it("calls onSend with trimmed input on submit", async () => {
    const onSend = vi.fn();
    const user = userEvent.setup();
    render(<RefineChat history={[]} isRefining={false} onSend={onSend} />);

    await user.type(screen.getByLabelText(/refinement message/i), "  Add more detail  ");
    await user.click(screen.getByRole("button", { name: /send/i }));

    expect(onSend).toHaveBeenCalledWith("Add more detail");
  });

  it("clears input after sending", async () => {
    const user = userEvent.setup();
    render(<RefineChat history={[]} isRefining={false} onSend={() => {}} />);

    const input = screen.getByLabelText(/refinement message/i) as HTMLInputElement;
    await user.type(input, "Hello");
    await user.click(screen.getByRole("button", { name: /send/i }));

    expect(input.value).toBe("");
  });

  it("disables input and button when refining", () => {
    render(<RefineChat history={[]} isRefining={true} onSend={() => {}} />);
    const input = screen.getByLabelText(/refinement message/i) as HTMLInputElement;
    expect(input.disabled).toBe(true);
    expect(screen.getByRole("button", { name: /send/i })).toHaveProperty("disabled", true);
  });

  it("disables send button when input is empty", () => {
    render(<RefineChat history={[]} isRefining={false} onSend={() => {}} />);
    expect(screen.getByRole("button", { name: /send/i })).toHaveProperty("disabled", true);
  });
});
