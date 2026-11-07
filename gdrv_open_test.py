import ctypes, os
log = open(r"F:\dsh\32\Asgard_Polygon-main\gdrv_open.log", "w", encoding="utf-8")
try:
    log.write("admin=%s\n" % bool(ctypes.windll.shell32.IsUserAnAdmin()))
    k = ctypes.WinDLL("kernel32", use_last_error=True)
    for path in (r"\\.\GIOV3", r"\\.\gdrv3"):
        h = k.CreateFileW(path, 0xC0000000, 0, None, 3, 0, None)
        err = ctypes.get_last_error()
        log.write("%s -> %s err=%d\n" % (path, h, err))
        if h not in (0xffffffffffffffff, -1):
            k.CloseHandle(ctypes.c_void_p(h))
finally:
    log.close()
