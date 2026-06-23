// Minimal GFM-ish renderer (headings, bold, code, bullets) — no external dep.
function esc(s: string) {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}
function inline(s: string) {
  return esc(s)
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/`(.+?)`/g, "<code>$1</code>");
}
export function Markdown({ text }: { text: string }) {
  const lines = text.split("\n");
  const out: JSX.Element[] = [];
  let bullets: string[] = [];
  const flush = () => {
    if (bullets.length) {
      out.push(<ul key={out.length}>{bullets.map((b, i) => (
        <li key={i} dangerouslySetInnerHTML={{ __html: inline(b) }} />
      ))}</ul>);
      bullets = [];
    }
  };
  for (const ln of lines) {
    const t = ln.trim();
    if (t.startsWith("### ")) { flush(); out.push(<h4 key={out.length} dangerouslySetInnerHTML={{ __html: inline(t.slice(4)) }} />); }
    else if (t.startsWith("## ")) { flush(); out.push(<h3 key={out.length} dangerouslySetInnerHTML={{ __html: inline(t.slice(3)) }} />); }
    else if (t.startsWith("# ")) { flush(); out.push(<h3 key={out.length} dangerouslySetInnerHTML={{ __html: inline(t.slice(2)) }} />); }
    else if (t.startsWith("- ") || t.startsWith("* ")) { bullets.push(t.slice(2)); }
    else if (t === "") { flush(); }
    else { flush(); out.push(<p key={out.length} dangerouslySetInnerHTML={{ __html: inline(t) }} />); }
  }
  flush();
  return <div className="md">{out}</div>;
}
