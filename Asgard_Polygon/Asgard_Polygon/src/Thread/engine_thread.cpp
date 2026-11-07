#include "pch.h"
#include "engine_thread.h"
#include <cstdio>

// Hotkey dump: press mouse4/mouse5 in game to write a full actor snapshot to
// actor_dump.txt. Used to capture corpse state at the exact moment.
void dump_actors_hotkey()
{
	FILE* f = nullptr;
	if (fopen_s(&f, "F:\\dsh\\32\\Asgard_Polygon-main\\actor_dump.txt", "w") != 0 || !f)
		return;

	const std::uint64_t gw = driver.read<std::uint64_t>(global->base + global->offsets.gworld_rva);
	const std::uint64_t lvl = gw ? driver.read<std::uint64_t>(gw + global->offsets.world_persistent_level) : 0;
	std::uint64_t data = 0;
	int num = 0;
	if (lvl)
	{
		data = driver.read<std::uint64_t>(lvl + global->offsets.level_actor_array);
		num = driver.read<int>(lvl + global->offsets.level_actor_array + 8);
	}
	if (num < 0 || num > 20000) num = 0;

	fprintf(f, "gw=0x%llX lvl=0x%llX data=0x%llX num=%d\n",
		(unsigned long long)gw, (unsigned long long)lvl, (unsigned long long)data, num);

	const std::uint64_t lpawn = game::LocalPlayerPawn;
	double lx = 0, ly = 0, lz = 0;
	{
		const std::uint64_t lm = lpawn ? driver.read<std::uint64_t>(lpawn + 0x318) : 0;
		if (lm)
		{
			lx = driver.read<double>(lm + 0x250);
			ly = driver.read<double>(lm + 0x258);
			lz = driver.read<double>(lm + 0x260);
		}
	}

	int refs = 0;
	for (int i = 0; i < num; ++i)
	{
		const std::uint64_t actor = driver.read<std::uint64_t>(data + i * 8);
		if (!actor) continue;

		const std::uint64_t ps = driver.read<std::uint64_t>(actor + 0x2B0);
		const std::uint64_t own = ps ? driver.read<std::uint64_t>(ps + 0x308) : 0;
		const float hp = driver.read<float>(actor + 0x29C);

		double tx = 0, ty = 0, tz = 0;
		const std::uint64_t mesh = driver.read<std::uint64_t>(actor + 0x318);
		if (mesh)
		{
			tx = driver.read<double>(mesh + 0x250);
			ty = driver.read<double>(mesh + 0x258);
			tz = driver.read<double>(mesh + 0x260);
		}
		const double dx = tx - lx, dy = ty - ly, dz = tz - lz;
		const double dist = std::sqrt(dx * dx + dy * dy + dz * dz) / 100.0;

		std::string nm;
		if (ps)
		{
			FString fs(ps + 0x388);
			nm = fs.ToString();
		}

		const bool is_target = (game::AimTarget != 0 && actor == game::AimTarget);
		if (game::AimTarget != 0 && !is_target)
		{
			// keep only a few named reference actors for comparison
			if (nm.empty() || refs >= 3) continue;
			++refs;
		}

		fprintf(f, "A idx=%d actor=0x%llX ps=0x%llX hp=%.2f own_match=%d dist=%.1f local=%d tgt=%d name=%s\n",
			i, (unsigned long long)actor, (unsigned long long)ps, hp,
			(ps && own == actor) ? 1 : 0, dist, (actor == lpawn) ? 1 : 0,
			(game::AimTarget && actor == game::AimTarget) ? 1 : 0, nm.c_str());

		std::uint8_t buf[0x1000]{};
		if (driver.readm(reinterpret_cast<void*>(actor), buf, sizeof(buf)))
		{
			fprintf(f, "  AHEX ");
			for (int b = 0; b < 0x1000; ++b) fprintf(f, "%02X", buf[b]);
			fprintf(f, "\n");
		}
		if (ps)
		{
			std::uint8_t pb[0x600]{};
			if (driver.readm(reinterpret_cast<void*>(ps), pb, sizeof(pb)))
			{
				fprintf(f, "  PHEX ");
				for (int b = 0; b < 0x600; ++b) fprintf(f, "%02X", pb[b]);
				fprintf(f, "\n");
			}
		}
		{
			const std::uint64_t hc = driver.read<std::uint64_t>(actor + 0x730);
			if (hc && hc > 0x10000 && hc < 0x00007fffffffffffULL)
			{
				std::uint8_t hb[0x400]{};
				if (driver.readm(reinterpret_cast<void*>(hc), hb, sizeof(hb)))
				{
					fprintf(f, "  CHEX ");
					for (int b = 0; b < 0x400; ++b) fprintf(f, "%02X", hb[b]);
					fprintf(f, "\n");
				}
			}
		}
		{
			const std::uint64_t msh = driver.read<std::uint64_t>(actor + 0x318);
			if (msh && msh > 0x10000 && msh < 0x00007fffffffffffULL)
			{
				std::uint8_t mb[0x800]{};
				if (driver.readm(reinterpret_cast<void*>(msh), mb, sizeof(mb)))
				{
					fprintf(f, "  MHEX ");
					for (int b = 0; b < 0x800; ++b) fprintf(f, "%02X", mb[b]);
					fprintf(f, "\n");
				}
			}
		}
	}
	fclose(f);
	printf("DUMP written: actor_dump.txt\n");
	fflush(stdout);
}

enum Bone
{
	Root = 0,
	pelvis = 8,
	spine_01 = 11,
	spine_02 = 10,
	spine_03 = 9,
	neck_01 = 62,
	Head = 63,

	upperarm_l = 13,
	lowerarm_l = 14,
	hand_l = 15,

	upperarm_r = 38,
	lowerarm_r = 39,
	hand_r = 40,

	upperleg_l = 64,
	lowerleg_l = 65,
	foot_l = 67,

	upperleg_r = 70,
	lowerleg_r = 71,
	foot_r = 73,
};

D3DMATRIX MatrixMultiplication(D3DMATRIX pM1, D3DMATRIX pM2)
{
	D3DMATRIX pOut;
	pOut._11 = pM1._11 * pM2._11 + pM1._12 * pM2._21 + pM1._13 * pM2._31 + pM1._14 * pM2._41;
	pOut._12 = pM1._11 * pM2._12 + pM1._12 * pM2._22 + pM1._13 * pM2._32 + pM1._14 * pM2._42;
	pOut._13 = pM1._11 * pM2._13 + pM1._12 * pM2._23 + pM1._13 * pM2._33 + pM1._14 * pM2._43;
	pOut._14 = pM1._11 * pM2._14 + pM1._12 * pM2._24 + pM1._13 * pM2._34 + pM1._14 * pM2._44;
	pOut._21 = pM1._21 * pM2._11 + pM1._22 * pM2._21 + pM1._23 * pM2._31 + pM1._24 * pM2._41;
	pOut._22 = pM1._21 * pM2._12 + pM1._22 * pM2._22 + pM1._23 * pM2._32 + pM1._24 * pM2._42;
	pOut._23 = pM1._21 * pM2._13 + pM1._22 * pM2._23 + pM1._23 * pM2._33 + pM1._24 * pM2._43;
	pOut._24 = pM1._21 * pM2._14 + pM1._22 * pM2._24 + pM1._23 * pM2._34 + pM1._24 * pM2._44;
	pOut._31 = pM1._31 * pM2._11 + pM1._32 * pM2._21 + pM1._33 * pM2._31 + pM1._34 * pM2._41;
	pOut._32 = pM1._31 * pM2._12 + pM1._32 * pM2._22 + pM1._33 * pM2._32 + pM1._34 * pM2._42;
	pOut._33 = pM1._31 * pM2._13 + pM1._32 * pM2._23 + pM1._33 * pM2._33 + pM1._34 * pM2._43;
	pOut._34 = pM1._31 * pM2._14 + pM1._32 * pM2._24 + pM1._33 * pM2._34 + pM1._34 * pM2._44;
	pOut._41 = pM1._41 * pM2._11 + pM1._42 * pM2._21 + pM1._43 * pM2._31 + pM1._44 * pM2._41;
	pOut._42 = pM1._41 * pM2._12 + pM1._42 * pM2._22 + pM1._43 * pM2._32 + pM1._44 * pM2._42;
	pOut._43 = pM1._41 * pM2._13 + pM1._42 * pM2._23 + pM1._43 * pM2._33 + pM1._44 * pM2._43;
	pOut._44 = pM1._41 * pM2._14 + pM1._42 * pM2._24 + pM1._43 * pM2._34 + pM1._44 * pM2._44;
	return pOut;
}

FVector get_entity_bone(uintptr_t mesh, int bone_id)
{
	auto bone_array = driver.read<uint64_t>(mesh + 0x600);
	auto bone_array_size = driver.read<uint64_t>(mesh + 0x600 + 0x8);
	if (bone_array_size == 0)
		bone_array = driver.read<uint64_t>(mesh + 0x600 + 0x10);

	FTransform bone;
	driver.readm((void*)(bone_array + (bone_id * 0x60)), &bone, sizeof(FTransform));

	FTransform component_to_world = driver.read<FTransform>(mesh + 0x240);
	D3DMATRIX matrix = MatrixMultiplication(bone.ToMatrixWithScale(), component_to_world.ToMatrixWithScale());
	return FVector(matrix._41, matrix._42, matrix._43);
}

bool isVisible(DWORD_PTR mesh)
{
	float tolerance = .06f;
	float LastRenderTime = driver.read<float>(mesh + 0x35C);
	float LastSubmitTime = driver.read<float>(mesh + 0x358);

	return (LastRenderTime + tolerance) > LastSubmitTime;
}


void engine_thread()
{
	while (true)
	{
		game::GWorld = driver.read<uint64_t>(global->base + global->offsets.gworld_rva);

		if (game::GWorld < 0x10000 || game::GWorld > 0x00007fffffffffffULL)
		{
			publish_actors({});
			Sleep(10);
			continue;
		}

		game::PersistentLevel = driver.read(game::GWorld + global->offsets.world_persistent_level);

		if (!game::PersistentLevel)
		{
			publish_actors({});
			Sleep(10);
			continue;
		}

		game::OwningGameInstance = driver.read(game::GWorld + global->offsets.world_game_instance);

		if (!game::OwningGameInstance)
		{
			publish_actors({});
			Sleep(10);
			continue;
		}

		auto localPlayers = driver.read<TArray<uint64_t>>(game::OwningGameInstance + global->offsets.game_instance_local_players);
		game::LocalPlayer = localPlayers[0];

		if (!game::LocalPlayer)
		{
			publish_actors({});
			Sleep(10);
			continue;
		}

		game::PlayerController = driver.read(game::LocalPlayer + global->offsets.local_player_controller);

		if (!game::PlayerController)
		{
			publish_actors({});
			Sleep(10);
			continue;
		}

		game::LocalPlayerPawn = driver.read(game::PlayerController + 0x338);

		if (!game::LocalPlayerPawn)
		{
			publish_actors({});
			Sleep(10);
			continue;
		}

		game::LocalPlayerState = driver.read(game::LocalPlayerPawn + 0x2B0);

		{
			// Eye origin for aiming: same path used for every actor's Location
			// (root bone world position), lifted to head height.
			const std::uint64_t local_mesh = driver.read<std::uint64_t>(game::LocalPlayerPawn + 0x318);
			if (local_mesh)
			{
				FVector root = get_entity_bone(local_mesh, Root);
				if (std::isfinite(root.X) && std::isfinite(root.Y) && std::isfinite(root.Z))
				{
					game::LocalEyePos = FVector(root.X, root.Y, root.Z + 64.0);
				}
			}
		}

		if (!game::LocalPlayerState)
		{
			publish_actors({});
			Sleep(10);
			continue;
		}

		if (global->aimbot.nospread)
		{
			auto inventory = driver.read(game::LocalPlayerState + 0x430);
			auto weapon = driver.read(inventory + 0xF8);

			driver.write<float>(weapon + 0x6C4, 0.0000000001f); //Setting 0 breaks things
		}


		if (global->aimbot.norecoil)
		{
			auto inventory = driver.read(game::LocalPlayerState + 0x430);
			auto weapon = driver.read(inventory + 0xF8);

			driver.write<float>(weapon + 0x3F4, 0.0000000001f); //Setting 0 breaks things
			driver.write<float>(weapon + 0x3F8, 0.0000000001f);
			driver.write<float>(weapon + 0x3FC, 0.0000000001f);
			driver.write<float>(weapon + 0x400, 0.0000000001f);
			driver.write<float>(weapon + 0x404, 0.0000000001f);
			driver.write<float>(weapon + 0x408, 0.0000000001f);
		}

		game::PlayerCameraManager = driver.read(game::PlayerController + global->offsets.controller_camera_manager);

		if (!game::PlayerCameraManager)
		{
			publish_actors({});
			Sleep(10);
			continue;
		}

		game::LocalPlayerTeam = driver.read<uint8_t>(game::LocalPlayerState + 0x428);

		game::CameraCachePrivate = driver.read<FMinimalViewInfo>(game::PlayerCameraManager + global->offsets.camera_manager_view);


		if (!NamePoolData)
		{
			NamePoolData = new FNamePool();
			driver.readm((void*)(global->base + global->offsets.fname_pool_rva), NamePoolData, sizeof(FNamePool));
		}

		TArray actor_array = driver.read<TArray<uint64_t>>(game::PersistentLevel + global->offsets.level_actor_array);		if (!actor_array.Data || actor_array.Num() < 0 || actor_array.Num() > 4096)
		{
			publish_actors({});
			Sleep(10);
			continue;
		}

		game::ActorArray = actor_array.Data;
		game::ActorCount = actor_array.Num();

		std::vector<AActor> temp_Array;
		for (auto index{ 0 }; index < actor_array.Num(); index++)
		{
			auto actor = actor_array[index];

			if (!actor)
				continue;
			if (actor == game::LocalPlayerPawn)
				continue;

			auto filter_name = driver.read<FName>(actor + global->offsets.actor_fname);
			auto bp_name = NamePoolData->GetName(filter_name.Index);

			if (!strstr(bp_name.data(), "BP_PG_Game_Character"))
				continue;

			auto RootComponent = driver.read(actor + 0x198);
			if (!RootComponent)
				continue;

			auto playerstate = driver.read(actor + 0x2B0);
			if (!playerstate)
				continue;

			auto fstring_name = FString(playerstate + 0x388);
			auto team = driver.read<uint8_t>(playerstate + 0x428);

			int health = 0;
			int max_health = 60;
			{
				// Death flags for this build (verified in-game):
				//   actor + 0x151 : 1 = alive, other = dead
				const unsigned char alive_flag = driver.read<unsigned char>(actor + 0x151);
				if (alive_flag != 1)
					continue;

				// Real health: int32 CurrentHealth / MaxHealth inside the
				// HealthComponent referenced at actor + 0x738.
				const std::uint64_t hc = driver.read<std::uint64_t>(actor + 0x738);
				if (!hc || hc < 0x10000 || hc > 0x00007fffffffffffULL)
					continue;
				const int cur = driver.read<int>(hc + 0xD0);
				const int mx = driver.read<int>(hc + 0xD4);
				if (cur <= 0 || cur > 100000)
					continue;
				health = cur;
				if (mx > 0 && mx <= 100000)
					max_health = mx;
			}

			auto mesh = driver.read(actor + 0x318);
			if (!mesh)
				continue;

			auto location = get_entity_bone(mesh, Root);
			auto rotation = driver.read<FVector>(RootComponent + 0x140);
			int flag = NONE;

			if (isVisible(mesh))
				flag |= actor_flags::VISIBLE;
			if (team != game::LocalPlayerTeam)
				flag |= actor_flags::ENEMY;

			auto inventory = driver.read(playerstate + 0x430);
			auto weapon = driver.read(inventory + 0xF8);

			auto grenade_count = driver.read<uint8_t>(inventory + 0x100);
			auto gun_type = driver.read<uint8_t>(weapon + 0x395);


			//Body
			auto headPos = get_entity_bone(mesh, Head);
			auto neckPos = get_entity_bone(mesh, neck_01);
			auto spine1Pos = get_entity_bone(mesh, spine_01);
			auto spine2Pos = get_entity_bone(mesh, spine_02);
			auto spine3Pos = get_entity_bone(mesh, spine_03);
			auto pelvisPos = get_entity_bone(mesh, pelvis);

			//Arms
			auto upperarmlPos = get_entity_bone(mesh, upperarm_l);
			auto lowerarmlPos = get_entity_bone(mesh, lowerarm_l);
			auto handlPos = get_entity_bone(mesh, hand_l);
			auto upperarmrPos = get_entity_bone(mesh, upperarm_r);
			auto lowerarmrPos = get_entity_bone(mesh, lowerarm_r);
			auto handrPos = get_entity_bone(mesh, hand_r);

			//Legs
			auto upperleglPos = get_entity_bone(mesh, upperleg_l);
			auto lowerleglPos = get_entity_bone(mesh, lowerleg_l);
			auto footlPos = get_entity_bone(mesh, foot_l);
			auto upperlegrPos = get_entity_bone(mesh, upperleg_r);
			auto lowerlegrPos = get_entity_bone(mesh, lowerleg_r);
			auto footrPos = get_entity_bone(mesh, foot_r);

			AActor temp;

			temp.Location = location;
			temp.Rotation = rotation;
			temp.Name = fstring_name.ToString();
			temp.health = health;
			temp.max_health = max_health;

			temp.gun_type = gun_type;
			temp.grenade_count = grenade_count;

			temp.bone.headPos = headPos;
			temp.bone.neckPos = neckPos;
			temp.bone.spine1Pos = spine1Pos;
			temp.bone.spine2Pos = spine2Pos;
			temp.bone.spine3Pos = spine3Pos;
			temp.bone.pelvisPos = pelvisPos;

			temp.bone.upperarmlPos = upperarmlPos;
			temp.bone.lowerarmlPos = lowerarmlPos;
			temp.bone.handlPos = handlPos;
			temp.bone.upperarmrPos = upperarmrPos;
			temp.bone.lowerarmrPos = lowerarmrPos;
			temp.bone.handrPos = handrPos;

			temp.bone.upperleglPos = upperleglPos;
			temp.bone.lowerleglPos = lowerleglPos;
			temp.bone.footlPos = footlPos;
			temp.bone.upperlegrPos = upperlegrPos;
			temp.bone.lowerlegrPos = lowerlegrPos;
			temp.bone.footrPos = footrPos;

			temp.flags = flag;
			temp.address = actor;

			temp_Array.push_back(temp);

		}
		publish_actors(std::move(temp_Array));

	}
}

