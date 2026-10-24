import { Fragment, type ReactNode } from "react";

// Render a bounded Markdown subset as React nodes. HTML is always plain text;
// links allow only HTTP(S), local paths and anchors. No HTML injection or images.
function inline(text: string): ReactNode[] {
  const pattern = /(`[^`\n]+`|\*\*[^*]+\*\*|__[^_]+__|\[[^\]\n]+\]\([^\s)]+\)|\*[^*\n]+\*)/g;
  const parts: ReactNode[] = []; let start = 0;
  for (const match of text.matchAll(pattern)) {
    parts.push(text.slice(start, match.index)); const token = match[0];
    if (token.startsWith("`")) parts.push(<code key={match.index}>{token.slice(1,-1)}</code>);
    else if (token.startsWith("**") || token.startsWith("__")) parts.push(<strong key={match.index}>{inline(token.slice(2,-2))}</strong>);
    else if (token.startsWith("*")) parts.push(<em key={match.index}>{inline(token.slice(1,-1))}</em>);
    else {
      const link = token.match(/^\[([^\]]+)\]\((.+)\)$/)!;
      const href = link[2];
      parts.push(/^(https?:\/\/|\/(?!\/)|#)/i.test(href) && !/[\u0000-\u0020\\]/.test(href)
        ? <a key={match.index} href={href} target={href.startsWith("http") ? "_blank" : undefined} rel="noopener noreferrer">{inline(link[1])}</a>
        : <Fragment key={match.index}>{link[1]}</Fragment>);
    }
    start = match.index! + token.length;
  }
  parts.push(text.slice(start)); return parts;
}
export default function AssistantMarkdown({ text }: { text: string }) {
  const lines = text.replaceAll("\r\n", "\n").split("\n"), nodes: ReactNode[] = [];
  for (let i = 0; i < lines.length;) {
    const line = lines[i], key = i;
    if (!line.trim()) { i++; continue; }
    if (line.startsWith("```")) {
      const code: string[] = []; i++;
      while (i < lines.length && !lines[i].startsWith("```")) code.push(lines[i++]);
      if (i < lines.length) i++;
      nodes.push(<pre key={key}><code>{code.join("\n")}</code></pre>); continue;
    }
    if (/^#{1,6}\s/.test(line)) { nodes.push(<h3 key={key}>{inline(line.replace(/^#{1,6}\s+/, ""))}</h3>); i++; continue; }
    if (/^\s*([-*+] |\d+\. )/.test(line)) {
      const ordered = /^\s*\d+\./.test(line), items: ReactNode[] = [];
      while (i < lines.length && (ordered ? /^\s*\d+\. / : /^\s*[-*+] /).test(lines[i])) {
        items.push(<li key={i}>{inline(lines[i++].replace(/^\s*(?:[-*+]|\d+\.)\s+/, ""))}</li>);
      }
      nodes.push(ordered ? <ol key={key}>{items}</ol> : <ul key={key}>{items}</ul>); continue;
    }
    if (line.startsWith("> ")) { nodes.push(<blockquote key={key}>{inline(line.slice(2))}</blockquote>); i++; continue; }
    const paragraph = [line]; i++;
    while (i < lines.length && lines[i].trim() && !/^(#{1,6}\s|```|> |\s*[-*+] |\s*\d+\. )/.test(lines[i])) paragraph.push(lines[i++]);
    nodes.push(<p key={key}>{inline(paragraph.join("\n"))}</p>);
  }
  return <div className="assistant-markdown">{nodes}</div>;
}
