from enum import Enum, auto
from uuid import UUID, uuid3


class MetadataProvider(object):
    class Names(Enum):
        DEEZER = auto()

    _providers: dict[Names, tuple] = {
        Names.DEEZER: (
            UUID("67e48b9e-dd7e-11ef-9282-325096b39f47"),
            UUID("0d376a2a-dd80-11ef-90e7-325096b39f47"),
            UUID("d1957bc9-dab9-4ced-9f31-d4f963efe34b"),
            UUID("64d6b991-d489-4196-bf4f-d537b0249757"),
            UUID("85658c83-9524-4e0f-ae00-178448e07a76"),
            UUID("db451a77-193c-42e9-a6ef-f59637536b08")
        )
    }

    def __init__(self, provider_name: Names, actual_id: str = "") -> None:
        self.actual_id: str = actual_id
        self._release_ns: UUID = self._providers[provider_name][0]
        self._releasegroup_ns: UUID = self._providers[provider_name][1]
        self._artist_ns: UUID = self._providers[provider_name][2]
        self._label_ns: UUID = self._providers[provider_name][3]
        self._track_ns: UUID = self._providers[provider_name][4]
        self._recording_ns: UUID = self._providers[provider_name][5]

    def _generate_UUID(self, namespace: UUID, id: str | None = None):
        if id is None:
            id = self.actual_id
        return uuid3(namespace, str(id))

    def generate_release_UUID(self, id: str | None = None) -> UUID:
        return self._generate_UUID(self._release_ns, id)

    def generate_releasegroup_UUID(self, id: str | None = None) -> UUID:
        return self._generate_UUID(self._releasegroup_ns, id)

    def generate_artist_UUID(self, id: str | None = None) -> UUID:
        return self._generate_UUID(self._artist_ns, id)

    def generate_label_UUID(self, id: str | None = None) -> UUID:
        return self._generate_UUID(self._label_ns, id)

    def generate_track_UUID(self, id: str | None = None) -> UUID:
        return self._generate_UUID(self._track_ns, id)

    def generate_recording_UUID(self, id: str | None = None) -> UUID:
        return self._generate_UUID(self._recording_ns, id)
