import { act, cleanup, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
vi.mock("next/dynamic", () => ({ default: () => function Scene() { return <canvas data-testid="preview-renderer" />; } }));
import ConstructionPreview from "./ConstructionPreview";
afterEach(() => { cleanup(); vi.unstubAllGlobals(); });
it("releases a decorative gallery renderer when the card leaves view", () => {
  let notify!: IntersectionObserverCallback;
  const disconnect = vi.fn();
  vi.stubGlobal("IntersectionObserver", class { constructor(callback: IntersectionObserverCallback) { notify = callback; } observe() {} disconnect = disconnect; });
  const view = render(<ConstructionPreview type="building" />);
  act(() => notify([{ isIntersecting: true }] as IntersectionObserverEntry[], {} as IntersectionObserver));
  expect(screen.getByTestId("preview-renderer")).toBeInTheDocument();
  act(() => notify([{ isIntersecting: false }] as IntersectionObserverEntry[], {} as IntersectionObserver));
  expect(screen.queryByTestId("preview-renderer")).not.toBeInTheDocument();
  view.unmount();
  expect(disconnect).toHaveBeenCalledOnce();
});
