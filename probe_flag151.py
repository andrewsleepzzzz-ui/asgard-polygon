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
def fs(addr):
    hd=rd(addr,16)
    if not hd: return ''
    ptr,num,mx=struct.unpack('<QII',hd[:16])
    if not (0x10000<=ptr<=0x7fffffffffff) or num<=1 or num>64: return ''
    raw=rd(ptr,num*2)
    return raw[:(num-1)*2].decode('utf-16-le','ignore') if raw else ''
io(BIND,struct.pack('<I',pid),0)
base=struct.unpack('<Q',io(BASE,b'',8)[1][:8])[0]
o=struct.unpack('<10Q',io(OFF,b'',80)[1][:80])
gw=rq(base+o[0]); lvl=rq(gw+o[2])
aa=rd(lvl+o[4],16); ad,an,am=struct.unpack('<QII',aa[:16])
print('idx  name                        hp    f151 f150 f152 f331 f33D')
for i in range(min(320,an)):
    a=rq(ad+i*8)
    if not a: continue
    ps=rq(a+0x2B0)
    if not ps: continue
    nm=fs(ps+0x388)
    if not nm or nm.strip()=='\ucb00': continue
    hp=struct.unpack('<f',rd(a+0x29C,4) or b'\0'*4)[0]
    b=rd(a+0x150,4) or b'\0'*4
    f331=rd(a+0x331,1)[0]; f33d=rd(a+0x33D,1)[0]
    print('%-3d  %-26s %-5.1f %-4d %-4d %-4d %-4d %-4d'%(i,nm,hp,b[1],b[0],b[2],f331,f33d))
k.CloseHandle(ctypes.c_void_p(h))
