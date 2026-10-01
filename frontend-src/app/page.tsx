"use client";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { api } from "@/lib/api";

export default function Home() {
  const router = useRouter(); const [busy, setBusy] = useState(false); const [err, setErr] = useState("");
  const onFile = async (f?: File) => {
    if (!f) return; setBusy(true);
    try { const { id } = await api.upload(f); router.push(`/jobs/${id}`); } catch (e: any) { setErr(e.message); setBusy(false); }
  };
  return (
    <main style={{ maxWidth: 640, margin: "80px auto", fontFamily: "system-ui" }}>
      <h1>Loan Register Cleaner</h1>
      <p>Upload a branch register (.xlsx or .csv). We fix the safe things, and ask you about the rest.</p>
      <label style={{ display: "block", border: "2px dashed #bbb", borderRadius: 10, padding: 40, textAlign: "center", cursor: "pointer" }}>
        {busy ? "Uploading…" : "Click to choose a file"}
        <input type="file" accept=".xlsx,.csv" hidden onChange={(e) => onFile(e.target.files?.[0])} />
      </label>
      {err && <p style={{ color: "crimson" }}>{err}</p>}
    </main>
  );
}
