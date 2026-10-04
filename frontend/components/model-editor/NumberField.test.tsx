import { render, screen, cleanup } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { NumberField } from "./ProfessionalModelEditor";

afterEach(cleanup);
describe("precision numeric confirmation", () => {
  it("commits once on Enter, never on keystrokes", async () => {
    const commit = vi.fn(); const user = userEvent.setup();
    render(<NumberField label="East m" value={12.5} onChange={commit}/>);
    const input = screen.getByLabelText("East m");
    await user.clear(input); await user.type(input,"15.125"); expect(commit).not.toHaveBeenCalled();
    await user.keyboard("{Enter}"); expect(commit).toHaveBeenCalledExactlyOnceWith(15.125);
  });
  it("shows an inline error without clamping and Escape restores the original value", async () => {
    const commit = vi.fn(); const user = userEvent.setup();
    render(<NumberField label="Scale X" value={1} positive onChange={commit}/>);
    const input = screen.getByLabelText("Scale X"); await user.clear(input); await user.type(input,"-2"); await user.tab();
    expect(screen.getByRole("alert")).toHaveTextContent("greater than zero"); expect(commit).not.toHaveBeenCalled(); expect(input).toHaveValue("-2");
    await user.click(input); await user.keyboard("{Escape}"); expect(input).toHaveValue("1");
  });
});
