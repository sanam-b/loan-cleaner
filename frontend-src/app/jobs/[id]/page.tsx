"use client";
import { use, useCallback, useEffect, useState } from "react";
import { api, FIELDS, Flag, Row } from "@/lib/api";

export default function Job({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const [job, setJob] = useState<any>(null); const [rows, setRows] = useState<Row[]>([]);
  const [view, setView] = useState<"review" | "all">("review"); const [page, setPage] = useState(1);

  const load = useCallback(async () => {
    const j = await api.job(id); setJob(j);
    if (j.status === "done") setRows(await api.rows(id, view, page));
  }, [id, view, page]);
  useEffect(() => { load(); const t = setInterval(() => job?.status === "processing" && load(), 1500); return () => clearInterval(t); }, [load, job?.status]);

  if (!job) return <p>Loading…</p>;
  if (job.status === "processing") return <p style={{ padding: 40 }}>Cleaning {job.filename}… (big files take a moment)</p>;
  if (job.status === "error") return <p style={{ padding: 40, color: "crimson" }}>{job.error}</p>;
  const c = job.counts ?? {};
  return (
    <main style={{ maxWidth: 1100, margin: "30px auto", fontFamily: "system-ui" }}>
      <h2>{job.filename}</h2>
      <div style={{ display: "flex", gap: 12 }}>
        {[["Clean", c.ok ?? 0], ["Auto-fixed cells", job.fixes], ["Need review", c.review ?? 0], ["Excluded", c.excluded ?? 0]].map(([l, v]) =>
          <div key={l as string} style={{ padding: "8px 14px", background: "#f3f4f6", borderRadius: 8 }}><b style={{ fontSize: 20 }}>{v}</b><br />{l}</div>)}
        <a href={`/api/jobs/${id}/export`} style={{ marginLeft: "auto", alignSelf: "center" }}><button>⬇ Download Excel</button></a>
      </div>
      <p>
        <button onClick={() => { setView("review"); setPage(1); }} disabled={view === "review"}>Needs review</button>{" "}
        <button onClick={() => { setView("all"); setPage(1); }} disabled={view === "all"}>All rows</button>
      </p>
      <table width="100%" cellPadding={6} style={{ borderCollapse: "collapse" }}>
        <thead><tr><th>Row</th>{FIELDS.map((f) => <th key={f} align="left">{f}</th>)}<th /></tr></thead>
        <tbody>{rows.map((r) => (<RowView key={r.n} r={r} id={id} onDone={load} />))}</tbody>
      </table>
      <p><button disabled={page === 1} onClick={() => setPage(page - 1)}>← Prev</button> Page {page}{" "}
        <button disabled={rows.length < 20} onClick={() => setPage(page + 1)}>Next →</button></p>
    </main>
  );
}

function RowView({ r, id, onDone }: { r: Row; id: string; onDone: () => void }) {
  const hot = (f: string) => r.flags.some((x) => x.field === f && !x.resolved);
  return (<>
    <tr style={{ borderTop: "1px solid #ddd" }}><td>{r.n}</td>
      {FIELDS.map((f) => <td key={f} style={{ background: hot(f) ? "#fff3df" : r.fixes.some((x) => x.field === f) ? "#e5f5ec" : "" }}>{String(r.clean[f])}</td>)}
      <td>{r.state}</td></tr>
    {(r.flags.length > 0 || r.info.length > 0) && <tr><td /><td colSpan={7}>
      {r.flags.map((f, i) => <FlagCard key={i} f={f} i={i} r={r} id={id} onDone={onDone} />)}
      {r.info.map((t, i) => <div key={i} style={{ color: "#667", fontSize: 13 }}>ℹ {t}</div>)}
    </td></tr>}
  </>);
}

function FlagCard({ f, i, r, id, onDone }: { f: Flag; i: number; r: Row; id: string; onDone: () => void }) {
  const [val, setVal] = useState(f.suggestion?.value ?? String(r.clean[f.field] || r.raw[f.field] || "")); const [err, setErr] = useState("");
  const go = async (action: string, value?: string) => { try { await api.resolve(id, r.n, i, action, value); onDone(); } catch (e: any) { setErr(e.message); } };
  if (f.resolved) return <div style={{ background: "#e5f5ec", padding: 8, margin: "4px 0", borderRadius: 6 }}>✔ {f.msg}</div>;
  return (
    <div style={{ background: "#fff3df", padding: 10, margin: "6px 0", borderRadius: 8 }}>
      <div>⚠ {f.msg}</div>
      <small>Why flagged: {f.rule}. Original: “{String(r.raw[f.field] ?? "") || "(blank)"}”</small>
      {f.suggestion && <div style={{ margin: "6px 0", padding: 6, background: "#eef5ff", borderRadius: 6 }}>
        💡 {f.suggestion.explanation} <button onClick={() => go(f.suggestion!.action, f.suggestion!.value ?? undefined)}>Do it ({f.suggestion.action})</button></div>}
      <div style={{ marginTop: 6 }}>
        {f.kind === "dup" && <><button onClick={() => go("keep")}>Not a duplicate</button> <button onClick={() => go("exclude")}>Duplicate — exclude row {r.n}</button></>}
        {f.kind === "ack" && <button onClick={() => go("keep")}>Seen — it’s fine</button>}
        {(f.kind === "value" || f.kind === "confirm") && <>
          <input value={val} onChange={(e) => setVal(e.target.value)} /> <button onClick={() => go("apply", val)}>Apply correction</button>{" "}
          {f.kind === "confirm" ? <button onClick={() => go("keep")}>Value is correct</button> : <button onClick={() => go("blank")}>Leave blank</button>}</>}
        <span style={{ color: "crimson", marginLeft: 8 }}>{err}</span>
      </div>
    </div>);
}
