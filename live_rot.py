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

def targets():
    gw = rq(base + o[0])
    if not gw: return None, None
    gi = rq(gw + o[3]); lp = rd(gi + o[5], 16)
    if not lp: return None, None
    lpd = struct.unpack("<Q", lp[:8])[0]; localplayer = rq(lpd)
    if not localplayer: return None, None
    pc = rq(localplayer + o[6]); pawn = rq(pc + 0x338) if pc else 0
    return pc, pawn

def snap(addr, size):
    d = rd(addr, size)
    if not d: return None
    return [struct.unpack_from("<f", d, j)[0] for j in range(0, size - 4, 4)]

pc, pawn = targets()
print("pc=0x%X pawn=0x%X" % (pc or 0, pawn or 0), flush=True)
if not pc:
    k.CloseHandle(ctypes.c_void_p(h)); raise SystemExit

prev_pc = snap(pc, 0x800)
prev_pawn = snap(pawn, 0x1000)
print("现在请【慢慢左右上下转视角】5 秒...", flush=True)
time.sleep(1)
for it in range(10):
    time.sleep(0.4)
    cur_pc = snap(pc, 0x800)
    cur_pawn = snap(pawn, 0x1000)
    for tag, a, b in (("PC", prev_pc, cur_pc), ("PAWN", prev_pawn, cur_pawn)):
        if not a or not b: continue
        for i in range(min(len(a), len(b))):
            off = i * 4
            if a[i] == b[i]: continue
            f1, f2 = a[i], b[i]
            if not (-100000 < f1 < 100000 and -100000 < f2 < 100000): continue
            if abs(f1 - f2) < 0.0001: continue
            print("[%d] %s+0x%03X  %.3f -> %.3f" % (it, tag, off, f1, f2), flush=True)
    prev_pc, prev_pawn = cur_pc, cur_pawn
k.CloseHandle(ctypes.c_void_p(h))
