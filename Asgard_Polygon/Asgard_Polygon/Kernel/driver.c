#include <ntifs.h>
#include <wdmsec.h>
#include "shared.h"

extern NTKERNELAPI PVOID PsGetProcessSectionBaseAddress(PEPROCESS Process);
extern NTKERNELAPI NTSTATUS MmCopyVirtualMemory(
    PEPROCESS FromProcess, PVOID FromAddress,
    PEPROCESS ToProcess, PVOID ToAddress,
    SIZE_T BufferSize, KPROCESSOR_MODE PreviousMode, PSIZE_T NumberOfBytesCopied);

static const GUID PolygonDeviceGuid =
    {0x710845a9, 0xb06c, 0x4cf8, {0x94, 0xf2, 0x11, 0xa3, 0x90, 0x58, 0x21, 0xde}};

static NTSTATUS Complete(PIRP Irp, NTSTATUS Status, ULONG_PTR Information)
{
    Irp->IoStatus.Status = Status;
    Irp->IoStatus.Information = Information;
    IoCompleteRequest(Irp, IO_NO_INCREMENT);
    return Status;
}

static NTSTATUS Create(PDEVICE_OBJECT DeviceObject, PIRP Irp)
{
    UNREFERENCED_PARAMETER(DeviceObject);
    return Complete(Irp, STATUS_SUCCESS, 0);
}

static NTSTATUS Close(PDEVICE_OBJECT DeviceObject, PIRP Irp)
{
    PIO_STACK_LOCATION stack = IoGetCurrentIrpStackLocation(Irp);
    PEPROCESS process;
    UNREFERENCED_PARAMETER(DeviceObject);
    process = (PEPROCESS)InterlockedExchangePointer(&stack->FileObject->FsContext, NULL);
    if (process != NULL)
        ObDereferenceObject(process);
    return Complete(Irp, STATUS_SUCCESS, 0);
}

static BOOLEAN IsPolygonProcess(PEPROCESS Process)
{
    static const UNICODE_STRING suffix =
        RTL_CONSTANT_STRING(L"\\POLYGON-Win64-Shipping.exe");
    PUNICODE_STRING image = NULL;
    BOOLEAN matches = FALSE;
    if (NT_SUCCESS(SeLocateProcessImageName(Process, &image)) && image != NULL)
    {
        matches = RtlSuffixUnicodeString(&suffix, image, TRUE);
        ExFreePool(image);
    }
    return matches;
}

static BOOLEAN ValidUserRange(ULONGLONG Address, ULONG Size)
{
    const ULONGLONG maximum = 0x00007fffffffffffULL;
    return Address >= 0x10000 && Address <= maximum &&
        Size > 0 && Size <= POLYGON_MAX_TRANSFER &&
        (ULONGLONG)Size - 1 <= maximum - Address;
}

static NTSTATUS DeviceControl(PDEVICE_OBJECT DeviceObject, PIRP Irp)
{
    PIO_STACK_LOCATION stack = IoGetCurrentIrpStackLocation(Irp);
    ULONG input = stack->Parameters.DeviceIoControl.InputBufferLength;
    ULONG output = stack->Parameters.DeviceIoControl.OutputBufferLength;
    ULONG code = stack->Parameters.DeviceIoControl.IoControlCode;
    PVOID buffer = Irp->AssociatedIrp.SystemBuffer;
    PFILE_OBJECT file = stack->FileObject;
    PEPROCESS process = (PEPROCESS)file->FsContext;
    NTSTATUS status = STATUS_INVALID_DEVICE_REQUEST;
    ULONG_PTR information = 0;
    UNREFERENCED_PARAMETER(DeviceObject);

    if (code == POLYGON_IOCTL_BIND)
    {
        if (process != NULL)
            status = STATUS_DEVICE_BUSY;
        else if (buffer == NULL || input != sizeof(PolygonBind))
            status = STATUS_INVALID_PARAMETER;
        else
        {
            PEPROCESS candidate = NULL;
            ULONG pid = ((PolygonBind*)buffer)->process_id;
            status = PsLookupProcessByProcessId((HANDLE)(ULONG_PTR)pid, &candidate);
            if (NT_SUCCESS(status))
            {
                if (IsPolygonProcess(candidate))
                    file->FsContext = candidate;
                else
                {
                    status = STATUS_ACCESS_DENIED;
                    ObDereferenceObject(candidate);
                }
            }
        }
    }
    else if (process == NULL)
        status = STATUS_INVALID_HANDLE;
    else if (code == POLYGON_IOCTL_BASE)
    {
        if (buffer == NULL || output < sizeof(PolygonBase))
            status = STATUS_BUFFER_TOO_SMALL;
        else
        {
            ((PolygonBase*)buffer)->address =
                (ULONGLONG)(ULONG_PTR)PsGetProcessSectionBaseAddress(process);
            information = sizeof(PolygonBase);
            status = STATUS_SUCCESS;
        }
    }
    else if (code == POLYGON_IOCTL_OFFSETS)
    {
        if (buffer == NULL || output < sizeof(PolygonOffsets))
            status = STATUS_BUFFER_TOO_SMALL;
        else
        {
            PolygonOffsets* offsets = (PolygonOffsets*)buffer;
            offsets->gworld_rva = 0x82694E0ULL;
            offsets->fname_pool_rva = 0x8069A00ULL;
            offsets->world_persistent_level = 0x30ULL;
            offsets->world_game_instance = 0x1B8ULL;
            offsets->level_actor_array = 0xA8ULL;
            offsets->game_instance_local_players = 0x38ULL;
            offsets->local_player_controller = 0x30ULL;
            offsets->actor_fname = 0x18ULL;
            offsets->controller_camera_manager = 0x348ULL;
            offsets->camera_manager_view = 0x22C0ULL;
            information = sizeof(PolygonOffsets);
            status = STATUS_SUCCESS;
        }
    }
    else if (code == POLYGON_IOCTL_READ || code == POLYGON_IOCTL_WRITE)
    {
        PolygonTransfer* transfer = (PolygonTransfer*)buffer;
        SIZE_T copied = 0;
        if (buffer == NULL || input < POLYGON_TRANSFER_HEADER)
            status = STATUS_INVALID_PARAMETER;
        else if (!ValidUserRange(transfer->address, transfer->size))
            status = STATUS_INVALID_PARAMETER;
        else if (code == POLYGON_IOCTL_READ &&
                 output < POLYGON_TRANSFER_HEADER + transfer->size)
            status = STATUS_BUFFER_TOO_SMALL;
        else if (code == POLYGON_IOCTL_WRITE &&
                 input < POLYGON_TRANSFER_HEADER + transfer->size)
            status = STATUS_BUFFER_TOO_SMALL;
        else if (code == POLYGON_IOCTL_READ)
        {
            status = MmCopyVirtualMemory(process, (PVOID)(ULONG_PTR)transfer->address,
                PsGetCurrentProcess(), transfer->data, transfer->size, KernelMode, &copied);
            if (NT_SUCCESS(status) && copied == transfer->size)
                information = POLYGON_TRANSFER_HEADER + copied;
            else if (NT_SUCCESS(status))
                status = STATUS_PARTIAL_COPY;
        }
        else
        {
            status = MmCopyVirtualMemory(PsGetCurrentProcess(), transfer->data,
                process, (PVOID)(ULONG_PTR)transfer->address,
                transfer->size, KernelMode, &copied);
            if (NT_SUCCESS(status) && copied != transfer->size)
                status = STATUS_PARTIAL_COPY;
        }
    }
    return Complete(Irp, status, information);
}

static VOID Unload(PDRIVER_OBJECT DriverObject)
{
    UNICODE_STRING link = RTL_CONSTANT_STRING(L"\\DosDevices\\PolygonMemory");
    IoDeleteSymbolicLink(&link);
    IoDeleteDevice(DriverObject->DeviceObject);
}

NTKERNELAPI NTSTATUS NTAPI IoCreateDriver(PUNICODE_STRING DriverName, PDRIVER_INITIALIZE InitializationFunction);

NTSTATUS DriverEntry(PDRIVER_OBJECT DriverObject, PUNICODE_STRING RegistryPath)
{
    UNICODE_STRING name = RTL_CONSTANT_STRING(L"\\Device\\PolygonMemory");
    UNICODE_STRING link = RTL_CONSTANT_STRING(L"\\DosDevices\\PolygonMemory");
    PDEVICE_OBJECT device = NULL;
    NTSTATUS status;

    // Manually-mapped drivers (KDMapper etc.) are invoked with DriverObject == NULL.
    // Create a real driver object and re-enter so IoCreateDeviceSecure works.
    if (DriverObject == NULL)
    {
        UNICODE_STRING drvname;
        RtlInitUnicodeString(&drvname, L"\\Driver\\PolygonMemory");
        return IoCreateDriver(&drvname, DriverEntry);
    }
    UNREFERENCED_PARAMETER(RegistryPath);

    status = IoCreateDeviceSecure(DriverObject, 0, &name, FILE_DEVICE_UNKNOWN,
        FILE_DEVICE_SECURE_OPEN, FALSE, &SDDL_DEVOBJ_SYS_ALL_ADM_ALL,
        &PolygonDeviceGuid, &device);
    if (!NT_SUCCESS(status))
        return status;

    DriverObject->MajorFunction[IRP_MJ_CREATE] = Create;
    DriverObject->MajorFunction[IRP_MJ_CLOSE] = Close;
    DriverObject->MajorFunction[IRP_MJ_DEVICE_CONTROL] = DeviceControl;
    DriverObject->DriverUnload = Unload;

    status = IoCreateSymbolicLink(&link, &name);
    if (!NT_SUCCESS(status))
    {
        IoDeleteDevice(device);
        return status;
    }
    device->Flags &= ~DO_DEVICE_INITIALIZING;
    return STATUS_SUCCESS;
}
