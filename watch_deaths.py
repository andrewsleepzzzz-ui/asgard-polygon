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
A = 0x2000
PS = 0x600

def snap():
    gw = rq(base + o[0])
    if not gw: return {}
    lvl = rq(gw + o[2])
    aa = rd(lvl + o[4], 16)
    if not aa: return {}
    ad, an, am = struct.unpack("<QII", aa[:16])
    out = {}
    for i in range(min(320, an)):
        a = rq(ad + i*8)
        if not a: continue
        ps = rq(a + 0x2B0)
        if not ps: continue
        da = rd(a, A)
        dp = rd(ps, PS) if 0x10000 <= ps <= 0x7FFFFFFFFFFF else None
        if not da: continue
        hp = struct.unpack_from("<f", da, 0x29C)[0]
        own = struct.unpack_from("<Q", dp, 0x308)[0] if dp else 0
        out[a] = (hp, own, da, dp)
    return out

print("WATCH: 每秒全量快照，谁死了就打差异（60 秒窗口）", flush=True)
prev = snap()
print("初始角色数:", len(prev), flush=True)
for t in range(60):
    time.sleep(1)
    cur = snap()
    for a, (hp, own, da, dp) in cur.items():
        if a not in prev: continue
        php, pown, pda, pdp = prev[a]
        died = (php > 0 and hp <= 0) or (pown == a and own != a)
        if not died: continue
        print("=== DIED a=0x%X  hp %.1f -> %.1f  own 0x%X -> 0x%X ===" % (a, php, hp, pown, own), flush=True)
        for off in range(0, A - 1):
            if pda[off] != da[off]:
                print("   actor+0x%03X %02X -> %02X" % (off, pda[off], da[off]), flush=True)
        if pdp and dp:
            for off in range(0, PS - 1):
                if pdp[off] != dp[off]:
                    print("   ps+0x%03X %02X -> %02X" % (off, pdp[off], dp[off]), flush=True)
    prev = cur
k.CloseHandle(ctypes.c_void_p(h))
