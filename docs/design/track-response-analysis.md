# Track Response Shapes — Additional Tags & Pipeline Optimization

> Analysis requested after adding the [track](../reference/deezer/track.md) and [genre](../reference/deezer/genre.md) documentation fragments plus the `examples/deezer/track_dzr.json` and `examples/deezer/album_tracks_dzr.json` artifacts. Evidence: those fragments/artifacts, [../reference/picard/basic-tags.md](../reference/picard/basic-tags.md), [../reference/mp3tag/tags.md](../reference/mp3tag/tags.md), [musicbrainz-deezer-mapping.md](musicbrainz-deezer-mapping.md), [explicit-tag-analysis.md](explicit-tag-analysis.md). Status: **decided and implemented (Stage 9)** — verdicts in §4.

## 1. The three track-data shapes

Deezer exposes per-track data in three shapes with different field coverage (verified against the example artifacts):

| Field group | `album` embedded `tracks.data` | `GET /album/{id}/tracks` | `GET /track/{id}` |
| :-- | :-- | :-- | :-- |
| `id`, `title`, `title_short`, `title_version`, `link`, `duration`, `rank`, `explicit_lyrics`, `explicit_content_lyrics`/`_cover`, `preview`, `md5_image`, `readable` | ✓ | ✓ | ✓ |
| `track_position`, `disk_number`, `isrc` | ✗ | **✓** | ✓ |
| `contributors` (multi-artist list with roles) | ✗ | ✗ | **✓ only** |
| `bpm`, `gain`, track-level `release_date` | ✗ | ✗ | ✓ |
| `available_countries`, `track_token`, `alternative`, `unseen` | ✗ | ✗ | ✓ |
| `artist` object | `{id, name, tracklist, type}` — **no `role`** | `{id, name, tracklist, type}` — **no `role`** | `{id, name, link, share, picture…, nb_album, nb_fan, radio, tracklist, role}` |

The example artifacts make the differences concrete: `album_tracks_dzr.json` (album `12400342`) has `isrc`/`disk_number`/`track_position` on every track but neither a `contributors` key nor a `role` on any artist object; `track_dzr.json` (track `3135553`, "One More Time") is the only shape with `contributors` — which is what makes featuring/remix credits representable as `artist-credit`.

## 2. Additional tags — assessment

Fields not yet consumed by the pipeline, checked against predefined Picard tags and file-format mappings:

| Candidate | Predefined Picard tag? | Verdict |
| :-- | :-- | :-- |
| `bpm` (track, float) | **Yes** — `bpm` is in Picard's "Tags Not Provided from MusicBrainz Data" set (explicitly sanctioned for plugin population) and has standard mappings in every format: `TBPM` (ID3v2.3/2.4), `tmpo` (MP4), `BPM` (Vorbis/APE), `T=30 BPM` (Matroska) per the Mp3tag reference | **Preserved** (user decision). Mapped onto the synthetic node (`bpm` > 0 only — Deezer's `0` means unknown) and promoted to `metadata["bpm"]` by `track_metadata_processor`. Integral values are normalized to integer strings (MP4's `tmpo` is an int atom); fractional values keep their precision — note that Picard's MP4 writer silently skips non-integer values for int atoms (`except ValueError: pass`), so fractional BPM reaches every format except MP4. See [../reference/multi-value-tags.md](../reference/multi-value-tags.md) for the serialization note. |
| `gain` (track, float) | No | **Drop.** Deezer's signal-strength value is not ReplayGain-compliant (no unit, different reference level); mapping it to `replaygain_track_gain` would write misleading data into a workflow-sensitive tag. |
| track `release_date` (date) | No (Picard has no per-track release-date tag) | **Drop.** Semantics mismatch: Deezer's value is the track's digital release date; Picard's `_recording_firstreleasedate` derives from MusicBrainz release relationships — feeding it from Deezer would produce script-visible values of a different notion. |
| `available_countries`, `track_token`, `alternative`, `unseen` | No | **Drop.** Service/session state; no archival or player value. |
| `preview`, `rank`, `readable`, `title_short`, `title_version`, `link`, `share` | No | **Drop** — already classified in [explicit-tag-analysis.md](explicit-tag-analysis.md) §4. |
| Genre object (`id`, `picture` family) | No | **Drop.** Only `genres.data[].name` is consumed (→ `genre`); genre artwork/ids have no tag value. The `genre/artists` / `genre/radios` connections are not exercised. |

## 3. Pipeline optimization — assessment

Current per-album request pattern: **1× `GET /album/{id}` + N× `GET /track/{id}`** (parallel album tasks, `rate_limit_ms` floor on `api.deezer.com`).

**Possible switch:** replace the N per-track calls with a **single `GET /album/{id}/tracks`** (2 requests total). `DeezerAPIHelper.get_tracklist_by_id()` already exists for it (currently unused). What the node builder consumes would all be available: `id`, `title`, `duration`, `track_position`, `disk_number`, `isrc`, `explicit_lyrics`, `artist`.

| | Keep fan-out (status quo) | Switch to `/album/{id}/tracks` |
| :-- | :-- | :-- |
| Requests per album (N tracks) | N + 1 | **2** |
| Latency (15-track album, `rate_limit_ms` = 100) | ~1.5 s rate-limit floor + N round-trips | ~1 request ≈ one round-trip |
| Featuring / remix credits (`contributors` → `artist-credit`) | **preserved** | **lost** — artist-credit degrades to the single main artist |
| `bpm` availability (if adopted, §2) | ✓ | ✗ |
| Failure surface | N tasks (cancels cleanly per [../dataflow.md](../dataflow.md) §7) | 1 task |
| Code churn | none | node assembly rework + regression tests |

**Recommendation — accepted (user decision): keep the per-track fan-out.** Featuring-artist credits are permanent data quality visible in every tag the user writes (`artist`, `artists`, `artistsort`), while the request reduction is transient speed on an already-parallel, rate-controlled path. The switch becomes a strict win only if Deezer ever adds `contributors` to the tracklist response — that condition is the documented trigger, and `get_tracklist_by_id()` is already in place for it.

## 4. Verdicts (user decision, Stage 9)

1. **Keep requesting through `/track/{id}`** — implemented (status quo retained; §3 switch criteria recorded as the future trigger).
2. **Preserve the BPM tag when greater than 0** — implemented: `bpm` mapped onto the synthetic node (falsy `0` skipped by the value-skipping iterator) and promoted by `track_metadata_processor` with integer normalization; covered by `test/meta_streaming/test_explicit_tag.py` (float, integral, zero, and end-to-end cases).
3. **Use the Deezer genre list for the `genre` tag as a list** — implemented via a fix: the synthetic node's genres previously carried `count: 1`, which fell below Picard's default "Minimal genre usage" (`min_genre_usage = 90`) filter in `Track._genres_to_metadata`, so the accumulated list never materialized as a tag. The node now emits `count: 100` (the option's upper bound), letting the whole Deezer genre list pass as an alphabetically ordered, `max_genres`-capped multi-value `genre` tag. Serialization of list tags is documented in [../reference/multi-value-tags.md](../reference/multi-value-tags.md).
4. **Preserve Deezer-specific ID tags under the naming convention `{provider}_{type}_{id}_id`** — implemented by renaming the metadata tags: `deezer_albumid` → `deezer_album_id`, `deezer_trackid` → `deezer_track_id`, and the search-dialog's `deezer_albumartistid` → `deezer_albumartist_id` (stamp, processor, cover-art lookup, search columns/load path, and the synthetic node keys renamed in lockstep). Sessions saved before the rename restore nodes with the old `deezer_trackid` node key — reload an album once to regain per-track provenance on those. Future providers follow the same convention (`spotify_album_id`, …).
5. **Document list serialization** — added [../reference/multi-value-tags.md](../reference/multi-value-tags.md): internal list representation, per-format write behavior (ID3v2.4 null-separated frame values vs. the ID3v2.3 join character, MP4 list atoms with int-atom caveats, repeated Vorbis comments, ASF/APE), and the display-joiner distinction (`MULTI_VALUED_JOINER = '; '`).