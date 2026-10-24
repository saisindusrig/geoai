import React from "react";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import ModernAssistantPanel from "./ModernAssistantPanel";
afterEach(cleanup);
it("opens the one site-wide assistant without invoking model changes",()=>{
 const open=vi.fn(),mutate=vi.fn();window.addEventListener("geoai:open-site-assistant",open);
 render(<ModernAssistantPanel projectId={1} onApplyParameters={mutate} onRegenerate={mutate}/>);
 fireEvent.click(screen.getByRole("button",{name:"Open StruvoCivil Assistant"}));expect(open).toHaveBeenCalledOnce();expect(mutate).not.toHaveBeenCalled();expect(screen.queryByRole("textbox")).toBeNull();
 window.removeEventListener("geoai:open-site-assistant",open);
});
