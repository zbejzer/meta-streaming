from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import IntEnum


class Item(ABC):
    @abstractmethod
    def print(self) -> None:
        pass


@dataclass
class Track(Item):
    title: str | None = field(default=None)
    isrc: str | None = field(default=None)
    release_date: str | None = field(default=None)
    track_number: int | None = field(default=None)
    disc_number: int | None = field(default=None)
    bpm: float | None = field(default=None)
    gain: float | None = field(default=None)
    artist: list[str] = field(default_factory=list)

    def print(self) -> None:
        pass


@dataclass
class Album(Item):
    title: str | None = field(default=None)
    upc: str | None = field(default=None)
    label: str | None = field(default=None)
    release_date: str | None = field(default=None)
    artist: list[str] = field(default_factory=list)
    tracks: list[Track] = field(default_factory=list)

    def print(self) -> None:
        print("{} - {}".format("; ".join(self.artist), self.title))
        for track in self.tracks:
            print("{}\\{}".format(track.title, "; ".join(track.artist)))
