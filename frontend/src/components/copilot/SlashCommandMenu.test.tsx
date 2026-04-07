import { createRef } from "react";
import { render, screen, fireEvent, act } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useAssistantStore } from "@/stores/assistant-store";
import { SlashCommandMenu } from "./SlashCommandMenu";
import type { SlashCommandMenuHandle } from "./SlashCommandMenu";

const SKILLS = [
  { name: "manga-workflow", description: "完整工作流", scope: "project" as const, path: "/tmp/a" },
  { name: "generate-script", description: "用 Gemini 生成 JSON 剧本", scope: "project" as const, path: "/tmp/b" },
  { name: "generate-video", description: "用 Veo 生成视频片段", scope: "project" as const, path: "/tmp/c" },
];

describe("SlashCommandMenu", () => {
  const onSelect = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    useAssistantStore.setState({ skills: SKILLS });
  });

  it("renders all skills when filter is empty", () => {
    render(<SlashCommandMenu filter="" onSelect={onSelect} />);
    expect(screen.getAllByText(/manga-workflow/).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/generate-script/).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/generate-video/).length).toBeGreaterThan(0);
  });

  it("filters skills by name", () => {
    render(<SlashCommandMenu filter="script" onSelect={onSelect} />);
    expect(screen.getAllByText(/generate-script/).length).toBeGreaterThan(0);
    expect(screen.queryAllByText(/manga-workflow/).length).toBe(0);
  });

  it("filters skills by translated label", () => {
    // The mock t() returns keys like "skillFallback.generate-script" as labels.
    // The component lowercases the filter query, then checks label.includes(query) (case-sensitive).
    // "allback.generate-script" is a case-correctly-matching substring of the label.
    render(<SlashCommandMenu filter="allback.generate-script" onSelect={onSelect} />);
    expect(screen.getAllByText(/generate-script/).length).toBeGreaterThan(0);
    expect(screen.queryAllByText(/manga-workflow/).length).toBe(0);
  });

  it("returns null when no skills match", () => {
    const { container } = render(<SlashCommandMenu filter="nonexistent" onSelect={onSelect} />);
    expect(container.firstChild).toBeNull();
  });

  it("calls onSelect with command on mousedown", () => {
    render(<SlashCommandMenu filter="" onSelect={onSelect} />);
    fireEvent.mouseDown(screen.getAllByText(/manga-workflow/)[0].closest("button")!);
    expect(onSelect).toHaveBeenCalledWith("/manga-workflow");
  });

  it("displays translated labels for known skills", () => {
    render(<SlashCommandMenu filter="" onSelect={onSelect} />);
    expect(screen.getByText(/skillFallback\.manga-workflow/)).toBeInTheDocument();
    expect(screen.getByText(/skillFallback\.generate-script/)).toBeInTheDocument();
    expect(screen.getByText(/skillFallback\.generate-video/)).toBeInTheDocument();
  });

  it("shows distinct icons per skill", () => {
    const { container } = render(<SlashCommandMenu filter="" onSelect={onSelect} />);
    const buttons = container.querySelectorAll("button");
    for (const btn of buttons) {
      expect(btn.querySelector("svg")).toBeTruthy();
    }
  });

  describe("keyboard navigation via imperative handle", () => {
    it("navigates down and selects with Enter", () => {
      const ref = createRef<SlashCommandMenuHandle>();
      render(<SlashCommandMenu ref={ref} filter="" onSelect={onSelect} />);

      // Initially first item is active
      const firstOption = screen.getAllByText(/manga-workflow/)[0].closest("button")!;
      expect(firstOption).toHaveAttribute("aria-selected", "true");

      // Arrow down → second item
      act(() => { ref.current!.handleKeyDown("ArrowDown"); });
      const secondOption = screen.getAllByText(/generate-script/)[0].closest("button")!;
      expect(secondOption).toHaveAttribute("aria-selected", "true");
      expect(firstOption).toHaveAttribute("aria-selected", "false");

      // Enter → select second item
      act(() => { ref.current!.handleKeyDown("Enter"); });
      expect(onSelect).toHaveBeenCalledWith("/generate-script");
    });

    it("wraps around when navigating past boundaries", () => {
      const ref = createRef<SlashCommandMenuHandle>();
      render(<SlashCommandMenu ref={ref} filter="" onSelect={onSelect} />);

      // ArrowUp from first → wraps to last
      act(() => { ref.current!.handleKeyDown("ArrowUp"); });
      const lastOption = screen.getAllByText(/generate-video/)[0].closest("button")!;
      expect(lastOption).toHaveAttribute("aria-selected", "true");
    });

    it("exposes activeDescendantId", () => {
      const ref = createRef<SlashCommandMenuHandle>();
      render(<SlashCommandMenu ref={ref} filter="" onSelect={onSelect} />);

      expect(ref.current!.activeDescendantId).toBe("slash-command-menu-option-0");
      act(() => { ref.current!.handleKeyDown("ArrowDown"); });
      expect(ref.current!.activeDescendantId).toBe("slash-command-menu-option-1");
    });
  });
});
