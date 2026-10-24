import React from "react";
import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import SiteAssistant from "./SiteAssistant";
import { api } from "@/lib/api";
import { AssistantRequestError, sendAssistant, type AssistantEvent, type AssistantTask } from "@/lib/site-assistant";
const push = vi.fn();
vi.mock("next/navigation", () => ({usePathname:()=>"/projects/1/workspace",useRouter:()=>({push})}));
vi.mock("@/lib/api",()=>({api:{get:vi.fn(),post:vi.fn()}}));
vi.mock("@/lib/site-assistant",async original=>({...await original<typeof import("@/lib/site-assistant")>(),sendAssistant:vi.fn()}));
const request={project_id:1,revision_id:8,selected_ids:["beam"],dirty:false,message:"Explain saved results",model:"zai-org/GLM-5.3-Flash",page:"/projects/1/workspace"};
const task:AssistantTask={id:"old",request,status:"SUCCEEDED",reply:"Open **Analyze / Results**.\n\n- Read saved evidence.\n- Check [diagnostics](/diagnostics).",events:[],model:request.model};
beforeEach(()=>{vi.mocked(api.get).mockImplementation(async p=>p.includes("status")?{enabled:true,state:"AVAILABLE",message:"Ready",requestAllowance:3}:p.includes("/api/projects/")?{name:"Test project"}:{tasks:[]});});
afterEach(()=>{cleanup();vi.resetAllMocks();});
async function open(){render(<SiteAssistant/>);fireEvent.click(screen.getByRole("button",{name:"StruvoCivil Assistant"}));await waitFor(()=>expect(api.get).toHaveBeenCalled());}
function submit(message="Explain this beam"){fireEvent.change(screen.getByRole("textbox"),{target:{value:message}});fireEvent.click(screen.getByRole("button",{name:"Send"}));}
function details(){fireEvent.click(screen.getByText("Details",{exact:true}));}
it("keeps configuration collapsed and never fabricates a response or sends on open",async()=>{await open();expect(sendAssistant).not.toHaveBeenCalled();expect(screen.getByText("Details").closest("details")).not.toHaveAttribute("open");expect(screen.getByLabelText("Assistant task history").querySelectorAll("article")).toHaveLength(0);expect(screen.getByLabelText("Assistant model")).toHaveValue(request.model);});
it("renders retained history as separate Markdown messages with safe links",async()=>{vi.mocked(api.get).mockImplementation(async p=>p.includes("status")?{enabled:true,state:"AVAILABLE",message:"Ready"}:{tasks:[task]});await open();await screen.findByText("Analyze / Results");expect(screen.getByText("Analyze / Results").tagName).toBe("STRONG");expect(screen.getByRole("link",{name:"diagnostics"})).toHaveAttribute("href","/diagnostics");expect(screen.getByText("You")).toBeVisible();expect(screen.getAllByText("StruvoCivil Assistant",{exact:true})[1]).toBeVisible();expect(sendAssistant).not.toHaveBeenCalled();});
it("uses frozen context and manual model choice; transport retry never replays silently",async()=>{await open();details();act(()=>window.dispatchEvent(new CustomEvent("geoai:assistant-context",{detail:request})));fireEvent.change(screen.getByLabelText("Assistant model"),{target:{value:"zai-org/GLM-5.3"}});vi.mocked(sendAssistant).mockRejectedValue(new Error("Nebius timed out"));submit();await screen.findByRole("alert");expect(sendAssistant).toHaveBeenCalledOnce();expect(vi.mocked(sendAssistant).mock.calls[0][0]).toMatchObject({project_id:1,revision_id:8,selected_ids:["beam"],model:"zai-org/GLM-5.3"});fireEvent.click(screen.getByRole("button",{name:"Retry"}));await waitFor(()=>expect(sendAssistant).toHaveBeenCalledTimes(2));expect(vi.mocked(sendAssistant).mock.calls[1][0]).toEqual(vi.mocked(sendAssistant).mock.calls[0][0]);});
it("derives Thinking, project checks and action preparation from actual stream events",async()=>{await open();let emit!:(e:AssistantEvent)=>void;let finish!:()=>void;vi.mocked(sendAssistant).mockImplementation((_b,e)=>new Promise<void>(r=>{emit=e;finish=r;}));submit();expect(screen.getByLabelText("Task status")).toHaveTextContent("Thinking");act(()=>emit({type:"tool_start",name:"read_context"}));expect(screen.getByLabelText("Task status")).toHaveTextContent("Checking your project");act(()=>emit({type:"plan",steps:["Read evidence"]}));expect(screen.getByLabelText("Task status")).toHaveTextContent("Preparing an action");act(()=>{emit({type:"delta",text:"A **streamed answer**"});emit({type:"task",task:{...task,id:"new",reply:"A **streamed answer**",events:[{type:"delta",text:"A **streamed answer**"}]}});finish();});await screen.findByText("streamed answer");await waitFor(()=>expect(screen.getByLabelText("Task status")).toHaveTextContent("Completed"));expect(screen.queryByText("A **streamed answer**")).toBeNull();});
it("keeps native read operations simple and navigation allowlisted",async()=>{await open();vi.mocked(sendAssistant).mockImplementation(async(_b,emit)=>{emit({type:"tool_result",name:"read_context",ok:true,result:{kind:"context"}});emit({type:"tool_result",name:"navigate",ok:true,result:{kind:"navigation",href:"https://evil.test",destination:"outside"}});});submit();await screen.findByText("Checked saved project evidence");fireEvent.click(screen.getByRole("button",{name:"Open outside"}));expect(push).not.toHaveBeenCalled();expect(screen.getByText(/Navigation rejected/)).toBeVisible();expect(api.post).not.toHaveBeenCalled();});
it("confirms accessible project identity when opening an existing tool",async()=>{await open();vi.mocked(sendAssistant).mockImplementation(async(_b,emit)=>emit({type:"tool_result",name:"navigate",ok:true,result:{kind:"navigation",href:"/projects/1/workspace",destination:"results",projectId:1}}));submit();fireEvent.click(await screen.findByRole("button",{name:"Open results"}));await screen.findByText(/Opening Test project/);act(()=>window.dispatchEvent(new CustomEvent("geoai:inspector-view",{detail:"analysis"})));await screen.findByText(/Opened Test project/);expect(api.get).toHaveBeenCalledWith("/api/projects/1");expect(api.post).not.toHaveBeenCalled();});
it("requires explicit Preview, rejects dirty state, and supports nonmutating Cancel",async()=>{await open();const preview=vi.fn(),cancel=vi.fn();window.addEventListener("geoai:assistant-position-preview",preview);window.addEventListener("geoai:assistant-preview-cancel",cancel);act(()=>window.dispatchEvent(new CustomEvent("geoai:assistant-context",{detail:request})));vi.mocked(sendAssistant).mockImplementation(async(_b,emit)=>emit({type:"tool_result",name:"prepare_position_preview",ok:true,result:{kind:"position_preview",projectId:1,revisionId:8,componentId:"beam",before:[0,0,0],after:[1,0,0]}}));submit();const button=await screen.findByRole("button",{name:"Preview"});await waitFor(()=>expect(button).toBeEnabled());expect(preview).not.toHaveBeenCalled();fireEvent.click(button);expect(preview).toHaveBeenCalledOnce();act(()=>window.dispatchEvent(new CustomEvent("geoai:assistant-context",{detail:{...request,dirty:true}})));await waitFor(()=>expect(button).toBeDisabled());fireEvent.click(screen.getByRole("button",{name:"Cancel preview"}));expect(cancel).toHaveBeenCalledOnce();expect(api.post).not.toHaveBeenCalled();window.removeEventListener("geoai:assistant-position-preview",preview);window.removeEventListener("geoai:assistant-preview-cancel",cancel);});
it("distinguishes approved test-turn quota from tokens or money and does not retry",async()=>{await open();vi.mocked(sendAssistant).mockRejectedValue(new AssistantRequestError("daily request limit", "DAILY_REQUEST_LIMIT","RATE_LIMITED"));submit();await screen.findAllByText(/approved live test has used all 3 turns/);expect(screen.getByLabelText("Task status")).toHaveTextContent("Usage limit reached");expect(sendAssistant).toHaveBeenCalledOnce();expect(screen.queryByRole("button",{name:"Retry"})).toBeNull();});
it("stops a response, retains the draft, and never sends another request automatically",async()=>{await open();vi.mocked(sendAssistant).mockImplementation((_b,_e,signal)=>new Promise((_r,reject)=>signal.addEventListener("abort",()=>reject(new DOMException("Stopped","AbortError")),{once:true})));submit("Explain context");fireEvent.click(await screen.findByRole("button",{name:"Stop response"}));await screen.findByText(/Usage may be unknown/);expect(sendAssistant).toHaveBeenCalledOnce();expect(screen.getByRole("textbox")).toHaveValue("Explain context");});
it("supports keyboard resizing without covering the entire workspace",async()=>{await open();const separator=screen.getByRole("separator",{name:"Resize assistant"});expect(separator).toHaveAttribute("tabindex","0");fireEvent.keyDown(separator,{key:"ArrowLeft"});expect(separator).toHaveAttribute("aria-valuenow","504");fireEvent.click(screen.getByRole("button",{name:"Compact assistant"}));expect(separator).toHaveAttribute("aria-valuenow","480");});
it("cancelling an older preview does not hide a later proposal for the same component",async()=>{
 const event:AssistantEvent={type:'tool_result',name:'prepare_position_preview',ok:true,result:{kind:'position_preview',projectId:1,revisionId:8,componentId:'beam',before:[0,0,0],after:[1,0,0]}};
 vi.mocked(api.get).mockImplementation(async p=>p.includes('status')?{enabled:true,state:'AVAILABLE',message:'Ready'}:{tasks:[{...task,id:'first',events:[event]},{...task,id:'second',events:[event]}]});
 await open();act(()=>window.dispatchEvent(new CustomEvent('geoai:assistant-context',{detail:request})));
 await waitFor(()=>expect(screen.getAllByRole('button',{name:'Preview'})).toHaveLength(2));
 fireEvent.click(screen.getAllByRole('button',{name:'Cancel preview'})[0]);
 expect(screen.getAllByRole('button',{name:'Preview'})).toHaveLength(1);
});
it("shows completed history separately from disabled new-message availability",async()=>{
 vi.mocked(api.get).mockImplementation(async p=>p.includes('status')?{enabled:false,state:'AWAITING_SPENDING_APPROVAL',message:'Inference is disabled.'}:p.includes('/workspace/history')?{outcomes:[]}:{tasks:[task]});
 await open();await screen.findByText('Analyze / Results');
 expect(screen.getByLabelText('Task status')).toHaveTextContent('Completed');
 expect(screen.getByLabelText('AI availability')).toHaveTextContent('AI unavailable — awaiting activation');
 fireEvent.change(screen.getByRole('textbox'),{target:{value:'No paid request'}});
 expect(screen.getByRole('button',{name:'Send'})).toBeDisabled();expect(sendAssistant).not.toHaveBeenCalled();
});
it("does not mark historical prepared workspace actions completed without a frontend receipt",async()=>{
 const event:AssistantEvent={type:'tool_result',name:'select_components',ok:true,result:{kind:'workspace_action',actionId:'unconfirmed'}};
 vi.mocked(api.get).mockImplementation(async p=>p.includes('status')?{enabled:false,state:'DISABLED',message:'Disabled'}:p.includes('/workspace/history')?{outcomes:[]}:{tasks:[{...task,events:[event]}]});
 await open();await screen.findByText('Awaiting workspace confirmation');
 expect(screen.getByLabelText('Task status')).not.toHaveTextContent('Completed');
 expect(sendAssistant).not.toHaveBeenCalled();expect(api.post).not.toHaveBeenCalled();
});

it('marks historical primitive receipts as inactive and follows actual lifecycle status',async()=>{
 const event:AssistantEvent={type:'tool_result',name:'prepare_beam_preview',ok:true,result:{kind:'workspace_action',operation:'prepare_beam_preview',actionId:'beam-history',projectId:1,revisionId:8}};
 vi.mocked(api.get).mockImplementation(async p=>p.includes('status')?{enabled:true,state:'AVAILABLE',message:'Mock'}:p.includes('/workspace/history')?{outcomes:[]}:{tasks:[{...task,events:[event]}]});
 await open();await screen.findByText(/Historical preview record/);expect(screen.queryByRole('button',{name:/Apply beam/})).toBeNull();
 act(()=>window.dispatchEvent(new CustomEvent('geoai:primitive-status',{detail:{actionId:'beam-history',projectId:1,phase:'canceled',message:'Canceled - no active approval.'}})));
 expect(screen.getByLabelText('Task status')).toHaveTextContent('Canceled');
 act(()=>window.dispatchEvent(new CustomEvent('geoai:primitive-status',{detail:{actionId:'beam-history',projectId:1,phase:'saved',revisionId:9,message:'Saved beam in revision 9.'}})));
 expect(screen.getByLabelText('Task status')).toHaveTextContent('Saved in revision 9');expect(screen.queryByText(/Historical preview record/)).toBeNull();
 expect(sendAssistant).not.toHaveBeenCalled();expect(api.post).not.toHaveBeenCalled();
});

it("shows no Ready status when inference is disabled without task history",async()=>{
 vi.mocked(api.get).mockImplementation(async p=>p.includes('status')?{enabled:false,state:'AWAITING_SPENDING_APPROVAL',message:'Inference is disabled.'}:p.includes('/workspace/history')?{outcomes:[]}:{tasks:[]});
 await open();await screen.findByText('AI unavailable — awaiting activation');
 expect(screen.getByLabelText('Task status')).toHaveTextContent('No task in progress');
 expect(screen.queryByText('Ready',{exact:true})).toBeNull();
 submit('Do not send');expect(sendAssistant).not.toHaveBeenCalled();
});
it("fails closed for contradictory availability and retains the backend reason",async()=>{
 vi.mocked(api.get).mockImplementation(async p=>p.includes('status')?{enabled:false,state:'AVAILABLE',message:'Provider disabled by administrator.'}:p.includes('/workspace/history')?{outcomes:[]}:{tasks:[]});
 await open();await screen.findByText('AI unavailable — Provider disabled by administrator.');
 submit('Do not send');expect(screen.getByRole('button',{name:'Send'})).toBeDisabled();expect(sendAssistant).not.toHaveBeenCalled();
});
