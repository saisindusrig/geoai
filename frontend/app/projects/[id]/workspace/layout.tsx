import type { Metadata } from "next";
import type { ReactNode } from "react";

export const metadata: Metadata = { title: "3D workspace" };

export default function RouteLayout({ children }: { children: ReactNode }) { return children; }
