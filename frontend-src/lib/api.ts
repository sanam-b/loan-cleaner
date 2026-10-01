export type Flag = { field: string; kind: "value" | "confirm" | "dup" | "ack"; msg: string; rule: string; resolved: boolean;
  suggestion?: { action: string; value: string | null; evidence: string; explanation: string } | null };
export type Row = { n: number; raw: Record<string, any>; clean: Record<string, any>; fixes: any[]; flags: Flag[]; info: string[]; state: string };
export const FIELDS = ["branch", "name", "amount", "date", "phone", "status"] as const;
const j = async (r: Response) => { if (!r.ok) throw new Error((await r.json()).detail ?? r.statusText); return r.json(); };
export const api = {
  upload: (f: File) => { const fd = new FormData(); fd.append("file", f); return fetch("/api/jobs", { method: "POST", body: fd }).then(j); },
  job: (id: string) => fetch(`/api/jobs/${id}`).then(j),
  rows: (id: string, state: string, page: number) => fetch(`/api/jobs/${id}/rows?state=${state}&page=${page}&size=20`).then(j) as Promise<Row[]>,
  resolve: (id: string, n: number, i: number, action: string, value?: string) =>
    fetch(`/api/jobs/${id}/rows/${n}/flags/${i}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ action, value }) }).then(j),
};
