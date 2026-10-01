"""RAG layer for the REVIEW step (not for cleaning).
Retrieve: past reviewer decisions for similar flags. Generate: a suggestion + plain-English explanation.
Embedding is a local char-trigram hash so it runs offline; swap embed() for a real model / pgvector in prod."""
import json, os, zlib, sqlite3
import numpy as np
D = 256

def embed(text: str) -> np.ndarray:
    v = np.zeros(D); t = f"  {text.lower()}  "
    for i in range(len(t) - 2): v[zlib.crc32(t[i:i+3].encode()) % D] += 1
    n = np.linalg.norm(v); return v / n if n else v

def remember(db: sqlite3.Connection, tenant, flag, action, value=None):
    db.execute("INSERT INTO decisions(tenant,rule,ctx,vec,action,value) VALUES(?,?,?,?,?,?)",
               (tenant, flag["rule"], flag["ctx"], json.dumps(embed(flag["ctx"]).tolist()), action, value))

def retrieve(db, tenant, flag, k=5, min_sim=0.8):
    rows = db.execute("SELECT ctx,vec,action,value FROM decisions WHERE tenant=? AND rule=?", (tenant, flag["rule"])).fetchall()
    if not rows: return []
    q = embed(flag["ctx"]); sc = np.array([np.dot(q, np.array(json.loads(r[1]))) for r in rows])
    return [dict(ctx=rows[i][0], action=rows[i][2], value=rows[i][3], sim=float(sc[i])) for i in np.argsort(-sc)[:k] if sc[i] >= min_sim]

def suggest(db, tenant, flag):
    """Majority past decision among similar flags -> one-click suggestion with evidence."""
    # Row-specific values (phone, amount, date, name) must NEVER be copied between rows; only decisions
    # (keep/exclude/confirm) and category mappings (branch, status) are safe to learn.
    if flag["kind"] == "value" and flag["field"] not in ("branch", "status"): return None
    nb = retrieve(db, tenant, flag)
    if not nb: return None
    top = max({n["action"] for n in nb}, key=lambda a: sum(n["action"] == a for n in nb))
    votes = [n for n in nb if n["action"] == top]
    text = f'{len(votes)} of {len(nb)} similar past cases were resolved as "{top}"' + (f' (e.g. value {votes[0]["value"]})' if votes[0]["value"] else "")
    return {"action": top, "value": votes[0]["value"], "evidence": text, "explanation": llm_explain(flag, nb, text)}

def llm_explain(flag, neighbours, fallback):
    if not os.getenv("ANTHROPIC_API_KEY"): return fallback
    try:
        import anthropic
        r = anthropic.Anthropic().messages.create(model=os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5-5"), max_tokens=150,
            messages=[{"role": "user", "content": f"Loan-register flag: {flag['msg']}\nSimilar past reviewer decisions: {json.dumps(neighbours)}\n"
                       "In 2 plain sentences for a non-technical branch clerk: why was this flagged and what do past decisions suggest? Do not invent facts."}])
        return r.content[0].text
    except Exception: return fallback
