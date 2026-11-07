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
    o = secoff+i*40; nm = d[o:o+8].rstrip(b"\0").decode("latin1")
    vs, va, rs, rp = struct.unpack_from("<IIII", d, o+8); secs.append((nm, va, vs, rp, rs))
def va2off(va):
    for nm, sva, vs, rp, rs in secs:
        if sva <= va < sva+max(vs, rs):
            return rp+(va-sva)
    return None
# import table
imp_rva, imp_size = struct.unpack_from("<II", d, opt+0x78 if magic == 0x20b else opt+0x68)
imp_off = va2off(imp_rva)
iat = {}
if imp_off:
    off = imp_off
    while True:
        ilt, ts, fc, nameRva, ft = struct.unpack_from("<IIIII", d, off)
        if nameRva == 0 and ft == 0:
            break
        nmb = d[va2off(nameRva):va2off(nameRva)+64].split(b"\0")[0].decode("latin1")
        # thunk
        t = iat.get(fc)
        toff = va2off(ilt) if ilt else va2off(fc)
        k = 0
        iat[fc] = iat.get(fc, {})
        while toff:
            v = struct.unpack_from("<Q", d, toff + k*8)[0]
            if v == 0:
                break
            fn = ""
            if not (v >> 63):
                foff = va2off((v & 0x7fffffff) + 2)
                fn = d[foff:foff+64].split(b"\0")[0].decode("latin1")
            iat[fc][k] = "%s!%s" % (nmb, fn)
            k += 1
        off += 20
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
md.detail = True
nm, sva, vs, rp, rs = [s for s in secs if s[0] == "PAGE"][0]
code = d[rp:rp+vs]
insns = list(md.disasm(code, base+sva))
start = next((i for i, x in enumerate(insns) if x.address-base >= 0xb2f0), 0)
for ins in insns[start:]:
    if ins.address-base > 0xb430:
        break
    s = "%s %s" % (ins.mnemonic, ins.op_str)
    extra = ""
    for op in ins.operands:
        if op.type == capstone.x86.X86_OP_MEM and op.mem.base == capstone.x86.X86_REG_RIP:
            tgt = ins.address + ins.size + op.mem.disp
            # find which IAT thunk contains tgt
            for fc, thunks in iat.items():
                for k, fname in thunks.items():
                    slot = base + fc + k*8
                    if slot == tgt:
                        extra = "   ; " + fname
                        break
    print("0x%x  %-42s%s" % (ins.address-base, s, extra))
