import ctypes, struct, time, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

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
gw = rq(base + o[0]); gi = rq(gw + o[3])
lp = rd(gi + o[5], 16); lpd = struct.unpack("<Q", lp[:8])[0]
localplayer = rq(lpd); pc = rq(localplayer + o[6]); pawn = rq(pc + 0x338)
ps = rq(pawn + 0x2B0)
hc = rq(pawn + 0x730)
print("pawn=0x%X ps=0x%X hc=0x%X" % (pawn, ps, hc), flush=True)

SZ = 0x2000
def regions():
    return [("pawn", pawn, SZ), ("ps", ps, 0x600), ("hc", hc, 0x400)]

snap0 = {}
for tag, addr, size in regions():
    if not addr or not (0x10000 <= addr <= 0x7FFFFFFFFFFF): continue
    d = rd(addr, size)
    if d: snap0[tag] = d

print("采样完成 -> 现在去挨一枪/掉血，12 秒后再采一次", flush=True)
time.sleep(12)

for tag, addr, size in regions():
    if tag not in snap0: continue
    d = rd(addr, size)
    if not d: continue
    old = snap0[tag]
    L = min(len(old), len(d))
    hits = 0
    for off in range(0, L - 4, 4):
        f1 = struct.unpack_from("<f", old, off)[0]
        f2 = struct.unpack_from("<f", d, off)[0]
        if not (-1e6 < f1 < 1e6 and -1e6 < f2 < 1e6): continue
        if f2 < f1 - 0.05 and 0.0 <= f2 <= 200.0 and (f1 - f2) >= 0.5:
            print("  %s+0x%03X  %.2f -> %.2f" % (tag, off, f1, f2), flush=True)
            hits += 1
            if hits >= 15: break
    if hits == 0:
        print("  %s: no decreasing float" % tag, flush=True)
k.CloseHandle(ctypes.c_void_p(h))
