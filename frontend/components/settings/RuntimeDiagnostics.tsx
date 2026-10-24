"use client";
import Link from 'next/link';
import {useCallback,useEffect,useRef,useState} from 'react';
import {api} from '@/lib/api';
import {Badge} from '@/components/ui/badge';
import {Card,CardContent} from '@/components/ui/card';

type State='HEALTHY'|'DEGRADED'|'BLOCKED'|'UNAVAILABLE';
type Check={name:string;status:State;summary:string;action:string};
export type DiagnosticReport={checked_at:string;checks:Check[];methods:{method:string;status:string;current_results:number;historical_results:number}[];engineering_approval:'DISABLED';inference_requested:false;warning_codes?:string[]};
const warningNotes:Record<string,string>={insecure_app_secret:'Development authentication secret remains configured; public exposure is blocked.',auth_jwt_not_required:'Production JWT enforcement is not enabled.',sqlite_in_production:'SQLite is not a qualified production database.',redis_unavailable:'In-memory jobs are not durable across restarts.',local_storage:'Local storage requires qualified production durability and recovery.',map_tokens_missing:'Map imagery relies on fallback sources.',cesium_ion_missing:'Hosted terrain and imagery configuration is incomplete.'};
const labels:Record<State,string>={HEALTHY:'Healthy',DEGRADED:'Degraded',BLOCKED:'Blocked',UNAVAILABLE:'Unavailable'};
const methodNames:Record<string,string>={frame:'Planar frame',slab:'LOAD-ONLY floor',spatial:'Spatial frame',coupled:'Synthetic shell–frame',foundation:'Bounded foundation'};
const capabilityNames:Record<string,string>={SUPPORTED:'Supported',MISSING_INPUTS:'Missing inputs',UNSUPPORTED:'Unsupported',STALE:'Stale'};
const explanations:Record<string,string>={SUPPORTED:'Existing backend validator accepts the saved method inputs. Exact authorization is still required.',MISSING_INPUTS:'Complete explicitly declared engineering inputs in Analysis.',UNSUPPORTED:'The existing method does not support this saved model. Calculation remains disabled.',STALE:'Saved evidence does not match the current revision, source or review. Review historical evidence in Analysis.'};

export default function RuntimeDiagnostics(){
 const [report,setReport]=useState<DiagnosticReport>(),[loading,setLoading]=useState(false),[failed,setFailed]=useState(false),[context,setContext]=useState<{project:number;revision:number}>();
 const active=useRef<AbortController|null>(null);
 const load=useCallback(async()=>{
  if(active.current)return;
  const controller=new AbortController();active.current=controller;setLoading(true);setFailed(false);setReport(undefined);
  const params=new URLSearchParams(window.location.search),project=Number(params.get('project_id')),revision=Number(params.get('model_revision_id'));
  const hasContext=Number.isSafeInteger(project)&&project>0&&Number.isSafeInteger(revision)&&revision>0;
  setContext(hasContext?{project,revision}:undefined);
  const query=hasContext?`?project_id=${project}&model_revision_id=${revision}`:'';
  const timeout=window.setTimeout(()=>controller.abort(),10000);
  try{
   const data=await api.get<DiagnosticReport>('/api/system/diagnostics'+query,controller.signal);
   if(!Array.isArray(data.checks)||!Array.isArray(data.methods)||data.engineering_approval!=='DISABLED'||data.inference_requested!==false)throw Error('Invalid diagnostic contract');
   if(active.current===controller&&!controller.signal.aborted)setReport(data);
  }catch{if(active.current===controller)setFailed(true);}
  finally{window.clearTimeout(timeout);if(active.current===controller){active.current=null;setLoading(false);}}
 },[]);
 useEffect(()=>{const timer=window.setTimeout(()=>void load(),0);return()=>{window.clearTimeout(timer);const controller=active.current;active.current=null;controller?.abort();};},[load]);
 const connectivity:Check={name:'Frontend / API connection',status:failed?'UNAVAILABLE':report?'HEALTHY':'BLOCKED',summary:failed?'No current diagnostic response. The API may be stopped, unreachable, unauthorized or timed out. Previous health is not shown as current.':report?'This page received a fresh response through the configured application API path.':'Waiting for a bounded read-only check.',action:failed?'Confirm the backend on port 8001 and the same-origin proxy on port 3001. Use run-website.bat, check startup logs, then Retry. If sign-in is required, sign in first.':'No automatic polling or calculation retries.'};
 return <div className="min-h-0 flex-1 overflow-y-auto" data-testid="diagnostics-scroll"><section className="mx-auto w-full max-w-5xl space-y-5 px-6 py-7" aria-label="Runtime diagnostics">
  <div className="flex flex-wrap items-start justify-between gap-3"><div><p className="text-xs uppercase tracking-wider text-muted-foreground">StruvoCivil / local runtime</p><h1 className="mt-2 text-3xl font-medium">Runtime diagnostics</h1><p className="mt-2 text-sm text-muted-foreground">Read-only checks. No FEA, inference, data repair or automatic retries.</p></div><div className="flex flex-wrap items-center gap-3 text-sm"><Link href={context?`/projects/${context.project}/workspace`:'/dashboard'} className="text-primary underline">{context?'Return to model':'Dashboard'}</Link><Link href="/settings" className="text-primary underline">Settings</Link><button className="rounded border border-border px-4 py-2 disabled:opacity-50" disabled={loading} aria-busy={loading} onClick={()=>void load()}>{loading?'Checking…':failed?'Retry diagnostics':'Refresh diagnostics'}</button></div></div>
  <p className="rounded border border-border bg-muted/20 p-3 text-sm">Healthy services do not imply engineering safety or production approval. Engineering approval remains disabled.</p>
  {context&&<p className="text-sm">Saved context: project {context.project} · revision {context.revision}</p>}
  {loading&&<p role="status">Reading current runtime status. No analysis is running.</p>}
  {failed&&<p role="alert" className="text-sm">Diagnostics unavailable. No state-changing request was retried. Use the manual recovery steps below.</p>}
  {report&&<p className="text-xs text-muted-foreground">Checked {new Date(report.checked_at).toLocaleString()} · snapshot only; use Refresh to recheck.</p>}
  <div className="grid gap-3 md:grid-cols-2">{[connectivity,...(report?.checks??[])].map(item=><Card key={item.name}><CardContent className="space-y-2 p-4"><div className="flex items-start justify-between gap-3"><h2 className="text-sm font-semibold">{item.name}</h2><Badge variant={item.status==='HEALTHY'?'default':'outline'}>{labels[item.status]??'Unavailable'}</Badge></div><p className="text-sm text-muted-foreground">{item.summary}</p>{item.status!=='HEALTHY'&&<p className="text-sm">{item.action}</p>}</CardContent></Card>)}</div>
  {!!report?.methods.length&&<section aria-label="Saved engineering capabilities" className="space-y-2"><h2 className="font-semibold">Saved engineering capabilities</h2><div className="grid gap-3 md:grid-cols-2">{report.methods.map(method=><Card key={method.method}><CardContent className="space-y-2 p-4"><div className="flex justify-between gap-3"><h3 className="text-sm font-semibold">{methodNames[method.method]??'Engineering method'}</h3><Badge variant="outline">{capabilityNames[method.status]??'Unsupported'}</Badge></div><p className="text-sm text-muted-foreground">{explanations[method.status]??explanations.UNSUPPORTED}</p><p className="text-xs">{method.current_results} current result(s) · {method.historical_results} historical / failed / stale record(s)</p></CardContent></Card>)}</div></section>}
  {!!report?.warning_codes?.length&&<details className="text-sm"><summary className="cursor-pointer">Release configuration notes ({report.warning_codes.length})</summary><ul className="mt-2 list-disc space-y-1 pl-5">{report.warning_codes.map(code=><li key={code}>{warningNotes[code]??'An existing production dependency is unavailable or unverified. Review the readiness report.'}</li>)}</ul></details>}
  <details className="text-sm"><summary className="cursor-pointer">Logs and manual recovery</summary><p className="mt-2">Existing local launcher logs: docs/copilot-milestone-2/review-start.log and review-start.err.log. Backend responses carry X-Request-ID for correlation. Resolve occupied ports manually; do not start duplicate servers. Production blockers remain in docs/PRODUCTION_BETA_READINESS.md.</p></details>
 </section></div>;
}
