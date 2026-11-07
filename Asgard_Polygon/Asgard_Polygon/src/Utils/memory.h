#pragma once
#include <Windows.h>
#include <cstdint>
#include <cstddef>
#include "../../Kernel/shared.h"

bool get_key_state(int key, int flag = 1);
HWND get_process_wnd(DWORD pid);

class GameDriver
{
public:
    DWORD process_id = 0;
    ~GameDriver();

    DWORD get_process_id(const wchar_t* image_name) const;
    bool init();
    std::uint64_t get_base_address() const;
    bool get_offsets(PolygonOffsets& offsets) const;
    bool readm(const void* address, void* destination, std::size_t size) const;
    bool writem(void* address, const void* source, std::size_t size) const;

    template <typename T>
    T read(std::uint64_t address) const
    {
        T value{};
        readm(reinterpret_cast<const void*>(address), &value, sizeof(value));
        return value;
    }

    std::uint64_t read(std::uint64_t address) const
    {
        return read<std::uint64_t>(address);
    }

    template <typename T>
    bool write(std::uint64_t address, const T& value) const
    {
        return writem(reinterpret_cast<void*>(address), &value, sizeof(value));
    }

private:
    HANDLE device_ = INVALID_HANDLE_VALUE;
};

extern GameDriver driver;
