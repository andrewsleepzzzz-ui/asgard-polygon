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
print("pid", pid, "bind", io(BIND, struct.pack("<I", pid), 0)[0])
base = struct.unpack("<Q", io(BASE, b"", 8)[1][:8])[0]
offrva = struct.unpack("<10Q", io(OFF, b"", 80)[1][:80])
GWORLD_RVA = offrva[0]
print("base=0x%X gworld_rva=0x%X" % (base, GWORLD_RVA))

def rd(addr, n):
    ok, o = io(READ, struct.pack("<QII", addr, n, 0), 16 + n)
    return o[16:16+n] if ok else None

def rq(addr):
    d = rd(addr, 8)
    return struct.unpack("<Q", d)[0] if d else None

world = rq(base + GWORLD_RVA)
print("UWorld = 0x%X" % world)

# dump UWorld first 0x400 bytes and look for pointer-looking values
dump = rd(world, 0x400)
print("dump len", len(dump) if dump else None)
pv = []
for i in range(0, len(dump) - 8, 8):
    v = struct.unpack_from("<Q", dump, i)[0]
    if 0x10000 <= v <= 0x7FFFFFFFFFFF:
        pv.append((i, v))
print("pointer-like fields in UWorld:")
for i, v in pv[:60]:
    print("  +0x%03X = 0x%X" % (i, v))

# for each candidate, check if it looks like a ULevel (Actors TArray somewhere in first 0x400)
print("--- level candidates ---")
for i, v in pv:
    sub = rd(v, 0x400)
    if not sub: continue
    for j in range(0, 0x400 - 16, 8):
        data = struct.unpack_from("<Q", sub, j)[0]
        num = struct.unpack_from("<I", sub, j+8)[0]
        mx = struct.unpack_from("<I", sub, j+12)[0]
        if 0x10000 <= data <= 0x7FFFFFFFFFFF and 0 < num <= 0x5000 and num <= mx <= 0x10000 and (mx - num) < 0x1000:
            print("  UWorld+0x%03X -> 0x%X  TArray@+0x%03X data=0x%X num=%d max=%d" % (i, v, j, data, num, mx))
k.CloseHandle(ctypes.c_void_p(h))
