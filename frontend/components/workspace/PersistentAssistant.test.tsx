import React from "react";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import PersistentAssistant from "./PersistentAssistant";
afterEach(cleanup);
it("publishes exact editor context and opens the shared assistant without generating offline chat", () => {
 const listener=vi.fn(),open=vi.fn();window.addEventListener("geoai:assistant-context",listener);window.addEventListener("geoai:open-site-assistant",open);
 const view=render(<PersistentAssistant projectId={7} selectedIds={["beam"]} revisionId={8} dirty={false}/>);
 expect(listener.mock.calls[0][0].detail).toEqual({project_id:7,selected_ids:["beam"],revision_id:8,dirty:false});
 fireEvent.click(screen.getByRole("button",{name:"Open StruvoCivil Assistant"}));expect(open).toHaveBeenCalledOnce();
 view.rerender(<PersistentAssistant projectId={7} selectedIds={["column"]} revisionId={9} dirty/>);
 expect(listener.mock.calls.at(-1)?.[0].detail.dirty).toBe(true);expect(screen.queryByRole("textbox")).toBeNull();
 window.removeEventListener("geoai:assistant-context",listener);window.removeEventListener("geoai:open-site-assistant",open);
});
