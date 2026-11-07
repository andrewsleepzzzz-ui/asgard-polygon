import re, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
p = r"C:\Windows\System32\actor_dump.txt"
lines = open(p, encoding="utf-8", errors="ignore").read().splitlines()
recs, cur = [], None
for ln in lines:
    if ln.startswith("A idx="):
        cur = {"raw": ln}
        m = re.search(r"actor=0x([0-9A-F]+).*?ps=0x([0-9A-F]+).*?hp=([-\d.]+).*?own_match=(\d).*?name=(.*)$", ln)
        if m:
            cur.update(actor=m.group(1), ps=m.group(2), hp=float(m.group(3)), own=m.group(4), name=m.group(5))
        recs.append(cur)
    elif ln.startswith("  AHEX ") and cur: cur["ahex"] = ln[7:].strip()
    elif ln.startswith("  PHEX ") and cur: cur["phex"] = ln[7:].strip()

corpse = next(r for r in recs if r.get("name") == "路克走地鸡")
alive = [r for r in recs if r.get("name") and r is not corpse and r.get("own") == "1"
         and r.get("hp", 0) >= 35 and r.get("name") != "쬀" and r.get("ahex")]
print("corpse huge: hp=%.1f own=%s" % (corpse["hp"], corpse["own"]))
print("alive samples:", len(alive))

cb = bytes.fromhex(corpse["ahex"])
ab = [bytes.fromhex(r["ahex"]) for r in alive]

print("=== actor offsets where corpse differs from EVERY alive ===")
shown = 0
for off in range(0, 0x400):
    cv = cb[off]
    vals = {x[off] for x in ab}
    if cv not in vals and len(vals) <= 3:
        print("  actor+0x%03X corpse=%02X alive=%s" % (off, cv, sorted(vals)))
        shown += 1
        if shown >= 25: break

if corpse.get("phex"):
    pcb = bytes.fromhex(corpse["phex"])
    pab = [bytes.fromhex(r["phex"]) for r in alive if r.get("phex")]
    print("=== PS offsets where corpse differs from EVERY alive ===")
    shown = 0
    for off in range(0, min(0x400, len(pcb))):
        cv = pcb[off]
        vals = {x[off] for x in pab if off < len(x)}
        if cv not in vals and len(vals) <= 3:
            print("  ps+0x%03X corpse=%02X alive=%s" % (off, cv, sorted(vals)))
            shown += 1
            if shown >= 25: break
