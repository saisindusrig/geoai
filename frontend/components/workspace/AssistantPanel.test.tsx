import React from "react";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import AssistantPanel from "./AssistantPanel";
import { api } from "@/lib/api";

vi.mock("@/lib/api", () => ({ api: { post: vi.fn() }, apiUrl: (s: string) => s }));
afterEach(() => { cleanup(); vi.clearAllMocks(); });

it.each([null, { type: "update_parameters", parameters: { floors: 5 } }, { type: "regenerate" }, { type: "delete_objects" }])(
  "never invokes a model writer for assistant response %j", async (action) => {
    vi.mocked(api.post).mockResolvedValue({ reply: "Here is the explanation", action });
    const onApplyParameters = vi.fn(), onRegenerate = vi.fn();
    render(<AssistantPanel projectId={1} onApplyParameters={onApplyParameters} onRegenerate={onRegenerate} />);
    fireEvent.change(screen.getByRole("textbox"), { target: { value: "Explain or change the selected asset" } });
    fireEvent.click(screen.getByRole("button", { name: "Send" }));
    await screen.findByText("Here is the explanation");
    expect(onApplyParameters).not.toHaveBeenCalled();
    expect(onRegenerate).not.toHaveBeenCalled();
    if (action) expect(screen.getByText(/no model changes were applied/i)).toBeInTheDocument();
  },
);
