import { cleanup, fireEvent, render } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { useUnsavedChanges } from "./useUnsavedChanges";

function Draft({ dirty }: { dirty: boolean }) {
  useUnsavedChanges(dirty);
  return <a href="/dashboard">Dashboard</a>;
}
afterEach(() => { cleanup(); vi.restoreAllMocks(); });

it("keeps a dirty draft when link navigation is declined and removes guards when clean", () => {
  const confirm = vi.spyOn(window, "confirm").mockReturnValue(false);
  const view = render(<Draft dirty />);
  expect(fireEvent.click(view.getByText("Dashboard"))).toBe(false);
  expect(confirm).toHaveBeenCalledOnce();
  const unload = new Event("beforeunload", { cancelable: true });
  window.dispatchEvent(unload);
  expect(unload.defaultPrevented).toBe(true);
  view.rerender(<Draft dirty={false} />);
  const cleanUnload = new Event("beforeunload", { cancelable: true });
  window.dispatchEvent(cleanUnload);
  expect(cleanUnload.defaultPrevented).toBe(false);
});

it("does not block modified clicks that open another tab", () => {
  const confirm = vi.spyOn(window, "confirm").mockReturnValue(false);
  const view = render(<Draft dirty />);
  fireEvent.click(view.getByText("Dashboard"), { ctrlKey: true });
  expect(confirm).not.toHaveBeenCalled();
});
