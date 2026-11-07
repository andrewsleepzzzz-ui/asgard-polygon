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
def rd(addr, n):
    ok, o = io(READ, struct.pack("<QII", addr, n, 0), 16 + n)
    return o[16:16+n] if ok else None
def rq(a):
    d = rd(a, 8); return struct.unpack("<Q", d)[0] if d else None

print("pid", pid, "bind", io(BIND, struct.pack("<I", pid), 0)[0])
base = struct.unpack("<Q", io(BASE, b"", 8)[1][:8])[0]
o = struct.unpack("<10Q", io(OFF, b"", 80)[1][:80])
print("base=0x%X" % base)

def show(name, val, off=None):
    print("%-24s = 0x%X" % (name, val) if val is not None else "%s = FAIL" % name)

gw = rq(base + o[0]); show("GWorld (0x%X)" % o[0], gw)
lvl = rq(gw + o[2]); show("PersistentLevel (+0x%X)" % o[2], lvl)
gi  = rq(gw + o[3]); show("OwningGameInstance (+0x%X)" % o[3], gi)
if gi:
    lp = rd(gi + o[5], 16)
    if lp:
        data, num, mx = struct.unpack("<QII", lp[:16])
        print("LocalPlayers @gi+0x%X: data=0x%X num=%d max=%d" % (o[5], data, num, mx))
        if data:
            loc = rq(data); show("LocalPlayer", loc)
            if loc:
                pc = rq(loc + o[6]); show("PlayerController (+0x%X)" % o[6], pc)
                if pc:
                    pawn = rq(pc + 0x338); show("Pawn (+0x338)", pawn)
                    cam = rq(pc + o[8]); show("CameraManager (+0x%X)" % o[8], cam)
                    if cam:
                        print("  camera view bytes:", (rd(cam + o[9], 16) or b"").hex())
if lvl:
    aa = rd(lvl + o[4], 16)
    if aa:
        ad, an, am = struct.unpack("<QII", aa[:16])
        print("Actors @lvl+0x%X: data=0x%X num=%d max=%d" % (o[4], ad, an, am))
        if ad and an:
            for i in range(min(3, an)):
                a = rq(ad + i*8)
                print("  actor[%d] = 0x%X" % (i, a))
k.CloseHandle(ctypes.c_void_p(h))
