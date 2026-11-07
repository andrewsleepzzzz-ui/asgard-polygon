import ctypes, struct

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

def fstring(addr):
    hdr = rd(addr, 16)
    if not hdr: return ""
    ptr, num, mx = struct.unpack("<QII", hdr[:16])
    if not (0x10000 <= ptr <= 0x7FFFFFFFFFFF) or num <= 1 or num > 64: return ""
    raw = rd(ptr, num * 2)
    if not raw: return ""
    try:
        return raw[: (num-1)*2].decode("utf-16-le", "ignore")
    except Exception:
        return ""

io(BIND, struct.pack("<I", pid), 0)
base = struct.unpack("<Q", io(BASE, b"", 8)[1][:8])[0]
o = struct.unpack("<10Q", io(OFF, b"", 80)[1][:80])
gw = rq(base + o[0]); lvl = rq(gw + o[2])
aa = rd(lvl + o[4], 16); ad, an, am = struct.unpack("<QII", aa[:16])

dead = []
alive = []
for i in range(min(320, an)):
    a = rq(ad + i*8)
    if not a: continue
    ps = rq(a + 0x2B0)
    if not ps: continue
    hp = struct.unpack("<f", rd(a + 0x29C, 4) or b"\0\0\0\0")[0]
    own = rq(ps + 0x308) or 0
    nm = fstring(ps + 0x388)
    d = rd(a, 0x2000)
    rec = (i, a, ps, hp, own, nm, d)
    if hp <= 0.0:
        dead.append(rec)
    else:
        alive.append(rec)

print("alive=%d dead=%d" % (len(alive), len(dead)), flush=True)
for rec in alive[:12]:
    i, a, ps, hp, own, nm, _ = rec
    print("ALIVE a[%d]=0x%X hp=%.1f own_match=%s name=%s" % (i, a, hp, own == a, nm), flush=True)
for rec in dead[:12]:
    i, a, ps, hp, own, nm, _ = rec
    print("DEAD  a[%d]=0x%X hp=%.1f own_match=%s name=%s" % (i, a, hp, own == a, nm), flush=True)

if dead and alive:
    d0 = dead[0][6]; a0 = alive[0][6]
    if d0 and a0:
        print("--- bytes that are 0/1 in dead but not in alive (actor) ---", flush=True)
        cnt = 0
        for off in range(0x2000):
            if d0[off] <= 1 and a0[off] > 1:
                print("  actor+0x%03X dead=%d alive=%d" % (off, d0[off], a0[off]), flush=True)
                cnt += 1
                if cnt >= 20: break
k.CloseHandle(ctypes.c_void_p(h))
