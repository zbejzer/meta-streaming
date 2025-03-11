from enum import Enum, auto
from uuid import UUID, uuid3


class ProviderNames(Enum):
    DEEZER = auto()


class _Provider(object):
    def __init__(self, release_ns: UUID, releasegroup_ns: UUID, albumartist_ns: UUID) -> None:
        self._release_namespace: UUID = release_ns
        self._releasegroup_namespace: UUID = releasegroup_ns
        self._albumartist_ns: UUID = albumartist_ns

    def generate_release_UUID(self, id: str) -> UUID:
        return uuid3(self._release_namespace, id)

    def generate_releasegroup_UUID(self, id: str) -> UUID:
        return uuid3(self._releasegroup_namespace, id)

    def generate_albumartist_UUID(self, id: str) -> UUID:
        return uuid3(self._albumartist_ns, id)


providers: dict[ProviderNames, _Provider] = {
    ProviderNames.DEEZER: _Provider(
        UUID("67e48b9e-dd7e-11ef-9282-325096b39f47"),
        UUID("0d376a2a-dd80-11ef-90e7-325096b39f47"),
        UUID("d1957bc9-dab9-4ced-9f31-d4f963efe34b")
    )
}
