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
    return raw[: (num-1)*2].decode("utf-16-le", "ignore")

io(BIND, struct.pack("<I", pid), 0)
base = struct.unpack("<Q", io(BASE, b"", 8)[1][:8])[0]
o = struct.unpack("<10Q", io(OFF, b"", 80)[1][:80])
gw = rq(base + o[0]); lvl = rq(gw + o[2]); gi = rq(gw + o[3])
lp = rd(gi + o[5], 16); lpd = struct.unpack("<Q", lp[:8])[0]
localplayer = rq(lpd); pc = rq(localplayer + o[6]); lpawn = rq(pc + 0x338)

# find offset in local pawn that stores the local PlayerController
buf = rd(lpawn, 0x1000)
ctrl_off = None
for off in range(0, 0x1000 - 8, 8):
    if struct.unpack_from("<Q", buf, off)[0] == pc:
        ctrl_off = off
        print("localpawn+0x%X == PlayerController(0x%X)" % (off, pc), flush=True)
if ctrl_off is None:
    print("controller offset not found", flush=True)
    k.CloseHandle(ctypes.c_void_p(h)); raise SystemExit

aa = rd(lvl + o[4], 16); ad, an, am = struct.unpack("<QII", aa[:16])
print("--- named actors: pawn+0x%X (0 = unpossessed/dead) ---" % ctrl_off, flush=True)
for i in range(min(320, an)):
    a = rq(ad + i*8)
    if not a: continue
    ps = rq(a + 0x2B0)
    if not ps: continue
    nm = fstring(ps + 0x388)
    if not nm or nm.strip() == "\ucb00": continue
    ctl = rq(a + ctrl_off) or 0
    hp = struct.unpack("<f", rd(a + 0x29C, 4) or b"\0"*4)[0]
    print("  %-26s hp=%-5.1f pawn_controller=0x%-10X %s" % (nm, hp, ctl, "DEAD?" if ctl == 0 else ""), flush=True)
k.CloseHandle(ctypes.c_void_p(h))
