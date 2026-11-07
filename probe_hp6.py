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

io(BIND, struct.pack("<I", pid), 0)
base = struct.unpack("<Q", io(BASE, b"", 8)[1][:8])[0]
o = struct.unpack("<10Q", io(OFF, b"", 80)[1][:80])
gw = rq(base + o[0]); lvl = rq(gw + o[2])
aa = rd(lvl + o[4], 16); ad, an, am = struct.unpack("<QII", aa[:16])

SIZE = 0x2000
dumps = []
names = []
for i in range(min(300, an)):
    a = rq(ad + i*8)
    if not a: continue
    ps = rq(a + 0x2B0)
    mesh = rq(a + 0x318)
    if not (ps and mesh): continue
    d = rd(a, SIZE)
    if d:
        dumps.append(d)
        names.append(i)

n = len(dumps)
print("char actors:", n, flush=True)
print("--- offsets where some actor has 1..60 and not all do ---", flush=True)
hits = 0
for off in range(0, SIZE - 4, 4):
    vals = [struct.unpack_from("<f", d, off)[0] for d in dumps]
    good = [v for v in vals if 1.0 <= v <= 60.0]
    if len(good) == 0 or len(good) == n:
        continue
    hits += 1
    print("+0x%03X n=%d vals=%s" % (off, len(good), [round(v, 1) for v in good[:10]]), flush=True)
    if hits >= 18:
        break
k.CloseHandle(ctypes.c_void_p(h))
