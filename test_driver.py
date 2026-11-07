import ctypes, struct

k = ctypes.WinDLL("kernel32", use_last_error=True)

class PROCESSENTRY32W(ctypes.Structure):
    _fields_ = [("dwSize", ctypes.c_ulong), ("cntUsage", ctypes.c_ulong),
                ("th32ProcessID", ctypes.c_ulong), ("th32DefaultHeapID", ctypes.c_void_p),
                ("th32ModuleID", ctypes.c_ulong), ("cntThreads", ctypes.c_ulong),
                ("th32ParentProcessID", ctypes.c_ulong), ("pcPriClassBase", ctypes.c_long),
                ("dwFlags", ctypes.c_ulong), ("szExeFile", ctypes.c_wchar * 260)]
snap = k.CreateToolhelp32Snapshot(0x2, 0)
pe = PROCESSENTRY32W(); pe.dwSize = ctypes.sizeof(pe)
pid = 0
if k.Process32FirstW(snap, ctypes.byref(pe)):
    while True:
        if pe.szExeFile.lower() == "polygon-win64-shipping.exe":
            pid = pe.th32ProcessID; break
        if not k.Process32NextW(snap, ctypes.byref(pe)): break
k.CloseHandle(snap)
print("pid", pid)

def ctl(fn, access): return (0x22 << 16) | (access << 14) | (fn << 2) | 0
BIND, BASE, READ, OFF = ctl(0x800,3), ctl(0x801,1), ctl(0x802,1), ctl(0x804,1)

h = k.CreateFileW(r"\\.\PolygonMemory", 0xC0000000, 0, None, 3, 0, None)
print("handle", h, "err", ctypes.get_last_error())

def ioctl(code, inbuf, outsize, insize=None):
    ret = ctypes.c_ulong(0)
    out = ctypes.create_string_buffer(outsize if outsize else 1)
    ok = k.DeviceIoControl(ctypes.c_void_p(h), code, inbuf, insize if insize is not None else len(inbuf),
                           out, outsize, ctypes.byref(ret), None)
    return ok, ret.value, out.raw

if h not in (0xffffffffffffffff, -1):
    print("BIND", ioctl(BIND, struct.pack("<I", pid), 0)[:2])
    ok, r, o = ioctl(BASE, b"", 8)
    base = struct.unpack("<Q", o[:8])[0]
    print("BASE", ok, "base=0x%X" % base)
    ok, r, o = ioctl(OFF, b"", 80)
    offs = struct.unpack("<10Q", o[:80])
    print("OFF", ok, "gworld=0x%X" % offs[0])

    # --- exactly like the cheat: in=16, out=16+n, same buffer ---
    n = 8
    buf = struct.pack("<QII", base + offs[0], n, 0) + b"\0" * n   # 16 + n total
    ok, r, o = ioctl(READ, buf, 16 + n, insize=16)
    print("READ(cheat-style) ok=%s ret=%d err=%d" % (ok, r, ctypes.get_last_error()))
    print("  value=0x%X" % struct.unpack("<Q", o[16:24])[0])

    # --- python-style: in=16+n ---
    ok, r, o = ioctl(READ, buf, 16 + n, insize=16 + n)
    print("READ(python-style) ok=%s ret=%d err=%d" % (ok, r, ctypes.get_last_error()))
    print("  value=0x%X" % struct.unpack("<Q", o[16:24])[0])
    k.CloseHandle(ctypes.c_void_p(h))
