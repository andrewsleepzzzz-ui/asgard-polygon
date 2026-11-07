#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import struct, capstone
PATH = r"C:\Windows\System32\drivers\gdrv3.sys"
d = open(PATH, "rb").read()
e = struct.unpack_from("<I", d, 0x3C)[0]; coff = e+4
nsec = struct.unpack_from("<H", d, coff+2)[0]; opt = coff+20
magic = struct.unpack_from("<H", d, opt)[0]
base = struct.unpack_from("<Q", d, opt+24)[0] if magic == 0x20b else struct.unpack_from("<I", d, opt+28)[0]
secoff = opt + struct.unpack_from("<H", d, coff+16)[0]
secs = []
for i in range(nsec):
    o = secoff+i*40
    nm = d[o:o+8].rstrip(b"\0").decode("latin1")
    vs, va, rs, rp = struct.unpack_from("<IIII", d, o+8)
    secs.append((nm, va, vs, rp, rs))
    print("SEC %-8s VA=0x%x VS=0x%x RAW=0x%x" % (nm, base+va, vs, rp))
def va2off(va):
    for nm, sva, vs, rp, rs in secs:
        if sva <= va < sva+max(vs, rs):
            return rp+(va-sva)
    return None
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
md.detail = True
# disassemble text around the IOCTL constant immediates (file off ~0x6000-0x7200)
txt = [s for s in secs if s[0] == ".text"] or secs
nm, sva, vs, rp, rs = txt[0]
code = d[rp:rp+max(vs, rs)]
insns = list(md.disasm(code, base+sva))
# print window around cmp 0xC350 immediates
idx = [i for i, ins in enumerate(insns) if ins.mnemonic.startswith("cmp") and "0xc350" in ins.op_str.lower()]
print("cmp-with-C350 count:", len(idx))
for i in idx:
    lo = max(0, i-2); hi = min(len(insns), i+8)
    print("----")
    for ins in insns[lo:hi]:
        print("  0x%x  %s %s" % (ins.address-base, ins.mnemonic, ins.op_str))
