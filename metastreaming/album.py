from dataclasses import dataclass, field


@dataclass
class Track:
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
class Album:
    title: str | None = field(default=None)
    upc: str | None = field(default=None)
    label: str | None = field(default=None)
    release_date: str | None = field(default=None)
    artist: list[str] = field(default_factory=list)
    tracks: list[Track] = field(default_factory=list)

    def print(self) -> None:
        print(self.title)
        print("; ".join(self.artist))
        for track in self.tracks:
            print("{}\\".format(track.title) + "; ".join(track.artist))
