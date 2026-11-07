import ctypes, struct, sys, time

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

def char_actors():
    gw = rq(base + o[0])
    if not gw: return []
    lvl = rq(gw + o[2]); aa = rd(lvl + o[4], 16)
    if not aa: return []
    ad, an, am = struct.unpack("<QII", aa[:16])
    out = []
    for i in range(min(200, an)):
        a = rq(ad + i*8)
        if not a: continue
        ps = rq(a + 0x2B0)
        if not ps: continue
        out.append((i, a, ps))
    return out

def snap():
    d = {}
    for i, a, ps in char_actors():
        ad = rd(a, 0x800)
        hc = rq(a + 0x730)
        hd = rd(hc, 0x300) if hc and 0x10000 <= hc <= 0x7FFFFFFFFFFF else None
        d[a] = (i, ad, hd)
    return d

print("PHASE1 ... 请现在去打一个敌人，然后等 20 秒", flush=True)
a1 = snap()
print("captured %d actors, waiting 20s..." % len(a1), flush=True)
time.sleep(20)
a2 = snap()
print("diffing...", flush=True)
for addr in a1:
    if addr not in a2: continue
    i, d1, h1 = a1[addr]
    _, d2, h2 = a2[addr]
    if not d1 or not d2: continue
    ch = [(off, d1[off], d2[off]) for off in range(min(len(d1), len(d2))) if d1[off] != d2[off]]
    chh = []
    if h1 and h2:
        chh = [(off, h1[off], h2[off]) for off in range(min(len(h1), len(h2))) if h1[off] != h2[off]]
    if ch or chh:
        print("actor[%d]=0x%X  actor_changes=%d hc_changes=%d" % (i, addr, len(ch), len(chh)), flush=True)
        for off, b1, b2 in ch[:12]:
            print("   actor+0x%03X  %02X -> %02X" % (off, b1, b2), flush=True)
        for off, b1, b2 in chh[:12]:
            print("   hc+0x%03X  %02X -> %02X" % (off, b1, b2), flush=True)
k.CloseHandle(ctypes.c_void_p(h))
