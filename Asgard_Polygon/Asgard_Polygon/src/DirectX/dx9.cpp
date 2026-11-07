#include "pch.h"
#include "dx9.h"

extern IMGUI_IMPL_API LRESULT ImGui_ImplWin32_WndProcHandler(HWND, UINT, WPARAM, LPARAM);

static LRESULT CALLBACK OverlayWndProc(HWND hwnd, UINT message, WPARAM wparam, LPARAM lparam)
{
	if (ImGui::GetCurrentContext() &&
		ImGui_ImplWin32_WndProcHandler(hwnd, message, wparam, lparam))
		return TRUE;
	if (message == WM_DESTROY)
	{
		PostQuitMessage(0);
		return 0;
	}
	return DefWindowProcA(hwnd, message, wparam, lparam);
}

namespace DirectX
{
	HRESULT Init()
	{
		if (FAILED(Direct3DCreate9Ex(D3D_SDK_VERSION, &global->dx9.directObject)))
			exit(3);

		ZeroMemory(&global->dx9.p_params, sizeof(global->dx9.p_params));

		global->dx9.p_params.Windowed = true;
		global->dx9.p_params.SwapEffect = D3DSWAPEFFECT_DISCARD;
		global->dx9.p_params.hDeviceWindow = global->dx9.overlay_hwnd;
		global->dx9.p_params.MultiSampleQuality = D3DMULTISAMPLE_NONE;
		global->dx9.p_params.BackBufferFormat = D3DFMT_A8R8G8B8;
		global->dx9.p_params.BackBufferWidth = global->width;
		global->dx9.p_params.BackBufferHeight = global->height;
		global->dx9.p_params.EnableAutoDepthStencil = TRUE;
		global->dx9.p_params.AutoDepthStencilFormat = D3DFMT_D16;
		global->dx9.p_params.PresentationInterval = D3DPRESENT_INTERVAL_IMMEDIATE;

		if (FAILED(global->dx9.directObject->CreateDeviceEx(D3DADAPTER_DEFAULT, D3DDEVTYPE_HAL, global->dx9.overlay_hwnd, D3DCREATE_HARDWARE_VERTEXPROCESSING, &global->dx9.p_params, 0, &global->dx9.device)))
		{
			global->dx9.directObject->Release();
			exit(4);
		}

		ImGui::CreateContext();
		{
			ImGuiIO& fio = ImGui::GetIO();
			// Chinese font (Microsoft YaHei) + full CJK glyph ranges
			ImFont* cn = fio.Fonts->AddFontFromFileTTF("C:\\Windows\\Fonts\\msyh.ttc", 17.0f,
				nullptr, fio.Fonts->GetGlyphRangesChineseFull());
			if (!cn)
				fio.Fonts->AddFontFromFileTTF("C:\\Windows\\Fonts\\simhei.ttf", 17.0f,
					nullptr, fio.Fonts->GetGlyphRangesChineseFull());
		}
		ImGui_ImplWin32_Init(global->dx9.overlay_hwnd);
		ImGui_ImplDX9_Init(global->dx9.device);
		ImGuiIO& io = ImGui::GetIO(); (void)io;
		io.IniFilename = 0;
		ImGuiStyle* style = &ImGui::GetStyle();

		ImFontConfig config;
		config.PixelSnapH = true;
		config.OversampleH = 2;
		config.OversampleV = 1;
		config.GlyphExtraSpacing.x = 1.0f;

		io.Fonts->AddFontFromFileTTF("C:\\Windows\\Fonts\\calibril.ttf", 13, &config);

		style->WindowBorderSize = 0;
		style->FrameBorderSize = 0;
		style->WindowTitleAlign = { 0.5f, 0.5f };

		style->WindowRounding = 8.f;
		style->FrameRounding = 8.f;
		style->GrabRounding = 12.f;
		style->TabRounding = 5.f;

		style->GrabMinSize = 6.f;

	
		global->dx9.directObject->Release();
		return S_OK;
	}

	void CreateOverlay()
	{
		WNDCLASSEXA wcex = {
		sizeof(WNDCLASSEXA),
		0,
		OverlayWndProc,
		0,
		0,
		GetModuleHandleA(nullptr),
		LoadIcon(0, IDI_APPLICATION),
		LoadCursor(0, IDC_ARROW),
		0,
		0,
		"ASGARDCLASS",
		LoadIcon(0, IDI_APPLICATION)
		};
		if (!RegisterClassExA(&wcex))
			throw std::runtime_error("Could not register overlay class");
		RECT rect;
		GetWindowRect(GetDesktopWindow(), &rect);
		global->dx9.overlay_hwnd = CreateWindowExA(WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_TOOLWINDOW | WS_EX_TOPMOST,
			"ASGARDCLASS", "ASGARDWINDOW", WS_POPUP, rect.left, rect.top,
			rect.right - rect.left, rect.bottom - rect.top, nullptr, nullptr, wcex.hInstance, nullptr);
		if (!global->dx9.overlay_hwnd)
			throw std::runtime_error("Could not create overlay window");
		SetLayeredWindowAttributes(global->dx9.overlay_hwnd, RGB(0, 0, 0), 255, LWA_ALPHA);
		MARGINS margin = { -1 };
		DwmExtendFrameIntoClientArea(global->dx9.overlay_hwnd, &margin);
		ShowWindow(global->dx9.overlay_hwnd, SW_SHOW);
		// The first ShowWindow call may be overridden by STARTUPINFO.wShowWindow
		// for console processes; force it visible.
		ShowWindow(global->dx9.overlay_hwnd, SW_SHOW);
		SetWindowPos(global->dx9.overlay_hwnd, HWND_TOPMOST, rect.left, rect.top,
			rect.right - rect.left, rect.bottom - rect.top, SWP_SHOWWINDOW);
		UpdateWindow(global->dx9.overlay_hwnd);
	}
}
