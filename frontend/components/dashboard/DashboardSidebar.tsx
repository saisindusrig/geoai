"use client";
import Link from "next/link";
import { Box, Folder, FolderCog, FolderPlus, HelpCircle, LayoutDashboard, Layers, PanelLeftClose, PanelLeftOpen, Settings, Shapes } from "lucide-react";
import BrandWordmark from "@/components/landing/BrandWordmark";
import { LOCAL_SANDBOX_PATH } from "@/lib/local-sandbox";
import type { ProjectFolder } from "@/lib/types";

export default function DashboardSidebar({folders,selected,collapsed,onCollapse,onFolder,onManage,onNavigate,section}:{folders:ProjectFolder[];selected:"all"|"unfiled"|number;collapsed:boolean;onCollapse:()=>void;onFolder:(id:number)=>void;onManage:(folder?:ProjectFolder)=>void;onNavigate:(section:"overview"|"concepts"|"templates")=>void;section:string}) {
  return <aside className="hub-sidebar">
    <div className="hub-brand"><Link href="/" title="GeoAI home">{collapsed?<Shapes size={24}/>:<BrandWordmark size="sm"/>}</Link><button onClick={onCollapse} title={collapsed?"Expand sidebar":"Collapse sidebar"} aria-label={collapsed?"Expand sidebar":"Collapse sidebar"}>{collapsed?<PanelLeftOpen size={16}/>:<PanelLeftClose size={16}/>}</button></div>
    <span className="hub-micro hub-sidebar-label">WORKSPACE</span>
    <nav aria-label="Dashboard navigation">{([["overview","Overview",LayoutDashboard],["concepts","Concepts",Layers],["templates","Templates",Shapes]] as const).map(([id,label,Icon])=><button key={id} title={label} aria-current={section===id?"page":undefined} onClick={()=>onNavigate(id)}><Icon size={16}/><span>{label}</span></button>)}<Link href={LOCAL_SANDBOX_PATH} title="3D Sandbox"><Box size={16}/><span>3D Sandbox</span></Link></nav>
    <div className="hub-folders"><div className="hub-folder-heading"><span className="hub-micro hub-sidebar-label">FOLDERS</span><button onClick={()=>onManage()} aria-label="New folder" title="New folder"><FolderPlus size={15}/></button></div>{folders.length===0&&!collapsed&&<p>No folders yet.<br/>Organize your saved concepts here.</p>}{folders.map(folder=><div className="hub-folder" key={folder.id}><button title={folder.name} aria-pressed={selected===folder.id} onClick={()=>onFolder(folder.id)}><Folder size={15}/><span>{folder.name}</span></button>{!collapsed&&<button title={`Manage ${folder.name}`} aria-label={`Manage ${folder.name}`} onClick={()=>onManage(folder)}><FolderCog size={14}/></button>}</div>)}</div>
    <nav className="hub-sidebar-bottom" aria-label="Workspace resources"><Link href="/settings" title="Settings"><Settings size={16}/><span>Settings</span></Link><Link href="/#faq" title="Help"><HelpCircle size={16}/><span>Help</span></Link></nav>
    {!collapsed&&<div className="hub-sidebar-foot"><i/> CONCEPT PLANNING<br/><small>Professional verification required</small></div>}
  </aside>;
}
