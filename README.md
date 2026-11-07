# Asgard Polygon

External ESP / aimbot for **POLYGON** (Unreal Engine 5.2, EasyAntiCheat), driven by a
manually-mapped kernel driver instead of a handle-based read/write path.

Based on **[Asgard_Polygon](https://github.com/MrReekoFTWxD/Asgard_Polygon)** by
**MrReekoFTWxD** — the original external cheat base this fork was built from. All of the
original ESP/aimbot/ImGui groundwork is his; this fork adapts it to POLYGON, adds the
kernel driver path and re-derives the offsets for the current build.

> Research / educational project. Use only in your own offline sessions or private
> servers you are authorised to test. Using it in public matches violates the game's
> Terms of Service and will get your account banned.

---

## Architecture

```
Asgard_Polygon.exe  (user mode, admin)
      │  DeviceIoControl
      ▼
\\.\PolygonMemory     ← PolygonMemory.sys, manually mapped by KDMapper
      │  MmCopyVirtualMemory
      ▼
POLYGON-Win64-Shipping.exe
```

* **`PolygonMemory.sys`** – minimal driver exposing `bind / base / read / write / offsets`
  through IOCTLs. `DriverEntry` self-bootstraps with `IoCreateDriver` because KDMapper
  passes a `NULL` `DriverObject`.
* **KDMapper** – maps the unsigned driver using the `iqvw64e.sys` DSE bypass and then
  cleans `PiDDBCacheTable`, `g_KernelHashBucketList` and `MmUnloadedDrivers`.
* **Overlay** – ImGui on a layered, click-through D3D9 window; `F5` toggles the menu.

## Features

| Feature | Notes |
|---|---|
| ESP | 2D / 3D / 3D-rotated / corner / filled boxes, snaplines, names, distance, bones, weapon, view-angle bar |
| Health bar | real `CurrentHealth / MaxHealth` from the actor's health component |
| Team filter | hides teammates by default |
| Dead filter | corpses are neither drawn nor aimed at |
| Aimbot | crosshair-closest target, FOV circle, bone selection, smoothing + randomness |
| Silent aim | rewrites the view angles only around the shot and restores them |
| Auto fire | `SendInput` trigger with configurable interval |
| Extras | no-spread / no-recoil / FOV slider (offsets unverified) |

## Offsets (verified against the current build)

```
GWorld (RVA)                          0x82694E0
UWorld.PersistentLevel                0x30
UWorld.OwningGameInstance             0x1B8
ULevel.Actors (TArray)                0xA8
UGameInstance.LocalPlayers            0x38
UPlayer.LocalPlayerController         0x30
APlayerController.Pawn                0x338
APlayerController.PlayerCameraManager 0x348
APlayerCameraManager.CameraCache      0x22C0
AActor.Name (FName)                   0x18
AActor.RootComponent                  0x198
AActor.PlayerState                    0x2B0
AActor.Mesh (SkeletalMesh)            0x318
AActor.HealthComponent                0x738
```

| Field | Expression | Meaning |
|---|---|---|
| Health | `int32 *(actor + 0x738) + 0xD0` | 60 at full HP |
| Max health | `int32 *(actor + 0x738) + 0xD4` | 60 |
| Alive flag | `uint8 actor + 0x151` | `1` alive, other values = dead (health is **not** zeroed on death) |
| Team | `uint8 PlayerState + 0x428` | differs from local team ⇒ enemy |
| Player name | `FString PlayerState + 0x388` | UTF-16 |
| View pitch | `float Pawn + 0x678` | matches camera rotation exactly |
| View yaw | `float Pawn + 0x67C` | same |

## Quick start

1. Make sure EAC and the game are **not** running.
2. Map the driver (elevated):
   ```bat
   kdmapper.exe Asgard_Polygon\Asgard_Polygon\Kernel\PolygonMemory.sys
   ```
3. Launch POLYGON (Steam, EAC enabled).
4. Run `run_cheat.bat` as administrator.
5. `F5` in game opens the menu.

See [`README-OPERATION.md`](README-OPERATION.md) for the full write-up (build commands,
troubleshooting, debug tooling).

## Building

```powershell
# user-mode cheat (MSVC + Windows SDK 10.0.26100)
powershell -ExecutionPolicy Bypass -File build_manual.ps1

# kernel driver (WDM)
powershell -ExecutionPolicy Bypass -File build_kernel.ps1
```

Kill `Asgard_Polygon.exe` before rebuilding, otherwise the linker fails with `LNK1104`.

## Debug tooling

Pressing **mouse button 4 / 5** in game writes `actor_dump.txt` containing the currently
aimed actor plus three references, with hex dumps of the `AActor`, its `PlayerState`,
its `HealthComponent` and its `SkeletalMesh`. This is how the health and alive-flag
offsets above were recovered, and it is the fastest way to re-derive offsets after a
game update.

## Credits

* **[MrReekoFTWxD / Asgard_Polygon](https://github.com/MrReekoFTWxD/Asgard_Polygon)** –
  original project this fork is based on (ESP, aimbot, ImGui menu, `driver` abstraction).
  Huge thanks for releasing it.
* [KDMapper](https://github.com/TheCruZ/kdmapper) – manual mapper used to load the driver.
* [GSpots](https://github.com/Do0ks/GSpots) – UE dump tool used while locating `GWorld` / `GNames`.
* Dear ImGui – overlay UI.
