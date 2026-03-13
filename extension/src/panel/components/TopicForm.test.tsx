import React from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi, describe, it, expect } from "vitest";
import TopicForm from "./TopicForm";

describe("TopicForm", () => {
  it("renders all fields and the submit button", () => {
    render(<TopicForm onSubmit={() => {}} isLoading={false} />);

    expect(screen.getByLabelText(/topic/i)).toBeDefined();
    expect(screen.getByLabelText(/audience/i)).toBeDefined();
    expect(screen.getByLabelText(/notes/i)).toBeDefined();
    expect(screen.getByLabelText(/writing samples/i)).toBeDefined();
    expect(screen.getByRole("button", { name: /generate plan/i })).toBeDefined();
  });

  it("calls onSubmit with form values", async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();

    render(<TopicForm onSubmit={onSubmit} isLoading={false} />);

    await user.type(screen.getByLabelText(/topic/i), "Baking bread");
    await user.type(screen.getByLabelText(/audience/i), "Beginners");
    await user.type(screen.getByLabelText(/notes/i), "Focus on sourdough");
    await user.click(screen.getByRole("button", { name: /generate plan/i }));

    expect(onSubmit).toHaveBeenCalledOnce();
    const params = onSubmit.mock.calls[0][0];
    expect(params.topic).toBe("Baking bread");
    expect(params.audience).toBe("Beginners");
    expect(params.notes).toBe("Focus on sourdough");
  });

  it("splits writing samples by --- separator", async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();

    render(<TopicForm onSubmit={onSubmit} isLoading={false} />);

    await user.type(screen.getByLabelText(/topic/i), "Test");
    await user.type(screen.getByLabelText(/audience/i), "All");
    await user.type(
      screen.getByLabelText(/writing samples/i),
      "Sample one\n---\nSample two",
    );
    await user.click(screen.getByRole("button", { name: /generate plan/i }));

    const params = onSubmit.mock.calls[0][0];
    expect(params.writing_samples).toEqual(["Sample one", "Sample two"]);
  });

  it("disables button when isLoading is true", () => {
    render(<TopicForm onSubmit={() => {}} isLoading={true} />);

    const button = screen.getByRole("button");
    expect(button).toHaveProperty("disabled", true);
    expect(button.textContent).toMatch(/planning/i);
  });

  it("omits notes and writing_samples when empty", async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();

    render(<TopicForm onSubmit={onSubmit} isLoading={false} />);

    await user.type(screen.getByLabelText(/topic/i), "Test");
    await user.type(screen.getByLabelText(/audience/i), "All");
    await user.click(screen.getByRole("button", { name: /generate plan/i }));

    const params = onSubmit.mock.calls[0][0];
    expect(params.notes).toBeUndefined();
    expect(params.writing_samples).toBeUndefined();
  });
});
