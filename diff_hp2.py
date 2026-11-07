import ctypes, struct, time

k = ctypes.WinDLL("kernel32", use_last_error=True)
class P(ctypes.Structure):
    _fields_ = [("dwSize", ctypes.c_ulong), ("c", ctypes.c_ulong), ("pid", ctypes.c_ulong),
                ("h", ctypes.c_void_p), ("m", ctypes.c_ulong), ("t", ctypes.c_ulong),
                ("pp", ctypes.c_ulong), ("pr", ctypes.c_long), ("f", ctypes.c_ulong),
                ("n", ctypes.c_wchar * 260)]
s = k.CreateToolhelp32Snapshot(2, 0); pe = P(); pe.dwSize = ctypes.sizeof(pe); pid = 0
if k.Process32FirstW(s, ctypes.byref(pe)):
    while True:
        if pe.n.lower() == "polygon-win64-shipping.exe": pid = pe.pid; break
        if not k.Process32NextW(s, ctypes.byref(pe)): break
k.CloseHandle(s)

def c(fn, a): return (0x22 << 16) | (a << 14) | (fn << 2)
BIND, BASE, READ, OFF = c(0x800,3), c(0x801,1), c(0x802,1), c(0x804,1)
h = k.CreateFileW(r"\\.\PolygonMemory", 0xC0000000, 0, None, 3, 0, None)
def io(code, inb, out):
    r = ctypes.c_ulong(0); o = ctypes.create_string_buffer(out or 1)
    ok = k.DeviceIoControl(ctypes.c_void_p(h), code, inb, len(inb), o, out, ctypes.byref(r), None)
    return ok, o.raw
def rd(a, n):
    ok, o = io(READ, struct.pack("<QII", a, n, 0), 16 + n)
    return o[16:16+n] if ok else None
def rq(a):
    d = rd(a, 8); return struct.unpack("<Q", d)[0] if d else None

io(BIND, struct.pack("<I", pid), 0)
base = struct.unpack("<Q", io(BASE, b"", 8)[1][:8])[0]
o = struct.unpack("<10Q", io(OFF, b"", 80)[1][:80])

def actors():
    gw = rq(base + o[0])
    if not gw: return []
    lvl = rq(gw + o[2]); aa = rd(lvl + o[4], 16)
    if not aa: return []
    ad, an, am = struct.unpack("<QII", aa[:16])
    out = []
    for i in range(min(300, an)):
        a = rq(ad + i*8)
        if not a: continue
        ps = rq(a + 0x2B0)
        if not ps: continue
        out.append((i, a))
    return out

def snap():
    d = {}
    for i, a in actors():
        ad = rd(a, 0x1000)
        hc = rq(a + 0x730)
        hd = rd(hc, 0x300) if hc and 0x10000 <= hc <= 0x7FFFFFFFFFFF else None
        d[a] = (i, ad, hd)
    return d

print("PHASE1: 现在开一枪打中敌人（人别动），6 秒后对比", flush=True)
a1 = snap()
time.sleep(6)
a2 = snap()
print("actors: %d -> %d" % (len(a1), len(a2)), flush=True)
for addr in a1:
    if addr not in a2: continue
    i, d1, h1 = a1[addr]
    _, d2, h2 = a2[addr]
    if not d1 or not d2: continue
    for tag, x1, x2 in (("A", d1, d2), ("H", h1, h2)):
        if not x1 or not x2: continue
        n = min(len(x1), len(x2))
        for off in range(0, n - 4, 4):
            v1 = struct.unpack_from("<I", x1, off)[0]
            v2 = struct.unpack_from("<I", x2, off)[0]
            if v1 == v2: continue
            f1 = struct.unpack("<f", struct.pack("<I", v1))[0]
            f2 = struct.unpack("<f", struct.pack("<I", v2))[0]
            i1 = struct.unpack("<i", struct.pack("<I", v1))[0]
            i2 = struct.unpack("<i", struct.pack("<I", v2))[0]
            okf = all(-1e6 < z < 1e6 and z == z for z in (f1, f2))
            print("actor[%d] %s+0x%03X  int %d->%d  float %s" % (
                i, tag, off, i1, i2, ("%.2f->%.2f" % (f1, f2)) if okf else "nan"), flush=True)
k.CloseHandle(ctypes.c_void_p(h))
