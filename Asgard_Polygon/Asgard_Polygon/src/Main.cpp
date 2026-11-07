// External_Template.cpp : This file contains the 'main' function. Program execution begins and ends there.
//

#include "pch.h"

static int probe_session()
{
    const auto& offsets = global->offsets;
    const auto world = driver.read<uint64_t>(global->base + offsets.gworld_rva);
    if (world < 0x10000 || world > 0x00007fffffffffffULL)
    {
        printf("GWorld read failed: 0x%llX\n", world);
        return 2;
    }

    const auto level = driver.read<uint64_t>(world + offsets.world_persistent_level);
    const auto instance = driver.read<uint64_t>(world + offsets.world_game_instance);
    const auto local_players = driver.read<TArray<uint64_t>>(
        instance + offsets.game_instance_local_players);
    const auto local_player = local_players.Num() > 0 && local_players.Num() <= 8
        ? local_players[0] : 0;
    const auto controller = driver.read<uint64_t>(local_player + offsets.local_player_controller);
    const auto pawn = driver.read<uint64_t>(controller + 0x338);
    const auto camera = driver.read<uint64_t>(controller + offsets.controller_camera_manager);
    const auto view = driver.read<FMinimalViewInfo>(camera + offsets.camera_manager_view);
    printf("World=0x%llX Level=0x%llX Instance=0x%llX\n", world, level, instance);
    printf("LocalPlayers=%d LocalPlayer=0x%llX Controller=0x%llX Pawn(candidate)=0x%llX\n",
        local_players.Num(), local_player, controller, pawn);
    printf("Camera=0x%llX FOV=%.1f Position=(%.1f, %.1f, %.1f)\n",
        camera, view.FOV, view.Location.X, view.Location.Y, view.Location.Z);

    FNamePool names{};
    if (!driver.readm(reinterpret_cast<void*>(global->base + offsets.fname_pool_rva),
        &names, sizeof(names)))
    {
        puts("Could not read name pool");
        return 3;
    }

    const auto actors = driver.read<TArray<uint64_t>>(level + offsets.level_actor_array);
    printf("ActorArray=0x%llX Count=%d Max=%d\n", actors.Data, actors.Num(), actors.Max);
    if (!actors.Data || actors.Num() < 0 || actors.Num() > 4096 ||
        actors.Max < actors.Num())
        return 4;

    int shown = 0;
    for (int i = 0; i < actors.Num() && shown < 80; ++i)
    {
        const auto actor = actors[i];
        if (!actor)
            continue;
        const auto fname = driver.read<FName>(actor + offsets.actor_fname);
        const auto name = names.GetName(fname.Index);
        if (name.empty() || (i >= 20 && name.find("Character") == std::string::npos &&
            name.find("Player") == std::string::npos &&
            name.find("Pawn") == std::string::npos))
            continue;
        printf("Actor[%d] 0x%llX %s\n", i, actor, name.c_str());
        if (name.find("Character") != std::string::npos ||
            name.find("Pawn") != std::string::npos)
        {
            const auto root = driver.read<uint64_t>(actor + 0x198);
            const auto mesh = driver.read<uint64_t>(actor + 0x318);
            const auto state = driver.read<uint64_t>(actor + 0x2B0);
            const auto health_component = driver.read<uint64_t>(actor + 0x730);
            printf("  candidates: Root=0x%llX Mesh=0x%llX State=0x%llX HealthComponent=0x%llX\n",
                root, mesh, state, health_component);
        }
        ++shown;
    }
    return 0;
}

int main(int argc, char** argv)
{
	setvbuf(stdout, nullptr, _IONBF, 0); // unbuffered: log lines appear immediately
	global = new GlobalVariables();

	printf("Waiting for POLYGON-Win64-Shipping...\n");
    while (global->dx9.game_hwnd == 0)
    {
        driver.process_id = driver.get_process_id(L"POLYGON-Win64-Shipping.exe");
        if (driver.process_id)
            global->dx9.game_hwnd = get_process_wnd(driver.process_id);
        if (!global->dx9.game_hwnd)
            Sleep(500);
    }

    if (!driver.init())
    {
        printf("Could not connect to PolygonMemory driver (Windows error %lu).\n", GetLastError());
        return 1;
    }
    global->base = driver.get_base_address();
    if (!global->base)
    {
        printf("Could not read game image base\n");
        return 1;
    }
    if (!driver.get_offsets(global->offsets))
    {
        printf("Could not read offset table from driver\n");
        return 1;
    }
    // The game creates GWorld during its black-screen startup; poll until it is valid.
    std::uint64_t world = 0;
    for (int attempt = 0; attempt < 300; ++attempt)
    {
        world = driver.read<std::uint64_t>(global->base + global->offsets.gworld_rva);
        if (world >= 0x10000 && world <= 0x00007fffffffffffULL)
            break;
        Sleep(1000);
    }
    if (world < 0x10000 || world > 0x00007fffffffffffULL)
    {
        printf("Unsupported POLYGON build: GWorld offset 0x%llX is invalid (0x%llX).\n",
            global->offsets.gworld_rva, world);
        return 2;
    }
    printf(Xors("Base: %llX\n"), global->base);

    if (argc > 1 && strcmp(argv[1], "--probe") == 0)
        return probe_session();

    DirectX::CreateOverlay();

    // gui.cpp exits immediately if game_hwnd is NULL, and it only assigns
    // game_hwnd inside its else branch. Resolve it here before the gui loop.
    global->dx9.game_hwnd = get_process_wnd(driver.process_id);
    if (!global->dx9.game_hwnd)
    {
        printf("Could not find POLYGON game window\n");
        return 1;
    }

    DirectX::Init();

    std::thread engine(engine_thread);
    std::thread aimbot(aimbot_thread);
    engine.detach();
    aimbot.detach();

    gui::instance();
    exit(0);
}
