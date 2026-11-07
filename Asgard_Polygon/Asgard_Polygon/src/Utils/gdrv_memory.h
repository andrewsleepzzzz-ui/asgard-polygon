#pragma once
#include <windows.h>
#include <cstdint>
#include <vector>

// BYOVD via Gigabyte GIOV3 (gdrv3.sys, EV-signed, service "gdrv3")
//   IOCTL 0xC3502004 : IoAllocateMdl+MmBuildMdlForNonPagedPool+MmMapLockedPagesSpecifyCache
//                      in  = { uint64 phys; uint32 size; uint32 pad; }  (16 bytes)
//                      out = { uint64 user_va; }                       (16 bytes)
//   IOCTL 0xC3502584 : MmUnmapLockedPages (unmap)
// Device requires Administrator (SDDL) -> the cheat must run elevated.
namespace gdrv {
    bool open();
    void close();
    bool is_open();

    void* map_phys(uint64_t phys, uint32_t size);
    bool  unmap(void* va, uint32_t size);
    bool  read_phys(uint64_t phys, void* buf, uint32_t size);
    bool  write_phys(uint64_t phys, const void* buf, uint32_t size);

    // walk page tables of a process identified by its CR3 (PML4 physical address)
    bool  read_virt(uint64_t cr3, uint64_t va, void* buf, uint32_t size);
    bool  write_virt(uint64_t cr3, uint64_t va, const void* buf, uint32_t size);

    // scan physical memory for the PML4 whose translation maps `image_base` to an MZ header
    uint64_t find_cr3(uint64_t image_base, uint64_t max_phys = 0x800000000ULL);

    // scan physical memory for the game's EPROCESS by its 15-byte ImageFileName.
    // returns the EPROCESS physical address (0 on failure) and fills out_cr3 / out_base.
    uint64_t find_eprocess(const char* name15, uint64_t max_phys,
                           uint64_t* out_cr3, uint64_t* out_base);
}
