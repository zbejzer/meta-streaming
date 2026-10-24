# Known Limitations & Hazards

> Consolidated, user-facing summary of what does not (yet) work or behaves unexpectedly. Each item points to the design docs that verified it and to the roadmap stage that addresses it where applicable.

## 1. Synthetic MBIDs interact with MusicBrainz-bound flows

The plugin's deterministic UUIDs ([uuid-scheme.md](uuid-scheme.md)) are well-formed and pass Picard's `mbid_validate()`, but they do **not exist** in the MusicBrainz database. Verified consequences:

| Flow | Consequence | Mitigation / plan |
| :-- | :-- | :-- |
| Re-adding a saved file to Picard (with "ignore MBIDs" off, the default) | Picard looks up the synthetic `musicbrainz_albumid` via the real MB web service → 404 | Roadmap Stage 7: optional `save_synthetic_mbids` option with pre-save stripping (preserving pre-existing MBIDs) |
| Metadatabox album/artist lookup | Opens musicbrainz.org pages for synthetic IDs → nonexistent pages | Inherent to synthetic IDs; not planned for removal |
| ISRC submission / AcoustID fingerprint submission | Payloads keyed on `musicbrainz_recordingid` would submit synthetic IDs to MusicBrainz/AcoustID | Avoid submitting files tagged from streaming metadata; Stage 7 stripping reduces the risk |
| Cover art on album load | `CaaReleaseGroup` fires **one** CAA JSON request per load at the synthetic release-group UUID; the 404 is silently swallowed — one wasted request, no user-visible error. The release-level CAA provider skips pre-network (no `cover-art-archive` key on the node) | Accepted cost; eliminating it would require a genuine MBID (rejected — see below) |

A genuine release-group MBID was explicitly rejected as a fix: streaming-only releases are not allowed in MusicBrainz, the lookup adds a real-MB request per album, and a mismatch could tag artwork from the wrong release group. Rationale in [design/cover-art-piggyback-mechanism.md](design/cover-art-piggyback-mechanism.md) §8.

## 2. Cover art needs a manual step (current state)

The custom `DeezerCoverArtProvider` is unknown to Picard's default `ca_providers` list, so it registers **disabled** (position 666) and stays off until manually ticked in Options → Cover Art — and even when enabled it runs last. Until Stage 6 lands, expect no Deezer artwork unless you enable the provider yourself.

Stage 6 (planned) removes the custom provider and delivers artwork through the native, default-enabled **UrlRelationships** ("Allowed Cover Art URLs") provider by injecting a `cover art link` URL relation into the synthetic release node — no user action required. Full mechanism proof: [design/cover-art-piggyback-mechanism.md](design/cover-art-piggyback-mechanism.md). Caveat that will remain: users who disabled "Allowed Cover Art URLs" get no Deezer artwork (an explicit user choice, same as for MusicBrainz releases).

## 3. `tag_explicit` needs a load (or re-parse) to take effect

The option (title "Tag explicit tracks (explicit)") gates the track metadata processor added in [Stage 8](roadmap.md): explicit tracks get the user-visible `explicit` tag (`"1"`) — editable in the metadata box, scriptable as `%explicit%`, and written through Picard's native freeform path (`TXXX:explicit` on MP3, `----:com.apple.iTunes:explicit` on MP4, `EXPLICIT` on Vorbis, freeform on APEv2 and WAV's ID3 chunk). The same processor preserves `deezer_track_id` per track. Behavioral notes: the option is evaluated at parse time, so toggling it requires a reload of the album (or a session re-parse) to take effect; WMA (ASF) files do not carry either tag — Picard's ASF writer is restricted to known `WM/…` names (`asf.py:331`). Decision record with the full field assessment: [explicit-tag-analysis.md](design/explicit-tag-analysis.md).

## 4. Metadata fidelity differences vs. MusicBrainz

Data present in MusicBrainz but absent (or flattened) in Deezer — therefore not in the synthetic node:

- **Contributor roles flattened**: Deezer roles beyond `Main` (e.g. featuring) become plain `artist-credit` entries joined with `", "` / `" & "`; no `joinrelation` info.
- **Artist nodes are minimal**: `sort-name` equals `name`, `disambiguation` is empty — no MB-style artist metadata.
- **Genres are count-100 by design**: the synthetic node emits the Deezer genre list with `count: 100` so it passes Picard's default "Minimal genre usage" filter (90) and materializes as the multi-value `genre` tag (Stage 9; Deezer has no folksonomy counts, and all counts are equal so the list is ordered alphabetically and capped by `max_genres`).
- **Release context missing**: no country, packaging, language/script, barcode beyond UPC, disambiguation, or release status beyond the hardcoded `"Official"`.
- **Single ISRC per track** (Deezer exposes one string; MB recordings can carry several).
- **Release types limited** to Deezer's `record_type` (`album`/`single`/`ep` → `primary-type` → `~primaryreleasetype`/`releasetype`); no secondary types.
- **Label name only** — no catalog number (Deezer doesn't expose one), no label MBID (removed by design).
- Deezer-only data (`fans`, `available`, `preview` URLs, `rank`, per-track explicit-content granularity, `title_short`/`title_version`, `gain`) is **dropped** — nothing in Picard consumes it (verified in the [mapping report](design/musicbrainz-deezer-mapping.md)). `bpm` is preserved when Deezer reports a value `> 0` (Stage 9); track-level `release_date` was assessed and dropped ([track-response-analysis.md](design/track-response-analysis.md) §2).

## 5. Smaller behavioral notes

- **Search thumbnails always use `medium` size** regardless of the `cover_size` option (the option only governs full-resolution artwork).
- **`musicbrainz_trackid == musicbrainz_recordingid`** on every track — the recording node intentionally reuses the track UUID ([uuid-scheme.md](uuid-scheme.md) §4). Harmless for tagging/matching; relevant only if you diff tags against a genuine MB tagging of the same album.
- **Search is album-only** — no artist or track search entry points exist.
- **Multi-disc albums** are reconstructed from `disk_number`/`track_position` with a hardcoded `Digital Media` medium format; empty slots are padded if Deezer numbering has gaps.
- **Advanced search syntax** (`artist:"…" album:"…"`) is only used when Picard's "Use advanced search syntax" option is enabled; otherwise the raw query text is sent (quotes stripped) and results are broader.
- **No offline caching** — every load hits the Deezer API (within the rate limit); session files, however, persist the synthetic node, so *reloading* a session does not re-request the album.

None of these are regressions of the adapter design; they reflect either Deezer's data model or deliberate minimization choices, each traceable in the [mapping report](design/musicbrainz-deezer-mapping.md).