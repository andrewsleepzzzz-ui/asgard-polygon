import ctypes, struct, sys
log = open(r"C:\gdrv_probe.log", "w", encoding="utf-8")
def p(s):
    log.write(s + "\n"); log.flush()
k = ctypes.WinDLL("kernel32", use_last_error=True)
h = k.CreateFileW(r"\\.\GIOV3", 0xC0000000, 0, None, 3, 0, None)
p("open \\\\.\\GIOV3 -> %s err %d" % (h, ctypes.get_last_error()))
if h in (0xffffffffffffffff, -1):
    h = k.CreateFileW(r"\\.\GIOV3", 0x80000000, 0, None, 3, 0, None)
    p("open read-only -> %s err %d" % (h, ctypes.get_last_error()))
if h in (0xffffffffffffffff, -1):
    p("FAILED to open device"); log.close(); sys.exit(1)

codes = [0xC3502000, 0xC3502004, 0xC3502008, 0xC3502400, 0xC3502440, 0xC3502014, 0xC3502019, 0xC3502580, 0xC3502584]
for code in codes:
    for insz in (8, 16, 24, 32):
        inp = ctypes.create_string_buffer(insz)
        # physical addr 0, size 0x1000
        struct.pack_into("<Q", inp, 0, 0) if insz >= 8 else None
        if insz >= 16:
            struct.pack_into("<I", inp, 8, 0x1000)
        out = ctypes.create_string_buffer(0x40)
        ret = ctypes.c_ulong(0)
        ok = k.DeviceIoControl(ctypes.c_void_p(h), code, inp, insz, out, 0x40, ctypes.byref(ret), None)
        err = ctypes.get_last_error()
        p("code 0x%08X in=%d -> ok=%s err=%d ret=%d out=%s" %
          (code, insz, bool(ok), err, ret.value, out.raw[:min(ret.value, 0x40)].hex()))
k.CloseHandle(ctypes.c_void_p(h))
p("done")
log.close()
