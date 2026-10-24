"use client";
import {useState,type ReactNode} from 'react';
/** Heavy legacy forms stay unmounted until requested in a foundation study. */
export default function SecondaryAnalysisTools({foundation,lazy=false,children}:{foundation:boolean;lazy?:boolean;children:ReactNode}){
 const [open,setOpen]=useState(false);
 return <details data-analysis-tools className="mt-4 border-t border-border pt-4" onToggle={e=>setOpen(e.currentTarget.open)}><summary className="cursor-pointer text-xs text-muted-foreground">{foundation?'Other analysis tools and history':'Advanced analysis · inputs, tools and evidence'}</summary><div className="mt-4">{((!foundation&&!lazy)||open)&&children}</div></details>;
}
