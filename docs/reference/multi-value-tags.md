# Multi-Value Tags — How Lists Reach Files

> Reference note requested alongside the genre-as-list verdict in [../design/track-response-analysis.md](../design/track-response-analysis.md) (Stage 9): Picard tags carry **lists**, not comma-joined strings — but file formats serialize them differently. Relevant to every list-valued tag the plugin touches (`genre`, `artists`, `albumartists`, `label`, `isrc`, `catalognumber`, `releasetype`, and the plugin's own `deezer_track_id`/`deezer_album_id` provenance tags).

## Internal representation

Picard's `Metadata` **automatically normalizes whatever you assign** (`Metadata._set`, `picard/metadata.py`):

- Assigning a Python **list** (or any iterable) flattens it: every element is coerced with `str()` — `metadata["genre"] = [1, "Rock"]` stores `["1", "Rock"]` — and falsy elements are dropped **except** those equal to `0` or `''` (kept as `"0"`/`""`; note the `0`-equality quirk also lets `False` survive as the string `"False"` — avoid assigning raw booleans). Assigning `[]` or a single `''` removes the tag.
- A **single-element list collapses to a bare flat string**: `metadata["genre"] = ["Pop"]` stores the plain `str` `"Pop"`, not a 1-element list (a per-object memory optimization; only 2+ values are stored as `list[str]`).
- There is no pre-joined string storage anywhere: `get()` / `__getitem__` return the **display form** — all values joined on the fly with `multi_valued_joiner` (`MULTI_VALUED_JOINER = '; '`, `picard/metadata.py:61`) — which is what the UI and naive string handling see. That join never exists in storage.
- `getall()` always returns a **list** (a bare stored string is wrapped into a 1-element list), `rawitems()` likewise normalizes to `(name, [values…])` pairs — the format writers iterate `rawitems()`, so they always see lists. `items()` flattens to one `(name, value)` pair per value.

So "a Python list becomes proper flat text" holds in two senses: elements are stringified on assignment, and single-value tags are stored/handed over as plain text — while `getall()` still presents a list to callers that need one. (See the project's AGENTS.md guidance: never `get()` + `split()` on the joiner — use `getall()`.)
- Setting multiple values is done by passing a list: `metadata["genre"] = ["Pop", "Rock"]`.

## Per-format serialization on save

| Format | Behavior for a multi-value tag |
| :-- | :-- |
| ID3v2.4 (MP3, default) | One text frame per tag (`TCON`, `TXXX:…`) holding all values, serialized with **null (`\x00`) separators** inside the frame per the ID3v2.4 spec (`picard/formats/id3.py` — `tags.add(getattr(id3, frameid)(encoding=…, text=values))`) |
| ID3v2.3 (MP3, compat mode) | Multi-value frames are converted by `update_to_v23()` and the values are **joined into a single string** with the configurable `id3v23_join_with` character (default `/`, Options → Tags → ID3 Compatibility) |
| MP4 (M4A) | Native **list** inside the atom (`©gen`, `----:com.apple.iTunes:…` freeform); integer atoms (`tmpo`/BPM) take `int()`-able values only — fractional values are silently skipped by Picard's writer (`picard/formats/mp4.py`, `except ValueError: pass`) |
| Vorbis (FLAC/Ogg/Opus) | **Repeated comment keys** — one `GENRE=…` line per value; the most natural list representation |
| ASF (WMA) | Multiple values on one WM attribute |
| APEv2 | One item holding the value list |
| WAV | ID3v2 chunk (same behavior as MP3); the RIFF INFO chunk is single-valued only |

So a two-genre album tags as a real list on MP3/v2.4, MP4, FLAC and WMA — **not** `"Pop; Rock"` as one string — while ID3v2.3 files contain a single joiner-joined string because the format cannot represent lists in text frames.

## Practical consequences for this plugin

- The `genre` materialization (Stage 9 verdict: use the Deezer genre list as a list) passes a **list** to `metadata["genre"]` via `Track._genres_to_metadata` — capped by `max_genres` (default 5), filtered by `min_genre_usage`, optionally joined when `join_genres` is set (then it becomes a deliberately single-value joined string).
- The provenance tags are single-valued, so serialization differences don't affect them; they exist so users *can* build lists or URLs from them via scripts.
- When reading back (e.g., the cover-art provider's `metadata.get(…)`), single-valued keys are safe; anything potentially multi-valued must go through `getall()`.
- Tagger scripts see the joined display form for `%genre%`; `$multi()`/`%genre%` handling and `$setmulti()` exist for list-aware scripting.