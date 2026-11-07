import re, sys, collections
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
p = r"C:\Windows\System32\actor_dump.txt"
recs, cur = [], None
for ln in open(p, encoding="utf-8", errors="ignore").read().splitlines():
    if ln.startswith("A idx="):
        cur = {"raw": ln}
        m = re.search(r"actor=0x([0-9A-F]+).*?ps=0x([0-9A-F]+).*?hp=([-\d.]+).*?own_match=(\d).*?dist=([-\d.]+).*?name=(.*)$", ln)
        if m:
            cur.update(actor=m.group(1), ps=m.group(2), hp=float(m.group(3)), own=m.group(4), dist=float(m.group(5)), name=m.group(6))
        recs.append(cur)
    elif ln.startswith("  AHEX ") and cur: cur["ahex"] = ln[7:].strip()
    elif ln.startswith("  PHEX ") and cur: cur["phex"] = ln[7:].strip()
    elif ln.startswith("  CHEX ") and cur: cur["chex"] = ln[7:].strip()

named = [r for r in recs if r.get("name") and r.get("name") != "쬀" and r.get("ahex")]
print("named records:", len(named))
for r in named:
    print("  %-26s hp=%-5.1f own=%s dist=%.1f" % (r["name"], r["hp"], r["own"], r.get("dist", -1)))

if len(named) >= 3:
    A = [bytes.fromhex(r["ahex"]) for r in named]
    L = min(len(x) for x in A)
    print("--- actor offsets where exactly ONE record deviates (and value is 0 or 1) ---")
    cnt = 0
    for off in range(L):
        vals = [x[off] for x in A]
        c = collections.Counter(vals)
        if len(c) != 2: continue
        (v1, n1), (v2, n2) = c.most_common(2)
        if n1 == len(vals) - 1 and n2 == 1:
            dev = v2 if v2 != v1 else v1
            if dev in (0, 1) and (v1 in (0, 1)):
                who = named[vals.index(v2)]["name"]
                print("  actor+0x%03X deviant=%s val=%02X others=%02X" % (off, who, v2, v1))
                cnt += 1
                if cnt >= 20: break
