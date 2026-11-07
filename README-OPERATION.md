# Asgard Polygon — 运行说明（UE 5.2 / EAC）

**方案**：KDMapper（`iqvw64e.sys`）映射自研 `PolygonMemory.sys`（含 DKOM 清表）+ `MmCopyVirtualMemory` 读写 + ImGui(D3D9) 外部覆盖层。

---

## 一、每次开机流程

1. **确保 EAC / POLYGON 都没运行**（KDMapper 加载脆弱驱动时 EAC 会拦，报 `0xC0000022`）
2. 管理员运行：
   ```
   F:\dsh\kdmapper-master\x64\Release\kdmapper.exe ^
     F:\dsh\32\Asgard_Polygon-main\Asgard_Polygon\Asgard_Polygon\Kernel\PolygonMemory.sys
   ```
   看到 `[+] success` 即可（会清 `PiDDBCacheTable` / `g_KernelHashBucketList` / `MmUnloadedDrivers`）
3. **启动 POLYGON**（Steam，正常带 EAC 进游戏）
4. 管理员运行 `F:\dsh\32\Asgard_Polygon-main\run_cheat.bat`
5. 游戏内 **F5** 开菜单 → 勾选项 → 再按 **F5** 关菜单

> 火绒会把 `kdmapper.exe` / 编译产物当风险删掉，用之前先退火绒；
> 缺了就用 `build_kdmapper.ps1` / `build_manual.ps1` 重编。

## 二、按键

| 键 | 功能 |
|---|---|
| **F5** | 开/关 ImGui 中文菜单 |
| **F12** | 退出外挂 |
| **鼠标右键** | 自瞄（可改热键） |
| **鼠标侧键 4/5** | 调试：dump 当前锁定目标到 `actor_dump.txt` |

## 三、已验证偏移（本 build 实测）

```
GWorld (RVA)                          0x82694E0
UWorld.PersistentLevel                0x30
UWorld.OwningGameInstance             0x1B8
ULevel.Actors(TArray)                 0xA8
UGameInstance.LocalPlayers            0x38
UPlayer.LocalPlayerController         0x30
APlayerController.Pawn                0x338
APlayerController.PlayerCameraManager 0x348
APlayerCameraManager.CameraCache      0x22C0
AActor.Name(FName)                    0x18
AActor.RootComponent                  0x198
AActor.PlayerState                    0x2B0
AActor.Mesh(SkeletalMesh)             0x318
AActor.HealthComponent                0x730
```

### 关键游戏字段（实测验证）

| 用途 | 表达式 | 说明 |
|---|---|---|
| **HealthComponent** | `uint64 actor + 0x738` | 真血量的组件指针（注意不是 0x730） |
| **当前血量** | `int32  hc + 0xD0` | 满血 60，随伤害递减 |
| **血量上限** | `int32  hc + 0xD4` | 本版本为 60 |
| **存活标志** | `uint8  actor + 0x151` | **1 = 活**，其他（2/4）= 死（死后血量不归零，必须靠这个） |
| **Pawn 归属** | `uint64 PlayerState + 0x308` | == actor 表示仍被占有 |
| **队伍** | `uint8  PlayerState + 0x428` | 与本地玩家不同即敌人 |
| **玩家名** | `FString PlayerState + 0x388` | UTF-16 |
| **视角 Pitch** | `float  LocalPawn + 0x678` | 与相机 rotation 完全一致 |
| **视角 Yaw** | `float  LocalPawn + 0x67C` | 同上；自瞄写这两个 |

## 四、功能状态

| 功能 | 状态 |
|---|---|
| ESP 方框（2D/3D/转角/填充） | ✅ |
| 名字 / 距离 / 骨骼 / 武器 / 视角条 | ✅ |
| 血条（0~70，随伤害变化） | ✅ |
| 队友过滤（`显示队友` 默认关） | ✅ |
| 死亡过滤（尸体不画、不锁） | ✅ |
| 自瞄（准星最近优先，写 0x678/0x67C） | ✅ |
| 无扩散 / 无后坐力 / FOV 圈 | 已接菜单（效果未逐一验证） |
| 杂项 FOV 修改 | 已接菜单（未验证） |

## 五、编译

```powershell
# 外挂（用户态）
powershell -ExecutionPolicy Bypass -File F:\dsh\32\Asgard_Polygon-main\build_manual.ps1
# 内核驱动
powershell -ExecutionPolicy Bypass -File F:\dsh\32\Asgard_Polygon-main\build_kernel.ps1
# KDMapper
powershell -ExecutionPolicy Bypass -File F:\dsh\kdmapper-master\build_kdmapper.ps1
```

编译前必须**先杀 `Asgard_Polygon.exe`**，否则 LNK1104（exe 被占用）。
源码含中文，`build_manual.ps1` 已加 `/utf-8`，不要去掉。

## 六、目录

```
F:\dsh\32\Asgard_Polygon-main\
├─ Asgard_Polygon\Asgard_Polygon\Kernel\     驱动源码 + PolygonMemory.sys
├─ Asgard_Polygon\Asgard_Polygon\src\        外挂源码
│   ├─ Thread\engine_thread.cpp              读取链 + 存活过滤 + dump 热键
│   ├─ Features\aimbot.cpp                   自瞄（准星最近 + 写 0x678/0x67C）
│   ├─ Features\visuals.cpp                  ESP 绘制
│   └─ Menu\gui.cpp                          中文菜单
├─ Asgard_Polygon\x64\Release\Asgard_Polygon.exe
├─ build_manual.ps1 / build_kernel.ps1 / run_cheat.bat
└─ README-OPERATION.md
```

## 七、调试工具（保留）

- **鼠标侧键 4/5**：把当前锁定目标 + 3 个活人的
  `actor(0x1000)` / `PlayerState(0x600)` / `HealthComponent(0x400)` / `Mesh(0x800)`
  十六进制写入 `F:\dsh\32\Asgard_Polygon-main\actor_dump.txt`。
- 游戏更新导致偏移失效时，用它对比"活人 vs 尸体 / 敌人 vs 队友"的字节差异，可快速重新定位。
---

## 八、鸣谢

- **原始项目：[MrReekoFTWxD / Asgard_Polygon](https://github.com/MrReekoFTWxD/Asgard_Polygon)**
  —— 本项目的 ESP / 自瞄 / ImGui 菜单 / driver 抽象层全部来自他的开源实现，
  本仓库只是把目标适配到 POLYGON、改走内核驱动路径并重新推导了当前版本的偏移。非常感谢。
- [KDMapper](https://github.com/TheCruZ/kdmapper) —— 手动映射驱动。
- [GSpots](https://github.com/Do0ks/GSpots) —— 定位 `GWorld` / `GNames` 时用的 UE dump 工具。
