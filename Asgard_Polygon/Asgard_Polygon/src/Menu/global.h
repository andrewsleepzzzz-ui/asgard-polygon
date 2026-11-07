#pragma once
#include "../../Kernel/shared.h"

enum targeting_type
{
	TARGET_VISIBLE,
	TARGET_FOV,
	TARGET_FOV_VISIBLE,
	TARGET_CLOSEST
};

struct GlobalVariables
{
	int width{ GetSystemMetrics(SM_CXSCREEN) };
	int height{ GetSystemMetrics(SM_CYSCREEN) };

	struct
	{
		IDirect3D9Ex* directObject;
		IDirect3DDevice9Ex* device;
		D3DPRESENT_PARAMETERS p_params;

		HWND overlay_hwnd;
		HWND game_hwnd;

	}dx9;

	struct
	{
		bool enabled{ true };

		int aimbot_targeting_type;
		int target_bone;

		int hotkey{ VK_RBUTTON };

		bool fov_circle;
		float fov_size{ 220 };

		bool nospread;
		bool norecoil;

		bool silent_aim;
		bool auto_fire;
		int auto_fire_delay{ 120 };

		struct
		{
			bool smoothing;
			float smoothing_speed{ 35 };
			bool randomness;
		}smoothness;

	}aimbot;

	struct
	{
		int boxType{ 1 };   // 2D by default
		int snapType{ 0 };

		bool name{ true };
		bool distance{ true };
		bool health_bar{ true };
		bool bones{ true };
		bool view_angles{ false };
		bool weapon{ false };
		bool teammates{ false };
	}esp;

	uint64_t base;
	PolygonOffsets offsets{};
};
extern GlobalVariables* global;
