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
print("actors num=%d" % an)

# find a BP_PG_Game_Character actor via the driver (name resolution already proven;
# just probe each actor's component fields)
for i in range(an):
    a = rq(ad + i*8)
    if not a: continue
    root = rq(a + 0x198)
    ps   = rq(a + 0x2B0)
    hc   = rq(a + 0x730)
    mesh = rq(a + 0x318)
    if root or ps or mesh:
        print("actor[%d]=0x%X root(+0x198)=0x%X ps(+0x2B0)=0x%X hc(+0x730)=0x%X mesh(+0x318)=0x%X" %
              (i, a, root or 0, ps or 0, hc or 0, mesh or 0))
    if i > 40: break
k.CloseHandle(ctypes.c_void_p(h))
