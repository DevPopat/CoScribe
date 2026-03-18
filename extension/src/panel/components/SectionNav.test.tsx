import React from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi, describe, it, expect } from "vitest";
import SectionNav from "./SectionNav";
import type { Section } from "../../types";

const noDraft: Section = { title: "Introduction", key_points: [], sources: [], draft: null, approved: false };
const drafted: Section = { title: "The Process", key_points: [], sources: [], draft: "Draft text.", approved: false };
const approved: Section = { title: "Conclusion", key_points: [], sources: [], draft: "Approved text.", approved: true };

const sections = [noDraft, drafted, approved];

describe("SectionNav", () => {
  it("renders a pill for every section", () => {
    render(<SectionNav sections={sections} currentIndex={0} onSelect={() => {}} />);
    expect(screen.getAllByRole("button")).toHaveLength(3);
  });

  it("displays section titles", () => {
    render(<SectionNav sections={sections} currentIndex={0} onSelect={() => {}} />);
    expect(screen.getByText("Introduction")).toBeDefined();
    expect(screen.getByText("The Process")).toBeDefined();
    expect(screen.getByText("Conclusion")).toBeDefined();
  });

  it("calls onSelect with the correct index when a pill is clicked", async () => {
    const onSelect = vi.fn();
    const user = userEvent.setup();
    render(<SectionNav sections={sections} currentIndex={0} onSelect={onSelect} />);
    await user.click(screen.getByText("The Process"));
    expect(onSelect).toHaveBeenCalledWith(1);
  });

  it("marks the active pill with aria-current", () => {
    render(<SectionNav sections={sections} currentIndex={1} onSelect={() => {}} />);
    const pills = screen.getAllByRole("button");
    expect(pills[0].getAttribute("aria-current")).toBeNull();
    expect(pills[1].getAttribute("aria-current")).toBe("true");
    expect(pills[2].getAttribute("aria-current")).toBeNull();
  });

  it("shows empty-circle status for sections with no draft", () => {
    render(<SectionNav sections={sections} currentIndex={0} onSelect={() => {}} />);
    const status = screen.getByTestId("section-status-0");
    expect(status.getAttribute("data-status")).toBe("empty");
  });

  it("shows drafted status for sections with a draft but not approved", () => {
    render(<SectionNav sections={sections} currentIndex={0} onSelect={() => {}} />);
    const status = screen.getByTestId("section-status-1");
    expect(status.getAttribute("data-status")).toBe("drafted");
  });

  it("shows approved status for approved sections", () => {
    render(<SectionNav sections={sections} currentIndex={0} onSelect={() => {}} />);
    const status = screen.getByTestId("section-status-2");
    expect(status.getAttribute("data-status")).toBe("approved");
  });

  it("renders a single section without error", () => {
    render(<SectionNav sections={[noDraft]} currentIndex={0} onSelect={() => {}} />);
    expect(screen.getAllByRole("button")).toHaveLength(1);
  });
});
