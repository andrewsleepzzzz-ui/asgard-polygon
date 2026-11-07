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
localplayer = rq(lpd); pc = rq(localplayer + o[6]); pawn = rq(pc + 0x338)

print("localpawn=0x%X" % pawn)
for tag, addr, size in (("PAWN", pawn, 0x1000), ("HC", rq(pawn + 0x730), 0x400)):
    if not addr or not (0x10000 <= addr <= 0x7FFFFFFFFFFF):
        print(tag, "invalid"); continue
    d = rd(addr, size)
    if not d:
        print(tag, "read fail"); continue
    print("=== %s 0x%X ===" % (tag, addr))
    for off in range(0, size - 4, 4):
        f = struct.unpack_from("<f", d, off)[0]
        iv = struct.unpack_from("<i", d, off)[0]
        if f != f or f in (float("inf"), float("-inf")):
            continue
        if 55.0 <= f <= 65.0 or (abs(f - round(f)) < 0.01 and 1.0 <= f <= 60.0):
            print("  +0x%03X float=%g" % (off, f))
        if 55 <= iv <= 65:
            print("  +0x%03X int=%d" % (off, iv))
print("--- also look for 60 exactly as int in pawn 0..0x2000 ---")
d = rd(pawn, 0x2000)
if d:
    for off in range(0, 0x2000 - 4, 4):
        iv = struct.unpack_from("<i", d, off)[0]
        if iv == 60:
            print("  pawn+0x%03X int=60" % off)
k.CloseHandle(ctypes.c_void_p(h))
