import { useRef, useState } from "react";
import { useApp } from "../context/AppContext";
import { Markdown } from "./Markdown";

interface Msg { role: "user" | "assistant"; text: string }
const SUGGESTIONS = [
  "Where should patrols go at 6pm?",
  "Which Upparpet hotspots need towing?",
  "Worst weekend congestion zones?",
];

export default function AssistantPanel() {
  const { setHighlightIds } = useApp();
  const [messages, setMessages] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const bodyRef = useRef<HTMLDivElement>(null);

  const scroll = () => requestAnimationFrame(() => {
    if (bodyRef.current) bodyRef.current.scrollTop = bodyRef.current.scrollHeight;
  });

  async function send(q: string) {
    const query = q.trim();
    if (!query || busy) return;
    setInput("");
    setMessages((m) => [...m, { role: "user", text: query }, { role: "assistant", text: "" }]);
    setBusy(true);
    scroll();
    const setLast = (t: string) =>
      setMessages((m) => { const c = [...m]; c[c.length - 1] = { role: "assistant", text: t }; return c; });
    try {
      const res = await fetch("/api/assistant/stream", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query }),
      });
      const reader = res.body!.getReader();
      const dec = new TextDecoder();
      let acc = "", pending = "", headerParsed = false;
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = dec.decode(value, { stream: true });
        if (!headerParsed) {
          pending += chunk;
          const nl = pending.indexOf("\n");
          if (nl < 0) continue;
          try { const j = JSON.parse(pending.slice(0, nl)); if (j.used_hotspot_ids) setHighlightIds(j.used_hotspot_ids); } catch {}
          acc = pending.slice(nl + 1); headerParsed = true; setLast(acc);
        } else { acc += chunk; setLast(acc); }
        scroll();
      }
    } catch {
      setLast("⚠️ Could not reach the assistant. Is the backend running?");
    } finally { setBusy(false); scroll(); }
  }

  return (
    <div className="assistant">
      <div className="assistant-head">
        <span className="dot-live" /> ParkSight AI · ask in plain English
      </div>
      <div className="assistant-body" ref={bodyRef}>
        {messages.length === 0 && (
          <div className="suggestions">
            {SUGGESTIONS.map((s) => (
              <button key={s} className="chip" onClick={() => send(s)}>{s}</button>
            ))}
          </div>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`msg ${m.role}`}>
            {m.role === "assistant"
              ? (m.text ? <Markdown text={m.text} /> : <span className="muted small">thinking…</span>)
              : m.text}
          </div>
        ))}
      </div>
      <form className="assistant-input" onSubmit={(e) => { e.preventDefault(); send(input); }}>
        <input
          value={input} placeholder="e.g. where to enforce near Koramangala at 6pm?"
          onChange={(e) => setInput(e.target.value)} disabled={busy}
        />
        <button type="submit" disabled={busy || !input.trim()}>{busy ? "…" : "Ask"}</button>
      </form>
    </div>
  );
}
