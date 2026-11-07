import re, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
p = r"C:\Windows\System32\actor_dump.txt"
lines = open(p, encoding="utf-8", errors="ignore").read().splitlines()
recs = []
cur = None
for ln in lines:
    if ln.startswith("A idx="):
        cur = {"raw": ln}
        m = re.search(r"actor=0x([0-9A-F]+).*?ps=0x([0-9A-F]+).*?hp=([-\d.]+).*?own_match=(\d).*?name=(.*)$", ln)
        if m:
            cur.update(actor=m.group(1), ps=m.group(2), hp=float(m.group(3)), own=m.group(4), name=m.group(5))
        recs.append(cur)
    elif ln.startswith("  AHEX ") and cur:
        cur["ahex"] = ln[7:].strip()
    elif ln.startswith("  PHEX ") and cur:
        cur["phex"] = ln[7:].strip()

named = [r for r in recs if r.get("name")]
print("records=%d named=%d" % (len(recs), len(named)))
for r in named:
    print("  name=%-24s hp=%-6.1f own=%s ps=%s actor=0x%s" % (r["name"], r["hp"], r["own"], r["ps"], r["actor"]))
