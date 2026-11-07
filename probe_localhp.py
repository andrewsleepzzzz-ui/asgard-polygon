import ctypes, struct, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
k=ctypes.WinDLL('kernel32',use_last_error=True)
class P(ctypes.Structure):
    _fields_=[('dwSize',ctypes.c_ulong),('c',ctypes.c_ulong),('pid',ctypes.c_ulong),('h',ctypes.c_void_p),('m',ctypes.c_ulong),('t',ctypes.c_ulong),('pp',ctypes.c_ulong),('pr',ctypes.c_long),('f',ctypes.c_ulong),('n',ctypes.c_wchar*260)]
s=k.CreateToolhelp32Snapshot(2,0); pe=P(); pe.dwSize=ctypes.sizeof(pe); pid=0
if k.Process32FirstW(s,ctypes.byref(pe)):
    while True:
        if pe.n.lower()=='polygon-win64-shipping.exe': pid=pe.pid; break
        if not k.Process32NextW(s,ctypes.byref(pe)): break
k.CloseHandle(s)
def c(fn,a): return (0x22<<16)|(a<<14)|(fn<<2)
BIND,BASE,READ,OFF=c(0x800,3),c(0x801,1),c(0x802,1),c(0x804,1)
h=k.CreateFileW(r'\\.\PolygonMemory',0xC0000000,0,None,3,0,None)
def io(code,inb,out):
    r=ctypes.c_ulong(0); o=ctypes.create_string_buffer(out or 1)
    ok=k.DeviceIoControl(ctypes.c_void_p(h),code,inb,len(inb),o,out,ctypes.byref(r),None)
    return ok,o.raw
def rd(a,n):
    ok,o=io(READ,struct.pack('<QII',a,n,0),16+n); return o[16:16+n] if ok else None
def rq(a):
    d=rd(a,8); return struct.unpack('<Q',d)[0] if d else None
io(BIND,struct.pack('<I',pid),0)
base=struct.unpack('<Q',io(BASE,b'',8)[1][:8])[0]
o=struct.unpack('<10Q',io(OFF,b'',80)[1][:80])
gw=rq(base+o[0]); gi=rq(gw+o[3]); lp=rd(gi+o[5],16); lpd=struct.unpack('<Q',lp[:8])[0]
localplayer=rq(lpd); pc=rq(localplayer+o[6]); pawn=rq(pc+0x338)
ps=rq(pawn+0x2B0)
print('pawn=0x%X ps=0x%X'%(pawn,ps))
offs=[0x29C,0x158,0x170,0x174,0x2D8,0x2A4,0x2A8,0x2AC]
for off in offs:
    v=struct.unpack('<f',rd(pawn+off,4) or b'\0'*4)[0]
    i=struct.unpack('<i',rd(pawn+off,4) or b'\0'*4)[0]
    print('pawn+0x%03X float=%-10.2f int=%d'%(off,v,i))
print('--- ps candidates ---')
for off in [0x140,0x144,0x148,0x14C,0x150,0x154]:
    v=struct.unpack('<f',rd(ps+off,4) or b'\0'*4)[0]
    print('ps+0x%03X float=%.2f'%(off,v))
k.CloseHandle(ctypes.c_void_p(h))
