$py = 'C:\Users\Administrator\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe'
$log = 'F:\dsh\32\Asgard_Polygon-main\admin_test.log'
& $py -c "import ctypes; k=ctypes.WinDLL('kernel32',use_last_error=True); [ (k.CreateFileW(p,0xC0000000,0,None,3,0,None), print(p,'err',ctypes.get_last_error())) for p in (r'\\.\PolygonMemory', r'\\.\GLOBALROOT\Device\PolygonMemory') ]" 2>&1 | Out-File $log -Encoding utf8
