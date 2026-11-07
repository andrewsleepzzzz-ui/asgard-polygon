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

print("live health: 每 0.5s 打印本地玩家; 去挨枪看哪个值掉", flush=True)
for n in range(120):
    gw = rq(base + o[0])
    if not gw: time.sleep(0.5); continue
    gi = rq(gw + o[3])
    if not gi: time.sleep(0.5); continue
    lp = rd(gi + o[5], 16)
    if not lp: time.sleep(0.5); continue
    lpd = struct.unpack("<Q", lp[:8])[0]
    localplayer = rq(lpd) if lpd else 0
    if not localplayer: time.sleep(0.5); continue
    pc = rq(localplayer + o[6])
    pawn = rq(pc + 0x338) if pc else 0
    if not pawn: time.sleep(0.5); continue
    hc = rq(pawn + 0x730)
    vals = []
    if hc and 0x10000 <= hc <= 0x7FFFFFFFFFFF:
        d = rd(hc + 0x150, 0x40)
        if d:
            for off in range(0, 0x40, 4):
                f = struct.unpack_from("<f", d, off)[0]
                if 0.0 <= f <= 500.0:
                    vals.append("hc+0x%X=%.1f" % (0x150 + off, f))
    ap = rd(pawn + 0x660, 0x30)
    if ap:
        for off in range(0, 0x30, 4):
            f = struct.unpack_from("<f", ap, off)[0]
            if 0.0 <= f <= 500.0:
                vals.append("pawn+0x%X=%.1f" % (0x660 + off, f))
    print("t=%d pawn=0x%X hc=0x%X  %s" % (n, pawn, hc or 0, " ".join(vals)), flush=True)
    time.sleep(0.5)
k.CloseHandle(ctypes.c_void_p(h))
