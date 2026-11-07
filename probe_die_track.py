import ctypes, struct, math, time

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
gw = rq(base + o[0]); lvl = rq(gw + o[2]); gi = rq(gw + o[3])
lp = rd(gi + o[5], 16); lpd = struct.unpack("<Q", lp[:8])[0]
localplayer = rq(lpd); pc = rq(localplayer + o[6]); lpawn = rq(pc + 0x338)
lmesh = rq(lpawn + 0x318)
lt = struct.unpack("<3d", rd(lmesh + 0x250, 24))

aa = rd(lvl + o[4], 16); ad, an, am = struct.unpack("<QII", aa[:16])
best = None
for i in range(min(300, an)):
    a = rq(ad + i*8)
    if not a or a == lpawn: continue
    ps = rq(a + 0x2B0); mesh = rq(a + 0x318)
    if not (ps and mesh): continue
    t = rd(mesh + 0x250, 24)
    if not t: continue
    x, y, z = struct.unpack("<3d", t)
    d = math.sqrt((x-lt[0])**2 + (y-lt[1])**2 + (z-lt[2])**2) / 100.0
    if best is None or d < best[0]:
        best = (d, i, a, ps)

if not best:
    print("no target"); k.CloseHandle(ctypes.c_void_p(h)); raise SystemExit
d, idx, act, ps = best
print("TRACK a[%d]=0x%X ps=0x%X d=%.1f  -> 现在去打死它" % (idx, act, ps, d), flush=True)

SZ = 0x2000
base_dump = rd(act, SZ)
ones0 = {off for off in range(SZ) if base_dump[off] == 1}
prev = base_dump
for it in range(45):
    time.sleep(1)
    d2 = rd(act, SZ)
    if not d2: print("read lost"); break
    ones1 = {off for off in range(SZ) if d2[off] == 1}
    newly = sorted(ones1 - ones0)
    hp = struct.unpack("<f", rd(act + 0x29C, 4) or b"\0\0\0\0")[0]
    if newly or it % 5 == 0:
        print("t=%ds hp=%.1f newly_set_1=%s" % (it, hp, ["+0x%X" % x for x in newly[:12]]), flush=True)
        ones0 = ones1
    prev = d2
k.CloseHandle(ctypes.c_void_p(h))
