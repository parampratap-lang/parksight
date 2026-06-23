import { useState } from "react";
import { Markdown } from "./Markdown";

export default function BriefPanel({ id }: { id: string }) {
  const [md, setMd] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function gen() {
    setBusy(true);
    try {
      const res = await fetch(`/api/brief/${id}`, { method: "POST" });
      const j = await res.json();
      setMd(j.brief_markdown ?? "No brief returned.");
    } catch {
      setMd("⚠️ Could not generate the brief. Is the backend running?");
    } finally { setBusy(false); }
  }

  return (
    <div className="card">
      <div className="card-title">AI enforcement briefing</div>
      {!md && (
        <button className="brief-btn" onClick={gen} disabled={busy}>
          {busy ? "Generating with Claude…" : "Generate enforcement brief"}
        </button>
      )}
      {md && <div className="brief"><Markdown text={md} /></div>}
      {md && !busy && (
        <button className="ts-reset" style={{ marginTop: 6 }} onClick={gen}>Regenerate</button>
      )}
    </div>
  );
}
