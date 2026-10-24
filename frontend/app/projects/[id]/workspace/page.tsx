"use client";

import dynamic from "next/dynamic";
import { ProjectLoading } from "@/components/layout/ProjectHeader";

const Page = dynamic(() => import("./WorkspacePageClient"), { ssr: false, loading: () => <ProjectLoading /> });
export default Page;
