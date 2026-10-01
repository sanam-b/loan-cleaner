"""Deterministic per-row cleaning. Returns auto-fix notes or flags -- never guesses."""
import re
from datetime import date, datetime
from rapidfuzz.distance import Levenshtein as L
from .config import FIELDS

MONTHS = ["jan","feb","mar","apr","may","jun","jul","aug","sep","oct","nov","dec"]
def s(v): return re.sub(r"\s+", " ", str(v if v is not None else "")).strip()
def ok(v, note=None): return {"v": v, "note": note}
def bad(msg, kind="value", v=None): return {"err": msg, "kind": kind, "v": v}

def mk_date(y, m, d):
    try: return date(y, m, d).isoformat()
    except ValueError: return None

def branch(raw, t):
    x = s(raw)
    if not x: return bad("Branch is missing")
    k = " ".join(w for w in x.lower().replace(".", "").replace(",", "").split() if w not in t.drop_words)
    hit = next((b for b in t.branches if k == b.lower() or k.startswith(b.lower()) or L.distance(k, b.lower()) <= 1), None)
    if not hit: return bad(f'Branch "{x}" is not in the known list ({", ".join(t.branches)})')
    return ok(hit, f'Standardised branch "{x}" -> "{hit}"' if x != hit else None)

def name(raw, t):
    x = s(raw)
    if not x: return bad("Customer name is missing - can't be guessed")
    v = re.sub(r"\b\w", lambda m: m.group().upper(), x.lower())
    return ok(v, f'Capitalised name "{x}" -> "{v}"' if v != x else None)

def amount(raw, t):
    if s(raw) == "": return bad("Loan amount is missing in the register")
    x = s(raw); u = re.sub(r"[₹,\s]|rs\.?|inr", "", x, flags=re.I)
    m = re.fullmatch(r"(-?\d+(?:\.\d+)?)(k|l|lakh|lac)?", u, re.I)
    if not m: return bad(f'Can\'t read "{x}" as an amount')
    n = float(m[1]); suf = (m[2] or "").lower()
    if suf == "k": n *= 1000
    elif suf: n *= 100000
    n = int(n) if n == int(n) else n
    if n <= 0: return bad(f"Amount {n} is zero/negative - a loan can't be negative, so no guess is made")
    return ok(n, f'Amount "{x}" -> {n}' if str(n) != x else None)

def loan_date(raw, t, today=None):
    today = today or date.today().isoformat()
    if s(raw) == "": return bad("Loan date is missing")
    amb = False
    if isinstance(raw, (datetime, date)): y, m, d = raw.year, raw.month, raw.day
    else:
        x = s(raw)
        if k := re.fullmatch(r"(\d{4})[-./](\d{1,2})[-./](\d{1,2})", x): y, m, d = map(int, k.groups())
        elif k := re.fullmatch(r"(\d{1,2})[-./](\d{1,2})[-./](\d{2,4})", x):
            a, b, y = map(int, k.groups()); y += 2000 if y < 100 else 0
            d, m = (a, b) if t.day_first else (b, a); amb = a <= 12 and b <= 12 and a != b
        elif k := re.fullmatch(r"([A-Za-z]{3})[a-z]*\.?\s+(\d{1,2}),?\s+(\d{4})", x):
            m, d, y = MONTHS.index(k[1].lower()) + 1 if k[1].lower() in MONTHS else 0, int(k[2]), int(k[3])
        elif k := re.fullmatch(r"(\d{1,2})\s+([A-Za-z]{3})[a-z]*\.?,?\s+(\d{4})", x):
            d, m, y = int(k[1]), MONTHS.index(k[2].lower()) + 1 if k[2].lower() in MONTHS else 0, int(k[3])
        else: return bad(f'Can\'t read "{x}" as a date')
    iso = m > 0 and mk_date(y, m, d)
    if not iso: return bad(f'"{s(raw)}" is not a real calendar date (day {d}, month {m})')
    if iso > today: return bad(f"Date {iso} is in the future", "confirm", iso)
    note = None
    if iso != s(raw): note = f'Date "{s(raw)}" -> {iso}' + (f' (read as {"DD/MM" if t.day_first else "MM/DD"})' if amb else "")
    return ok(iso, note)

def phone(raw, t):
    if s(raw) == "": return bad("Phone number is missing")
    x = s(raw)
    if re.search(r"[a-z]", x, re.I): return bad(f'Phone "{x}" contains letters')
    d = re.sub(r"\D", "", x)
    if len(d) == 12 and d.startswith("91"): d = d[2:]
    elif len(d) == 11 and d[0] == "0": d = d[1:]
    if len(d) != 10: return bad(f'Phone "{x}" has {len(d)} digits, expected 10')
    if d[0] not in "6789": return bad(f'Indian mobiles start with 6-9; "{d}" does not')
    if re.search(r"(\d)\1{5,}$", d): return bad(f"Phone {d} ends in a repeated-digit run - looks like a placeholder", "confirm", d)
    return ok(d, f'Phone "{x}" -> {d}' if d != x else None)

def status(raw, t):
    x = s(raw).lower(); mp = {"active": "Active", "closed": "Closed", "npa": "NPA"}
    if not x: return bad("Status is missing")
    if x not in mp: return bad(f'Unknown status "{s(raw)}" (expected Active / Closed / NPA)')
    return ok(mp[x], f'Status "{s(raw)}" -> "{mp[x]}"' if mp[x] != s(raw) else None)

CLEANERS = {"branch": branch, "name": name, "amount": amount, "date": loan_date, "phone": phone, "status": status}

def clean_row(raw: dict, t):
    clean, fixes, flags = {}, [], []
    for f in FIELDS:
        r = CLEANERS[f](raw.get(f), t); clean[f] = r["v"] if r.get("v") is not None else ""
        if "err" in r:
            flags.append({"field": f, "kind": r["kind"], "msg": r["err"], "rule": f"Format check: {f}",
                          "ctx": f"{f}|{s(raw.get(f))}|{r['err']}", "resolved": False})
        elif r.get("note"):
            fixes.append({"field": f, "from": s(raw.get(f)), "to": r["v"], "msg": r["note"], "by": "auto"})
    return clean, fixes, flags
