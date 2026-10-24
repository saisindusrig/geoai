// @vitest-environment jsdom
import {act,renderHook} from "@testing-library/react";
import {expect,it} from "vitest";
import {useHorizontalPanelResize} from "./usePointerResize";
import type {PointerEvent as ReactPointerEvent} from "react";
it("ends resize on focus loss, persists width and removes move handlers on unmount",()=>{
  localStorage.clear();
  const {result,unmount}=renderHook(()=>useHorizontalPanelResize({storageKey:"test-resize",defaultSize:400,minSize:320,maxSize:600}));
  act(()=>result.current.onResizePointerDown({button:0,clientX:900,preventDefault(){}} as ReactPointerEvent));
  act(()=>document.dispatchEvent(new MouseEvent("pointermove",{clientX:800})));
  expect(result.current.size).toBe(500);
  act(()=>window.dispatchEvent(new Event("blur")));
  expect(document.body.style.cursor).toBe("");
  expect(localStorage.getItem("test-resize")).toBe("500");
  act(()=>document.dispatchEvent(new MouseEvent("pointermove",{clientX:700})));
  expect(result.current.size).toBe(500);
  act(()=>result.current.onResizePointerDown({button:0,clientX:900,preventDefault(){}} as ReactPointerEvent));
  unmount();expect(document.body.style.userSelect).toBe("");
});
