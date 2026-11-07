#include "pch.h"
#include "game.h"

FNamePool* NamePoolData = nullptr;
std::vector<AActor> Actors;
static std::mutex ActorsMutex;

std::vector<AActor> snapshot_actors()
{
	std::lock_guard<std::mutex> lock(ActorsMutex);
	return Actors;
}

void publish_actors(std::vector<AActor> actors)
{
	std::lock_guard<std::mutex> lock(ActorsMutex);
	Actors = std::move(actors);
}

namespace game
{
	uint64_t AimTarget = 0;
	FVector LocalEyePos{};
	uint64_t GWorld = NULL;
	uint64_t PersistentLevel = NULL;
	uint64_t ActorArray = NULL;
	uint64_t ActorCount = NULL;
	uint64_t OwningGameInstance = NULL;
	uint64_t LocalPlayer = NULL;
	uint64_t LocalPlayerState = NULL;
	uint64_t LocalPlayerPawn = NULL;
	uint64_t PlayerController = NULL;
	uint64_t PlayerCameraManager = NULL;
	FMinimalViewInfo CameraCachePrivate;

	uint8_t LocalPlayerTeam = NULL;
}
