import ctypes, struct, math, sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

k = ctypes.WinDLL("kernel32", use_last_error=True)


class P(ctypes.Structure):
    _fields_ = [("dwSize", ctypes.c_ulong), ("c", ctypes.c_ulong), ("pid", ctypes.c_ulong),
                ("h", ctypes.c_void_p), ("m", ctypes.c_ulong), ("t", ctypes.c_ulong),
                ("pp", ctypes.c_ulong), ("pr", ctypes.c_long), ("f", ctypes.c_ulong),
                ("n", ctypes.c_wchar * 260)]


s = k.CreateToolhelp32Snapshot(2, 0)
pe = P()
pe.dwSize = ctypes.sizeof(pe)
pid = 0
if k.Process32FirstW(s, ctypes.byref(pe)):
    while True:
        if pe.n.lower() == "polygon-win64-shipping.exe":
            pid = pe.pid
            break
        if not k.Process32NextW(s, ctypes.byref(pe)):
            break
k.CloseHandle(s)


def c(fn, a):
    return (0x22 << 16) | (a << 14) | (fn << 2)


BIND, BASE, READ, OFF = c(0x800, 3), c(0x801, 1), c(0x802, 1), c(0x804, 1)
h = k.CreateFileW(r"\\.\PolygonMemory", 0xC0000000, 0, None, 3, 0, None)


def io(code, inb, out):
    r = ctypes.c_ulong(0)
    o = ctypes.create_string_buffer(out or 1)
    ok = k.DeviceIoControl(ctypes.c_void_p(h), code, inb, len(inb), o, out, ctypes.byref(r), None)
    return ok, o.raw


def rd(a, n):
    ok, o = io(READ, struct.pack("<QII", a, n, 0), 16 + n)
    return o[16:16 + n] if ok else None


def rq(a):
    d = rd(a, 8)
    return struct.unpack("<Q", d)[0] if d else None


def rf(a):
    d = rd(a, 4)
    return struct.unpack("<f", d)[0] if d else 0.0


def pos3(addr):
    d = rd(addr + 0x250, 24)
    if not d:
        return None
    return struct.unpack("<3d", d)


io(BIND, struct.pack("<I", pid), 0)
base = struct.unpack("<Q", io(BASE, b"", 8)[1][:8])[0]
o = struct.unpack("<10Q", io(OFF, b"", 80)[1][:80])
gw = rq(base + o[0])
lvl = rq(gw + o[2])
gi = rq(gw + o[3])
lp = rd(gi + o[5], 16)
lpd = struct.unpack("<Q", lp[:8])[0]
localplayer = rq(lpd)
pc = rq(localplayer + o[6])
pawn = rq(pc + 0x338)

lmesh = rq(pawn + 0x318)
lpos = pos3(lmesh) if lmesh else None
print("localpawn=0x%X  mesh(0x318)=0x%X  world=%s" % (pawn, lmesh or 0,
      "(%.1f, %.1f, %.1f)" % lpos if lpos else "NULL"))
print("view angles: pitch(0x678)=%.2f  yaw(0x67C)=%.2f" % (rf(pawn + 0x678), rf(pawn + 0x67C)))

aa = rd(lvl + o[4], 16)
ad, an, am = struct.unpack("<QII", aa[:16])
print("--- nearest 4 characters (mesh world + angle from local mesh pos) ---")
rows = []
for i in range(min(320, an)):
    a = rq(ad + i * 8)
    if not a or a == pawn:
        continue
    ps = rq(a + 0x2B0)
    if not ps:
        continue
    mesh = rq(a + 0x318)
    if not mesh:
        continue
    p = pos3(mesh)
    if not p or not lpos:
        continue
    d = math.sqrt((p[0]-lpos[0])**2 + (p[1]-lpos[1])**2 + (p[2]-lpos[2])**2)
    rows.append((d, i, a, p))
rows.sort()
for d, i, a, p in rows[:4]:
    dx, dy, dz = p[0]-lpos[0], p[1]-lpos[1], p[2]-lpos[2]
    horiz = math.hypot(dx, dy)
    pitch = math.degrees(math.atan2(dz, horiz))
    yaw = math.degrees(math.atan2(dy, dx))
    flag = (rd(a + 0x151, 1) or b"\0")[0]
    print("  a[%d]=0x%X dist=%.0f  target=(%.1f,%.1f,%.1f)  flag=%d" % (i, a, d/100.0, p[0], p[1], p[2], flag))
    print("       -> needed pitch=%.1f yaw=%.1f   (current pitch=%.1f yaw=%.1f)" % (
        pitch, yaw, rf(pawn + 0x678), rf(pawn + 0x67C)))
k.CloseHandle(ctypes.c_void_p(h))
