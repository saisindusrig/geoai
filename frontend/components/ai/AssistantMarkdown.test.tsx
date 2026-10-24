import { render, screen, cleanup } from "@testing-library/react";
import { afterEach, expect, it } from "vitest";
import Markdown from "./AssistantMarkdown";
afterEach(cleanup);
it("renders common Markdown safely without interpreting HTML or script links",()=>{
 render(<Markdown text={'## Saved results\n\n**Current** and *unverified*.\n\n1. Inspect `record 12`.\n2. Read [evidence](/projects/1/workspace).\n\n```text\n<script>alert(1)</script>\n```\n\n[unsafe](javascript:alert)\n<img src=x onerror=alert(1)>'}/>);
 expect(screen.getByRole('heading',{name:'Saved results'})).toBeVisible();
 expect(screen.getByText('Current').tagName).toBe('STRONG');
 expect(screen.getByRole('link',{name:'evidence'})).toHaveAttribute('href','/projects/1/workspace');
 expect(screen.queryByRole('link',{name:'unsafe'})).toBeNull();
 expect(document.querySelector('script,img')).toBeNull();
 expect(document.querySelectorAll('ol li')).toHaveLength(2);
});
