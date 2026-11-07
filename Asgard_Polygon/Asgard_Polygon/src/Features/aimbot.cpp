#include "pch.h"
#include "aimbot.h"
#include <random>


FVector FindLookAtRotation(AActor target)
{
	FVector target_bone = target.bone.neckPos;

	switch (global->aimbot.target_bone)
	{
	case 0: target_bone = target.bone.headPos; break;
	case 1: target_bone = target.bone.neckPos; break;
	case 2: target_bone = target.bone.spine1Pos; break;
	case 3: target_bone = target.bone.spine2Pos; break;
	case 4: target_bone = target.bone.spine3Pos; break;
	case 5: target_bone = target.bone.lowerarmlPos; break;
	case 6: target_bone = target.bone.lowerarmrPos; break;
	}

	// CameraCachePrivate.Location is valid (the ESP projection depends on it),
	// so aim in world space. The head bone sits on top of the skull, so for the
	// "head" option we aim ~25% of the way down towards the neck (head centre).
	FVector aim = target_bone;
	if (global->aimbot.target_bone == 0)
	{
		const FVector head = target.bone.headPos;
		const FVector neck = target.bone.neckPos;
		aim = FVector(head.X + (neck.X - head.X) * 0.45,
			head.Y + (neck.Y - head.Y) * 0.45,
			head.Z + (neck.Z - head.Z) * 0.45);
	}

	FVector direction = aim - game::CameraCachePrivate.Location;
	FVector lookAtRotation;

	if (direction.length() < 0.001)
		return FVector{};
	lookAtRotation.X = std::atan2(direction.Z, std::hypot(direction.X, direction.Y)) * (180.0 / M_PI);
	lookAtRotation.Y = std::atan2(direction.Y, direction.X) * (180.0f / M_PI);

	return lookAtRotation;
}

bool in_bounds(const FVector& point, const FVector2D& circleCenter, float circleRadius)
{
	FVector2D screen;
	if (!project_world_to_screen(point, screen))
		return false;

	float distance = std::sqrt((screen.x - circleCenter.x) * (screen.x - circleCenter.x) +
		(screen.y - circleCenter.y) * (screen.y - circleCenter.y));

	return distance <= circleRadius;
}

FVector aim_bone_pos(const AActor& a)
{
	switch (global->aimbot.target_bone)
	{
	case 1: return a.bone.neckPos;
	case 2: return a.bone.spine1Pos;
	case 3: return a.bone.spine2Pos;
	case 4: return a.bone.spine3Pos;
	case 5: return a.bone.lowerarmlPos;
	case 6: return a.bone.lowerarmrPos;
	default: return a.bone.headPos;
	}
}

void GetNearestClient(AActor* target)
{
	bool found = false;
	float best = FLT_MAX;
	const FVector2D center(global->width / 2.f, global->height / 2.f);

	for (const auto& actor : snapshot_actors())
	{
		if (!bitset(actor.flags, actor_flags::ENEMY))
			continue;

		FVector2D screen;
		if (!project_world_to_screen(aim_bone_pos(actor), screen))
			continue;

		const float dx = screen.x - center.x;
		const float dy = screen.y - center.y;
		const float screen_dist = std::sqrt(dx * dx + dy * dy);

		const int mode = global->aimbot.aimbot_targeting_type;

		if (mode == TARGET_FOV || mode == TARGET_FOV_VISIBLE)
		{
			if (screen_dist > global->aimbot.fov_size)
				continue;
		}
		if (mode == TARGET_VISIBLE || mode == TARGET_FOV_VISIBLE)
		{
			if (!bitset(actor.flags, actor_flags::VISIBLE))
				continue;
		}

		// Default: pick whoever is closest to the crosshair on screen,
		// not whoever is closest in 3D (that one is often off to the side).
		float score = screen_dist;
		if (mode == TARGET_VISIBLE)
		{
			FVector loc = actor.Location;
			FVector cam = game::LocalEyePos;
			score = loc.distance(cam);
		}

		if (!found || score < best)
		{
			*target = actor;
			best = score;
			found = true;
		}
	}
}

ImVec2 SmoothAngle(FVector current_rotation, FVector new_rotation)
{
	double factor = std::clamp(static_cast<double>(global->aimbot.smoothness.smoothing_speed), 0.0, 40.0);
	double alpha = 1.0 / (1.0 + factor);
	if (global->aimbot.smoothness.randomness)
	{
		static thread_local std::mt19937 generator{std::random_device{}()};
		static thread_local std::uniform_real_distribution<double> variation(0.9, 1.1);
		alpha *= variation(generator);
	}
	double pitch = current_rotation.X + std::remainder(new_rotation.X - current_rotation.X, 360.0) * alpha;
	double yaw = current_rotation.Y + std::remainder(new_rotation.Y - current_rotation.Y, 360.0) * alpha;
	return ImVec2(static_cast<float>(std::clamp(pitch, -89.0, 89.0)), static_cast<float>(std::remainder(yaw, 360.0)));
}



void run_aimbot()
{
	AActor Target{};
	GetNearestClient(&Target);

	game::AimTarget = Target.address;

	// In silent mode the trigger path drives the angles; don't also snap the view.
	if (global->aimbot.silent_aim)
		return;

	if (Target.health <= 0)
		return;

	if (!game::LocalPlayerPawn || !game::PlayerController)
		return;

	{
		// Manual comparison aid: aim at an enemy's head yourself and compare
		// "current view" with "computed needed" angles.
		static ULONGLONG last_log = 0;
		const ULONGLONG now = GetTickCount64();
		if (now - last_log > 700 && Target.health > 0)
		{
			last_log = now;
			const auto need = FindLookAtRotation(Target);
			const float cur_pitch = driver.read<float>(game::LocalPlayerPawn + 0x678);
			const float cur_yaw = driver.read<float>(game::LocalPlayerPawn + 0x67C);
			printf("AMATH %s need=(%.1f, %.1f) cur=(%.1f, %.1f) cam=(%.0f,%.0f,%.0f) head=(%.0f,%.0f,%.0f)\n",
				Target.Name.c_str(), need.x, need.y, cur_pitch, cur_yaw,
				game::CameraCachePrivate.Location.X, game::CameraCachePrivate.Location.Y, game::CameraCachePrivate.Location.Z,
				Target.bone.headPos.X, Target.bone.headPos.Y, Target.bone.headPos.Z);
			fflush(stdout);
		}
	}

	if (GetForegroundWindow() == global->dx9.game_hwnd &&
		(get_key_state(global->aimbot.hotkey, 0) || !global->aimbot.hotkey))
	{
		auto rotation = FindLookAtRotation(Target);
		if (rotation.x == 0.0f && rotation.y == 0.0f)
			return;

		auto re = global->aimbot.smoothness.smoothing
			? SmoothAngle(game::CameraCachePrivate.Rotation, rotation)
			: ImVec2(rotation.x, rotation.y);

		// These two floats follow the camera rotation exactly in this build:
		//   Pawn + 0x678 = Pitch, Pawn + 0x67C = Yaw
		driver.write<float>(game::LocalPlayerPawn + 0x678, re.x);
		driver.write<float>(game::LocalPlayerPawn + 0x67C, re.y);
	}
}

static void send_left_click()
{
	INPUT in[2]{};
	in[0].type = INPUT_MOUSE;
	in[0].mi.dwFlags = MOUSEEVENTF_LEFTDOWN;
	in[1].type = INPUT_MOUSE;
	in[1].mi.dwFlags = MOUSEEVENTF_LEFTUP;
	SendInput(2, in, sizeof(INPUT));
}

// Silent aim + auto fire.
// Writes the target rotation for a few milliseconds around the shot and then
// restores the original view, so the camera never visibly snaps.
void run_trigger()
{
	if (GetForegroundWindow() != global->dx9.game_hwnd)
		return;
	if (!game::LocalPlayerPawn)
		return;

	AActor target{};
	GetNearestClient(&target);
	if (target.health <= 0)
		return;

	FVector2D screen;
	if (!project_world_to_screen(aim_bone_pos(target), screen))
		return;
	const float dx = screen.x - global->width / 2.0f;
	const float dy = screen.y - global->height / 2.0f;
	if (std::sqrt(dx * dx + dy * dy) > global->aimbot.fov_size)
		return;

	const bool lmb = (GetAsyncKeyState(VK_LBUTTON) & 0x8000) != 0;
	const bool want = global->aimbot.auto_fire || (global->aimbot.silent_aim && lmb);
	if (!want)
		return;

	static ULONGLONG last_shot = 0;
	const ULONGLONG now = GetTickCount64();
	const ULONGLONG gap = static_cast<ULONGLONG>(global->aimbot.auto_fire_delay < 30 ? 30 : global->aimbot.auto_fire_delay);
	if (now - last_shot < gap)
		return;
	last_shot = now;

	const std::uint64_t pawn = game::LocalPlayerPawn;
	const float old_pitch = driver.read<float>(pawn + 0x678);
	const float old_yaw = driver.read<float>(pawn + 0x67C);

	const FVector rot = FindLookAtRotation(target);

	// The game rewrites these angles from mouse input every frame, so a single
	// write gets overwritten before the shot is processed. Hold them with a
	// tight loop across the fire moment instead.
	const ULONGLONG t0 = GetTickCount64();
	while (GetTickCount64() - t0 < 18)
	{
		driver.write<float>(pawn + 0x678, rot.x);
		driver.write<float>(pawn + 0x67C, rot.y);
	}

	send_left_click();

	const ULONGLONG t1 = GetTickCount64();
	while (GetTickCount64() - t1 < 30)
	{
		driver.write<float>(pawn + 0x678, rot.x);
		driver.write<float>(pawn + 0x67C, rot.y);
	}

	driver.write<float>(pawn + 0x678, old_pitch);
	driver.write<float>(pawn + 0x67C, old_yaw);
}

void aimbot_thread()
{
	bool was1 = false, was2 = false;
	while (true)
	{
		if (global->aimbot.enabled)
			run_aimbot();

		if (global->aimbot.enabled && (global->aimbot.silent_aim || global->aimbot.auto_fire))
			run_trigger();

		// Mouse4 / Mouse5 -> dump actor snapshot for offline analysis
		const bool b1 = (GetAsyncKeyState(0x05) & 0x8000) != 0;
		const bool b2 = (GetAsyncKeyState(0x06) & 0x8000) != 0;
		if ((b1 && !was1) || (b2 && !was2))
			dump_actors_hotkey();
		was1 = b1; was2 = b2;

		Sleep(1);
	}
}
