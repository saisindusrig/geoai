import type { Metadata } from "next";
import type { ReactNode } from "react";

export const metadata: Metadata = { title: "Scenarios" };

export default function RouteLayout({ children }: { children: ReactNode }) { return children; }
