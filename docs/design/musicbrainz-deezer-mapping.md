# MusicBrainz vs. Deezer Album API Mapping Report

This document maps fields from the MusicBrainz API release response (`album_mb.json`) to the equivalent Deezer API album response (`album_dzr.json`).

## Deezer Field Classification Audit

Verified against Picard 3.0.2 source (`picard/mbjson.py`, `picard/album.py`, `picard/tagger.py`, format tag mappings and the Picard tag mapping table). Every key produced by the plugin's synthetic release node — or **dropped** (never enters the synthetic node). Source functions: `album_to_mb_release()`, `_mb_track_from_track()`, `_artist_credit_from_contributors()`.

### Album node (`album_dzr.json` → `album_to_mb_release()`)

| Deezer field | Classification | Resulting tag / note |
| :-- | :-- | :-- |
| `id` | mapped & consumed | → synthetic release MBID → `deezer_albumid`, `musicbrainz_albumid` |
| `title` | mapped & consumed | `title`, plus `release-group.title` |
| `upc` | mapped & consumed | `barcode` |
| `release_date` | mapped & consumed | `date` |
| `label` | mapped & consumed (name only) | `label`; **`id` inside the label node was mapped but has zero consumers** — `label_info_from_node()` reads only `name` / `catalog-number`; no `musicbrainz_labelid` tag exists. Removed by the minimization. |
| `genres.data[].name` | mapped & consumed | `genre` / `~genres` (Picard reads only `name` and `count`; `genres[].id` is never consumed, even from genuine MB responses) |
| `record_type` | mapped & consumed | `release-group.primary-type` → `releasetype` |
| `contributors` / `artist` | mapped & consumed | `artist-credit` (roles flattened; joinphrase computed by the plugin) |
| `tracks.data` | mapped & consumed | drives per-track detail requests → `media[].tracks[]` |
| `asin` (hardcoded `None`) | mapped but ignored | falsy → skipped by `_node_skip_empty_iter()`; **removable dead weight** |
| `status` (hardcoded `"Official"`) | mapped & consumed | `releasestatus` |
| `cover_*`, `md5_image` | dropped | not carried on the node; artwork is delivered by the native `UrlRelationships` provider through an injected `cover art link` URL relation (Stage 6, planned — previously handled by the now-removed-from-plan `DeezerCoverArtProvider` via `deezer_albumid`) |
| `fans`, `available`, `nb_tracks`, `explicit_content_cover`, `explicit_content_lyrics`, `explicit_lyrics`, `link`, `share`, `tracklist`, `type`, `genre_id` | dropped | consumed by the search dialog or ignored; nothing in `mbjson.py` reads them |

### Track node (`_mb_track_from_track()`)

| Deezer / synthetic key | Classification | Resulting tag / note |
| :-- | :-- | :-- |
| `id` | mapped & consumed | synthetic track MBID → `musicbrainz_trackid` (TracksCache matching); recording node inherits it (`recording.id`) → `musicbrainz_recordingid` |
| `title` (*→ `deezer_trackid`, kept for round-tripping*) | mapped & consumed | `deezer_trackid` preserved on the node |
| `duration` | mapped & consumed | `length` (×1000 to ms) → `~length` |
| `track_position` | mapped & consumed | `position` / `number` → `tracknumber` |
| `disk_number` | mapped & consumed | drives `media[]` disc grouping → `discnumber` / `totaldiscs` |
| `contributors` / `artist` | mapped & consumed | track `artist-credit` → `artist`, `artists` |
| `isrc` | mapped & consumed | `recording.isrcs`  → `isrc` |
| `explicit` (`explicit_lyrics`) | **mapped but ignored** | `track_to_metadata()` has no `explicit` branch; `~explicit` does not exist in Picard core. The `tag_explicit` option promises `~explicit` but the pipeline never produces it — needs a track metadata processor or an option-title rewrite. |
| `recording.relations = []` | kept (not dead weight) | **Functionally required:** with "use track relationships" enabled, `_needs_track_relationships()` returns `MISSING_TRACK_RELS` when the key is absent, triggering real MB recording lookups that 404 on synthetic IDs. |
| `title_short`, `title_version`, `rank`, `preview`, `readable` | dropped | not represented in the synthetic node; nothing in `mbjson.py` consumes them |
| `explicit_content_cover`, `explicit_content_lyrics` (per-track) | dropped | only the boolean `explicit_lyrics` is ever consulted |

## Synthetic MBID Necessity Audit

Only these synthetic UUIDs are generated and carried into Picard's state. Consumer traces verified in `picard/mbjson.py`, `picard/album.py`, `picard/tagger.py`, cover art providers, and every format's tag mapping.

### Required — hard consumers exist

| Entity → tag | Consumers |
| :-- | :-- |
| release → `musicbrainz_albumid` | Album dict key (`tagger.py`); release-redirect check (`album.py`); file placement on re-add; CAA release cover art; metadatabox album lookup; search dialogs; all format mappings |
| release group → `musicbrainz_releasegroupid` | Hard access `get_release_group_by_id(rg_node["id"])` (`album.py`); CAA-RG cover art; RG lookups; format mappings |
| artist → `musicbrainz_artistid` / `musicbrainz_albumartistid` | Hard access `n["artist"]["id"]` in `artist_credit_to_metadata` (`mbjson.py`); album artist node dict (`album.py`); VA checks; track matching; format mappings |
| track → `musicbrainz_trackid` | `track_to_metadata` (`mbjson.py`); TracksCache file matching; format mappings |
| recording → `musicbrainz_recordingid` | Hard access `Track(track_node["recording"]["id"], …)` (`album.py`); TracksCache; AcoustID update; ISRC submission; file loading; format mappings |

### Removed — zero consumers

- **label** (`label-info[].label.id`): `label_info_from_node()` reads only `name` / `catalog-number`; there is no `musicbrainz_labelid` tag in core or in the Picard tag mapping table. Also absent from genuine-response consumption (`album_mb.json`'s `label-info[].label.id` is ignored in exactly the same way).
- **recording (separate UUID)**: `generate_recording_UUID()` was never called — the recording node inherits the track UUID via `dict(track)`.

Picard likewise consumes none of `genres[].id` or `media[].id` from genuine MB responses, so these were never candidates for synthetic generation.

## Hazards of Synthetic MBIDs

All verified; they motivate the Stage 7 pre-save stripping work.

1. **MB WS 404s:** synthetic UUIDs pass `mbid_validate()` (hex-format regex), so re-adding saved files (default `ignore_file_mbids=False`) triggers real `load_album()` lookups that 404.
2. **CAA-RG 404:** only `CaaReleaseGroup` ever hits the network — the release-level CAA provider checks for the non-existent `cover-art-archive` node key and skips *before any request*. The RG-level request 404s but is silently swallowed (`ignore_json_not_found_error = True`), so there is no user-visible error; eliminating it would require a genuine RG MBID (rejected — streaming releases are not allowed in the MB database). Stage 6's UrlRelationships piggyback additionally removes the custom `DeezerCoverArtProvider` (unknown to the `ca_providers` defaults → disabled at position 666 until manually ticked, and running last even when enabled).
3. **Dead web links:** metadatabox `LOOKUP_TAGS` opens musicbrainz.org pages for synthetic IDs → nonexistent pages.
4. **Submission pollution:** ISRC submission and AcoustID fingerprint submission key payloads on `recording_id` / `musicbrainz_recordingid` — synthetic IDs would be sent to MusicBrainz/AcoustID.
5. **Tag propagation:** the tag mapping table confirms the required synthetic MBIDs *above* are exactly the ones written to files, in every format (ID3v2, Vorbis, APEv2, MP4, ASF, RIFF INFO) — the removed label UUID never had a file-level representation, so its removal touches no file format.

## Field Mapping Table

| MusicBrainz Field (`album_mb.json`) | Deezer Field (`album_dzr.json`) | Description / Notes |
| :--- | :--- | :--- |
| `id` | `id` *(implicit in track/artist structure, URL)* | MusicBrainz Release MBID vs Deezer numeric album ID. |
| `title` | `title` | Release title (e.g., *"Hello, I Must Be Going (2016 Remaster)"*). |
| `artist-credit` | `artist` / `contributors` | Main artist credits and contributors (e.g., *Phil Collins*). |
| `barcode` | `upc` | Universal Product Code / EAN barcode. |
| `date` | `release_date` | Release date (MusicBrainz uses `date`, Deezer uses `release_date`). |
| `label-info` / `label-info-list` | `label` | Record label associated with the release (e.g., *Rhino*). |
| `media` → `track-list` | `tracks` / `tracks.data` | Track listings, track titles, and positions. |
| `media` → `track-list` → `length` | `tracks.data.duration` | Track duration in milliseconds (MusicBrainz) vs seconds (Deezer). |
| `release-group` → `primary-type` | `record_type` | Release/record type (e.g., `"Album"`). |
| `genres` / `tags` | `genres` | Musical genres/tags associated with the release or artist. |

---

## Missing Information Analysis

### 1. Information Present in Deezer but **Missing** in MusicBrainz:
- **Streaming & Fan Metrics:** Fan count (`fans`), explicit content flags (`explicit_lyrics`, `explicit_content_lyrics`, `explicit_content_cover`), and availability status (`available`).
- **Media Previews & Links:** 30-second audio preview streaming URLs (`preview`), web links/sharing URLs (`link`, `share`, `tracklist`).
- **Artwork Hashes / URLs:** Deezer cover image identifiers (`cover`, `cover_small`, `cover_medium`, `cover_big`, `cover_xl`, `md5_image`), whereas MusicBrainz relies on Cover Art Archive (CAA) IDs/URLs.

### 2. Information Present in MusicBrainz but **Missing** in Deezer:
- **Unique Identifiers (MBIDs):** Globally unique identifiers for the release (`id`), release group, artist (`artist.id`), recordings (`recording.id`), and tracks (`track.id`).
- **Detailed Release Metadata:** Country of release (`country`), release status (`status`: *Official*, etc.), packaging info, disambiguation comments (`disambiguation`), and explicit ISO language/script codes.
- **ISRC & ASIN Codes:** International Standard Recording Codes (ISRCs) for individual tracks and Amazon Standard Identification Numbers (ASINs) where linked.
- **Rich Tagging & Folksonomy:** Detailed tag counts and genre frequency lists (`tags` with counts).
