from enum import StrEnum
from typing import ClassVar
from uuid import (
    UUID,
    uuid5,
)


class Provider(StrEnum):
    DEEZER = "deezer"
    SPOTIFY = "spotify"
    TIDAL = "tidal"
    QOBUZ = "qobuz"
    APPLE_MUSIC = "apple_music"


class EntityType(StrEnum):
    RELEASE = "release"
    RELEASE_GROUP = "release_group"
    ARTIST = "artist"
    LABEL = "label"
    TRACK = "track"
    RECORDING = "recording"


# Pregenerated root base UUID for each metadata provider.
# Entity type namespaces and final item UUIDs are derived dynamically from these.
PROVIDER_ROOT_UUIDS: dict[Provider, UUID] = {
    Provider.DEEZER: UUID("67e48b9e-dd7e-11ef-9282-325096b39f47"),
    Provider.SPOTIFY: UUID("138a0f0d-ef34-4b82-9382-f5421d8b2e11"),
    Provider.TIDAL: UUID("9a823b12-9c12-4211-a832-11849a029312"),
    Provider.QOBUZ: UUID("4c312984-7a11-490b-923a-f11182743810"),
    Provider.APPLE_MUSIC: UUID("8a2e1932-b012-411a-8219-c4391a827402"),
}


class MetadataProvider:
    """Generates deterministic UUIDs for streaming entities using two-tier namespace hashing.

    1. Entity namespace = uuid5(PROVIDER_ROOT_UUID, entity_type)
    2. Item UUID = uuid5(entity_namespace, item_id)
    """

    # Backward compatibility alias
    Names: ClassVar[type[Provider]] = Provider

    def __init__(self, provider: Provider | str, actual_id: str = "") -> None:
        try:
            self.provider: Provider = Provider(provider)
            self._root_uuid: UUID = PROVIDER_ROOT_UUIDS[self.provider]
        except (ValueError, KeyError) as e:
            raise ValueError(f"Unknown provider: {provider}") from e
        self.actual_id: str = str(actual_id)

    def get_entity_namespace(self, entity_type: EntityType | str) -> UUID:
        """Derive namespace UUID for a specific entity type under this provider."""
        entity_str = entity_type.value if isinstance(entity_type, EntityType) else str(entity_type)
        return uuid5(self._root_uuid, entity_str)

    def generate_uuid(self, entity_type: EntityType | str, item_id: str | int | None = None) -> UUID:
        """Generate a deterministic item UUID for an entity type and ID."""
        target_id = str(item_id) if item_id is not None else self.actual_id
        entity_ns = self.get_entity_namespace(entity_type)
        return uuid5(entity_ns, target_id)

    # Convenience methods for standard entity types
    def generate_release_UUID(self, item_id: str | int | None = None) -> UUID:
        return self.generate_uuid(EntityType.RELEASE, item_id)

    def generate_releasegroup_UUID(self, item_id: str | int | None = None) -> UUID:
        return self.generate_uuid(EntityType.RELEASE_GROUP, item_id)

    def generate_artist_UUID(self, item_id: str | int | None = None) -> UUID:
        return self.generate_uuid(EntityType.ARTIST, item_id)

    def generate_label_UUID(self, item_id: str | int | None = None) -> UUID:
        return self.generate_uuid(EntityType.LABEL, item_id)

    def generate_track_UUID(self, item_id: str | int | None = None) -> UUID:
        return self.generate_uuid(EntityType.TRACK, item_id)

    def generate_recording_UUID(self, item_id: str | int | None = None) -> UUID:
        return self.generate_uuid(EntityType.RECORDING, item_id)
