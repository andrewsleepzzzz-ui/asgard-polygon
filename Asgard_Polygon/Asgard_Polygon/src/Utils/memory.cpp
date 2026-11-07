#include "pch.h"
#include "memory.h"
#include "../../Kernel/shared.h"

GameDriver driver;

GameDriver::~GameDriver()
{
    if (device_ != INVALID_HANDLE_VALUE)
        CloseHandle(device_);
}

DWORD GameDriver::get_process_id(const wchar_t* image_name) const
{
    HANDLE snapshot = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0);
    if (snapshot == INVALID_HANDLE_VALUE)
        return 0;
    PROCESSENTRY32W entry{};
    entry.dwSize = sizeof(entry);
    DWORD pid = 0;
    for (BOOL found = Process32FirstW(snapshot, &entry); found; found = Process32NextW(snapshot, &entry))
    {
        if (_wcsicmp(entry.szExeFile, image_name) == 0)
        {
            pid = entry.th32ProcessID;
            break;
        }
    }
    CloseHandle(snapshot);
    return pid;
}

bool GameDriver::init()
{
    if (!process_id)
        return false;
    device_ = CreateFileW(L"\\\\.\\PolygonMemory", GENERIC_READ | GENERIC_WRITE,
        0, nullptr, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, nullptr);
    if (device_ == INVALID_HANDLE_VALUE)
        return false;
    PolygonBind request{process_id};
    DWORD returned = 0;
    return DeviceIoControl(device_, POLYGON_IOCTL_BIND, &request, sizeof(request),
        nullptr, 0, &returned, nullptr) != FALSE;
}

std::uint64_t GameDriver::get_base_address() const
{
    if (device_ == INVALID_HANDLE_VALUE)
        return 0;
    PolygonBase response{};
    DWORD returned = 0;
    if (!DeviceIoControl(device_, POLYGON_IOCTL_BASE, nullptr, 0, &response,
        sizeof(response), &returned, nullptr) || returned != sizeof(response))
        return 0;
    return response.address;
}

bool GameDriver::get_offsets(PolygonOffsets& offsets) const
{
    offsets = {};
    if (device_ == INVALID_HANDLE_VALUE)
        return false;
    PolygonOffsets response{};
    DWORD returned = 0;
    if (!DeviceIoControl(device_, POLYGON_IOCTL_OFFSETS, nullptr, 0, &response,
        sizeof(response), &returned, nullptr) || returned != sizeof(response))
        return false;
    offsets = response;
    return offsets.gworld_rva != 0 && offsets.fname_pool_rva != 0;
}

bool GameDriver::readm(const void* address, void* destination, std::size_t size) const
{
    if (device_ == INVALID_HANDLE_VALUE || !address || !destination || !size ||
        size > POLYGON_MAX_TRANSFER)
        return false;
    std::vector<std::uint8_t> buffer(POLYGON_TRANSFER_HEADER + size);
    auto* transfer = reinterpret_cast<PolygonTransfer*>(buffer.data());
    transfer->address = reinterpret_cast<std::uint64_t>(address);
    transfer->size = static_cast<std::uint32_t>(size);
    transfer->reserved = 0;
    DWORD returned = 0;
    if (!DeviceIoControl(device_, POLYGON_IOCTL_READ, buffer.data(),
        static_cast<DWORD>(POLYGON_TRANSFER_HEADER), buffer.data(),
        static_cast<DWORD>(buffer.size()), &returned, nullptr) ||
        returned != buffer.size())
        return false;
    memcpy(destination, transfer->data, size);
    return true;
}

bool GameDriver::writem(void* address, const void* source, std::size_t size) const
{
    if (device_ == INVALID_HANDLE_VALUE || !address || !source || !size ||
        size > POLYGON_MAX_TRANSFER)
        return false;
    std::vector<std::uint8_t> buffer(POLYGON_TRANSFER_HEADER + size);
    auto* transfer = reinterpret_cast<PolygonTransfer*>(buffer.data());
    transfer->address = reinterpret_cast<std::uint64_t>(address);
    transfer->size = static_cast<std::uint32_t>(size);
    transfer->reserved = 0;
    memcpy(transfer->data, source, size);
    DWORD returned = 0;
    return DeviceIoControl(device_, POLYGON_IOCTL_WRITE, buffer.data(),
        static_cast<DWORD>(buffer.size()), nullptr, 0, &returned, nullptr) != FALSE;
}

bool get_key_state(int key, int flag)
{
    HWND foreground = GetForegroundWindow();
    if (foreground != global->dx9.game_hwnd && foreground != global->dx9.overlay_hwnd)
        return false;
    if (key < 0 || key >= 0x100)
        return false;
    static BYTE prior[0x100]{};
    bool down = (GetAsyncKeyState(key) & 0x8000) != 0;
    bool result = down && (!(flag & 1) || !prior[key]);
    prior[key] = down;
    return result;
}

HWND get_process_wnd(DWORD pid)
{
    struct Search { DWORD pid; HWND hwnd; } search{pid, nullptr};
    EnumWindows([](HWND hwnd, LPARAM param) -> BOOL {
        auto* result = reinterpret_cast<Search*>(param);
        DWORD candidate = 0;
        GetWindowThreadProcessId(hwnd, &candidate);
        if (candidate == result->pid && GetWindow(hwnd, GW_OWNER) == nullptr && IsWindowVisible(hwnd))
        {
            result->hwnd = hwnd;
            return FALSE;
        }
        return TRUE;
    }, reinterpret_cast<LPARAM>(&search));
    return search.hwnd;
}
