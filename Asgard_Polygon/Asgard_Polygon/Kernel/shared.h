#pragma once

#define POLYGON_MAX_TRANSFER (128u * 1024u)
#define POLYGON_TRANSFER_HEADER 16u

#define POLYGON_IOCTL_BIND CTL_CODE(FILE_DEVICE_UNKNOWN, 0x800, METHOD_BUFFERED, FILE_READ_DATA | FILE_WRITE_DATA)
#define POLYGON_IOCTL_BASE CTL_CODE(FILE_DEVICE_UNKNOWN, 0x801, METHOD_BUFFERED, FILE_READ_DATA)
#define POLYGON_IOCTL_READ CTL_CODE(FILE_DEVICE_UNKNOWN, 0x802, METHOD_BUFFERED, FILE_READ_DATA)
#define POLYGON_IOCTL_WRITE CTL_CODE(FILE_DEVICE_UNKNOWN, 0x803, METHOD_BUFFERED, FILE_WRITE_DATA)
#define POLYGON_IOCTL_OFFSETS CTL_CODE(FILE_DEVICE_UNKNOWN, 0x804, METHOD_BUFFERED, FILE_READ_DATA)

typedef struct _PolygonBind
{
    unsigned long process_id;
} PolygonBind;

typedef struct _PolygonBase
{
    unsigned long long address;
} PolygonBase;

typedef struct _PolygonOffsets
{
    unsigned long long gworld_rva;
    unsigned long long fname_pool_rva;
    unsigned long long world_persistent_level;
    unsigned long long world_game_instance;
    unsigned long long level_actor_array;
    unsigned long long game_instance_local_players;
    unsigned long long local_player_controller;
    unsigned long long actor_fname;
    unsigned long long controller_camera_manager;
    unsigned long long camera_manager_view;
} PolygonOffsets;

typedef struct _PolygonTransfer
{
    unsigned long long address;
    unsigned long size;
    unsigned long reserved;
    unsigned char data[1];
} PolygonTransfer;
