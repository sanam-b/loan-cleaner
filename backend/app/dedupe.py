"""Cross-row checks that stay ~O(n): candidates come from hash groups (blocking), never n^2."""
from collections import defaultdict
from statistics import median
from datetime import date
from rapidfuzz import fuzz
from .cleaner import s

def sim(a, b):
    n = lambda x: s(x).lower().replace(".", "")
    x, y = n(a), n(b)
    if not x or not y: return False
    if fuzz.ratio(x, y) >= 85: return True
    p, q = x.split(), y.split()
    return any(len(a_) > 1 and len(a_[0]) == 1 and a_[0] == b_[0][0] and a_[-1] == b_[-1] for a_, b_ in ((p, q), (q, p)))

def find_links(index, t):
    """index: iterable of (n, name, amount, date, phone, has_date_flag). -> {n: [flags]}, {n: [info]}"""
    flags, info = defaultdict(list), defaultdict(list)
    by_ad, by_ph, seen = defaultdict(list), defaultdict(list), []
    for n, nm, amt, dt, ph, _ in index:
        dup = next((a for a in by_ad.get((amt, dt), []) if amt != "" and dt and sim(a[1], nm)), None) if amt != "" and dt else None
        if dup:
            flags[n].append({"field": "_dup", "kind": "dup", "ref": dup[0], "rule": "Duplicate check", "resolved": False,
                "ctx": f"dup|{dup[1]}|{nm}",
                "msg": f'Possible duplicate of row {dup[0]}: names "{dup[1]}" ~ "{nm}", same amount ({amt}) and date ({dt}); '
                       f'phones {"match" if ph and ph == dup[4] else ("differ: %s vs %s" % (ph, dup[4]) if ph and dup[4] else "not comparable")}'})
        elif ph:
            prev = by_ph.get(ph, [])
            same = next((a for a in prev if sim(a[1], nm)), None)
            if same: info[n].append(f"Same customer & phone as row {same[0]} but different amount/date - likely a repeat loan, kept separate")
            elif prev: flags[n].append({"field": "_ph", "kind": "ack", "ref": prev[0][0], "rule": "Shared-phone check", "resolved": False,
                "ctx": f"ph|{prev[0][1]}|{nm}", "msg": f'Same phone ({ph}) as row {prev[0][0]}, different name ("{prev[0][1]}" vs "{nm}") - family or entry error?'})
        row = (n, nm, amt, dt, ph)
        if amt != "" and dt: by_ad[(amt, dt)].append(row)
        if ph: by_ph[ph].append(row)
    return flags, info

def outliers(index, t):
    ds = sorted(date.fromisoformat(d).toordinal() for _, _, _, d, _, bad in index if d and not bad)
    if len(ds) < 3: return {}
    med = int(median(ds)); out = {}
    for n, _, _, d, _, bad in index:
        if d and not bad and abs(date.fromisoformat(d).toordinal() - med) > t.outlier_days:
            out[n] = {"field": "date", "kind": "confirm", "rule": "Outlier check", "resolved": False, "ctx": f"outlier|{d}",
                      "msg": f"Date {d} is over {t.outlier_days} days from the rest of this file (typical: {date.fromordinal(med)}) - possible typo"}
    return out
