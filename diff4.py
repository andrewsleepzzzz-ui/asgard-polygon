import re, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
p = r"C:\Windows\System32\actor_dump.txt"
recs, cur = [], None
for ln in open(p, encoding="utf-8", errors="ignore").read().splitlines():
    if ln.startswith("A idx="):
        cur = {"raw": ln}
        m = re.search(r"actor=0x([0-9A-F]+).*?ps=0x([0-9A-F]+).*?hp=([-\d.]+).*?own_match=(\d).*?dist=([-\d.]+).*?local=(\d).*?tgt=(\d).*?name=(.*)$", ln)
        if m:
            cur.update(actor=m.group(1), psp=m.group(2), hp=float(m.group(3)), own=m.group(4),
                       dist=float(m.group(5)), tgt=int(m.group(7)), name=m.group(8))
        recs.append(cur)
    elif cur is not None:
        s = ln.strip()
        if s.startswith("AHEX "): cur["ahex"] = s[5:]
        elif s.startswith("PHEX "): cur["phex"] = s[5:]
        elif s.startswith("CHEX "): cur["chex"] = s[5:]
        elif s.startswith("MHEX "): cur["mhex"] = s[5:]

tgt = next((r for r in recs if r.get("tgt") == 1), None)
refs = [r for r in recs if r.get("tgt") == 0 and r.get("name") and r.get("hp", 0) > 0]
print("TARGET %s hp=%.1f  refs=%d" % (tgt["name"], tgt["hp"], len(refs)))
for k in ("ahex","phex","chex","mhex"):
    print("  target has %s: %s" % (k, len(tgt.get(k,""))//2))
    for r in refs:
        print("    ref %-20s has %s: %d" % (r["name"], k, len(r.get(k,""))//2))

for k, label in (("ahex","actor"), ("phex","ps"), ("chex","healthcomp"), ("mhex","mesh")):
    tb = tgt.get(k); rbs = [r.get(k) for r in refs]
    if not tb or not all(rbs):
        print("--- %s: missing data ---" % label); continue
    tb = bytes.fromhex(tb); rbs = [bytes.fromhex(x) for x in rbs]
    L = min([len(tb)] + [len(x) for x in rbs])
    print("--- %s (+0x%X bytes) : target-unique, refs agree ---" % (label, L))
    shown = 0
    for off in range(L):
        vals = {x[off] for x in rbs}
        if len(vals) == 1 and tb[off] not in vals:
            print("   +0x%03X target=%02X refs=%02X" % (off, tb[off], list(vals)[0]))
            shown += 1
            if shown >= 14: break
    if shown == 0: print("   (none)")
