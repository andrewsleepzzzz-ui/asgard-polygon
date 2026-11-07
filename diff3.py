import re, sys, collections
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
p = r"C:\Windows\System32\actor_dump.txt"
recs, cur = [], None
for ln in open(p, encoding="utf-8", errors="ignore").read().splitlines():
    if ln.startswith("A idx="):
        cur = {"raw": ln}
        m = re.search(r"actor=0x([0-9A-F]+).*?ps=0x([0-9A-F]+).*?hp=([-\d.]+).*?own_match=(\d).*?dist=([-\d.]+).*?local=(\d).*?tgt=(\d).*?name=(.*)$", ln)
        if m:
            cur.update(actor=m.group(1), ps=m.group(2), hp=float(m.group(3)), own=m.group(4),
                       dist=float(m.group(5)), tgt=int(m.group(7)), name=m.group(8))
        recs.append(cur)
    elif cur is not None and ln.startswith("  AHEX "): cur["ahex"] = ln[7:].strip()
    elif cur is not None and ln.startswith("  PHEX "): cur["phex"] = ln[7:].strip()
    elif cur is not None and ln.startswith("  CHEX "): cur["chex"] = ln[7:].strip()
    elif cur is not None and ln.startswith("  MHEX "): cur["mhex"] = ln[7:].strip()

print("records:", len(recs))
for r in recs:
    print("  tgt=%d %-24s hp=%-5.1f own=%s dist=%.1f" % (r.get("tgt",0), r.get("name",""), r.get("hp",-1), r.get("own","?"), r.get("dist",-1)))

tgt = next((r for r in recs if r.get("tgt") == 1), None)
refs = [r for r in recs if r.get("tgt") == 0 and r.get("name")]
if not tgt:
    print("NO TARGET RECORD"); raise SystemExit
print("\nTARGET:", tgt.get("name"), "hp=%.1f" % tgt["hp"], "refs=%d" % len(refs))

for region, key in (("AHEX","actor"), ("PHEX","ps"), ("CHEX","hc"), ("MHEX","mesh")):
    tb = bytes.fromhex(tgt.get(key.lower(), "")) if tgt.get(key.lower()) else None
    rb = [bytes.fromhex(r.get(key.lower(), "")) for r in refs if r.get(key.lower())]
    if not tb or not rb:
        print("%s: missing" % region); continue
    L = min([len(tb)] + [len(x) for x in rb])
    print("--- %s diffs (target unique, refs agree) ---" % region)
    shown = 0
    for off in range(L):
        vals = {x[off] for x in rb}
        if len(vals) == 1 and tb[off] not in vals:
            print("   +0x%03X target=%02X ref=%02X" % (off, tb[off], list(vals)[0]))
            shown += 1
            if shown >= 12: break
    if shown == 0:
        print("   (none)")
