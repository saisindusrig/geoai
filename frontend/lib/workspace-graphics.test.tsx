import { afterEach, expect, it, vi } from "vitest";
import { bindWorkspaceGraphics, graphicsSettings, type GraphicsQuality } from "./workspace-graphics";
afterEach(()=>vi.unstubAllGlobals());
it("bounds visual resolution without a device identifier or geometry input",()=>{
 expect(graphicsSettings("balanced",1280,900)).toEqual({scale:1,shadows:false,fxaa:false});
 expect(graphicsSettings("performance",1280,900).scale).toBe(.65);
 expect(graphicsSettings("high",1280,900)).toEqual({scale:1.25,shadows:true,fxaa:true});
 expect(graphicsSettings("auto",1280,900).scale).toBe(1);
 expect(graphicsSettings("auto",10000,10000).scale).toBe(.65);
 expect(graphicsSettings("auto",0,0).scale).toBe(1);
});
it("redraws quality and resize changes, recovers context and cleans subscriptions",()=>{
 let resize:()=>void=()=>{};const disconnect=vi.fn();
 vi.stubGlobal("ResizeObserver",class {constructor(cb:()=>void){resize=cb}observe(){}disconnect=disconnect});
 const canvas=document.createElement("canvas");Object.defineProperty(canvas,"clientWidth",{value:1280,configurable:true});Object.defineProperty(canvas,"clientHeight",{value:900});
 const viewer={canvas,resolutionScale:1,useBrowserRecommendedResolution:false,shadows:false,useDefaultRenderLoop:true,resize:vi.fn(),isDestroyed:()=>false,scene:{requestRenderMode:false,maximumRenderTimeChange:0,requestRender:vi.fn(),postProcessStages:{fxaa:{enabled:false}}}};
 let quality:GraphicsQuality="auto";const context=vi.fn(),restored=vi.fn();
 const binding=bindWorkspaceGraphics(viewer,()=>quality,context,restored);
 expect(viewer.scene.requestRenderMode).toBe(true);expect(viewer.scene.maximumRenderTimeChange).toBe(Infinity);
 quality="performance";binding.update();expect(viewer.resolutionScale).toBe(.65);
 quality="high";window.dispatchEvent(new Event("orientationchange"));expect(viewer.shadows).toBe(true);expect(viewer.scene.postProcessStages.fxaa.enabled).toBe(true);
 resize();expect(viewer.resize).toHaveBeenCalled();
 const lost=new Event("webglcontextlost",{cancelable:true});canvas.dispatchEvent(lost);
 expect(lost.defaultPrevented).toBe(true);expect(viewer.useDefaultRenderLoop).toBe(false);expect(context).toHaveBeenLastCalledWith("lost");
 const calls=viewer.resize.mock.calls.length;binding.update();expect(viewer.resize).toHaveBeenCalledTimes(calls);
 canvas.dispatchEvent(new Event("webglcontextrestored"));expect(restored).toHaveBeenCalledTimes(1);
 binding.dispose();canvas.dispatchEvent(new Event("webglcontextrestored"));window.dispatchEvent(new Event("resize"));
 expect(restored).toHaveBeenCalledTimes(1);expect(disconnect).toHaveBeenCalledTimes(1);expect(viewer.resize).toHaveBeenCalledTimes(calls);
});
