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
gw = rq(base + o[0]); gi = rq(gw + o[3])
lp = rd(gi + o[5], 16); lpd = struct.unpack("<Q", lp[:8])[0]
localplayer = rq(lpd)
pc = rq(localplayer + o[6])
pawn = rq(pc + 0x338)
print("Controller=0x%X Pawn=0x%X" % (pc, pawn))

def f3(a):
    d = rd(a, 12); return struct.unpack("<3f", d) if d else None

print("--- Controller + 0x2B0..0x320 (look for rotation) ---")
for off in range(0x2A0, 0x340, 4):
    v = f3(pc + off)
    if v and -90 <= v[0] <= 90 and 0 <= v[1] <= 360 and -180 <= v[2] <= 180 and (v[0] or v[1]):
        print("  pc+0x%X = (%.2f, %.2f, %.2f)" % (off, v[0], v[1], v[2]))

print("--- Pawn + 0x640..0x700 (current aimbot write target 0x674) ---")
for off in range(0x640, 0x700, 4):
    v = f3(pawn + off)
    if v and -90 <= v[0] <= 90 and 0 <= v[1] <= 360:
        print("  pawn+0x%X = (%.2f, %.2f, %.2f)" % (off, v[0], v[1], v[2]))

print("--- camera view (from PlayerCameraManager+0x22C0) ---")
cam = rq(pc + o[8])
cv = rd(cam + o[9], 0x40)
if cv:
    print("  cam bytes:", cv[:0x30].hex())
k.CloseHandle(ctypes.c_void_p(h))
