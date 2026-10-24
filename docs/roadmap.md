# MetaStreaming Plugin Roadmap

This document outlines the development roadmap and migration plan for the MetaStreaming (Deezer API) Picard v3 plugin.

---

## Overview & Architecture Goals

The primary goal of this plugin is to allow MusicBrainz Picard users to search for and load album metadata from Deezer (and future streaming services) as a direct alternative to MusicBrainz.

Because Picard's domain model is built around MusicBrainz UUIDs and schemas, the plugin utilizes a **Synthetic MusicBrainz Adapter** pattern:
1. **Dynamic Two-Tier UUID Derivation**: Generates stable, collision-free UUIDs (`uuid5`) for streaming entities across multiple providers:
   - **Provider Root Namespace**: Each streaming provider (Deezer, Spotify, Tidal, Qobuz, Apple Music) has one pregenerated root UUID.
   - **Entity Namespace**: Entity-type namespaces (`release`, `release_group`, `artist`, `track`) are derived dynamically: `uuid5(provider_root_uuid, entity_type)`. *(Stage 5 minimization removed `label` and `recording` entity types — no consumers in Picard core; recording nodes reuse the track UUID.)*
   - **Item UUID**: Final entity UUIDs are hashed dynamically: `uuid5(entity_namespace, item_id)`. Adding a new streaming provider requires only adding one root UUID.
2. **Schema Translation**: Translates Deezer JSON responses into Picard's internal MusicBrainz `release_node` format.
3. **Native Matching**: Leverages Picard's file-matching engine, tagger scripts, and tagging formulas seamlessly without modifying Picard core.

---

## Phase Breakdown

### Stage 1: API v3 Migration & Stability (Completed)

- [x] **PyQt6 & API v3 Upgrade**: Converted all imports from `PyQt5` to `PyQt6` and updated Qt enum references.
- [x] **Import-time Crash Prevention**: Removed top-level assertions and dynamic global monkey-patching executed during plugin discovery.
- [x] **Plugin Lifecycle Alignment**: Implemented explicit `enable(api)` and `disable()` entrypoints with automatic registration cleanup.
- [x] **UI Persistence Fixes**: Restored `StreamingAlbumSearchDialog` header state saving and loading using `api.plugin_persist`.
- [x] **Module Import Restructuring**: Standardized on relative imports across the plugin package and removed obsolete Python 3.12-removed imports (`lib2to3`).

---

### Stage 2: Performance, Cover Art & Metadata Pipeline (Completed)

#### Step 1: Cover Art & Base Rate Control (Completed)
- [x] **Cover Art Provider (`DeezerCoverArtProvider`)**: Registered a dedicated cover art provider that fetches full-resolution XL artwork from Deezer (`size=xl`). *Superseded by Stage 6:* plugin-registered providers are unknown to the `ca_providers` defaults, so this provider stayed disabled (position 666) until manually ticked in **Options → Cover Art** — and even when enabled, one CAA release-group request still ran first and 404'd on the synthetic UUID (silently swallowed, no user-visible error). CAA itself never 404s here: the release-level provider checks for the `cover-art-archive` key and skips on synthetic nodes *before any network request*. Replaced by the native UrlRelationships piggyback — see [Stage 6](#stage-6-cover-art-delivery-via-urlrelationships-piggyback-planned) and [cover-art-piggyback-mechanism.md](design/cover-art-piggyback-mechanism.md).
- [x] **Base Rate Control**: Registered initial minimum request delay for `https://api.deezer.com` to prevent aggressive throttling.

#### Step 2: Rate Limit Configuration & Parallel Track Fetching (Completed)
- [x] **Configurable Request Rate Limit**:
  - Registered `rate_limit_ms` in `api.plugin_config` (default: `100` ms, bounds: `50` to `2000` ms).
  - Configured `ratecontrol.set_minimum_delay_for_url("https://api.deezer.com", delay_ms)` dynamically from `api.plugin_config`.
- [x] **Parallel Track Details Fetching**:
  - Replaced sequential track-by-track chain (`deque.popleft()` loop) with concurrent `api.web_service` requests.
  - Dispatches all track detail requests in parallel so Picard's network queue processes them concurrently within the configured rate limit.
  - Reduced total album loading time from 15–20 seconds to 1–2 seconds.
- [x] **Enhanced Schema Mapping**:
  - Mapped genres (`genres.data[*].name`) to `genre` / `~genres`.
  - Mapped `record_type` (`album`, `single`, `ep`) to `primary-type` / `releasetype`.
  - Mapped explicit content tags (`~explicit = '1'`) based on `explicit_lyrics`. *(Superseded by the Stage 5 audit: this never reached metadata — the node sets `track["explicit"]`, which `track_to_metadata()` ignores. Resolution decision in [Stage 5](#stage-5-mapping-audit--mbid-minimization) and [`docs/design/explicit-tag-analysis.md`](design/explicit-tag-analysis.md): the regular `explicit` tag will be materialized via a track metadata processor; implementation planned as [Stage 8](#stage-8-explicit-track-metadata-processor-planned).)*
  - Included ISRCs on tracks and recordings.
  - Populated multi-disc attributes (`position`, `track-count`, `format`, `discnumber`, `totaldiscs`).

#### Step 3: Clean Loader & Refactoring (Completed)
- [x] **Loader Decoupling**:
  - Replaced dynamic `Album.load_from_deezer` method assignment and `Tagger.deezer_api` monkey-patching with a standalone, thread-safe `load_deezer_album(api, deezer_album_id, cluster)` loader function.
  - Ensured all album tasks (`api.add_album_task` / `api.complete_album_task`) complete cleanly on both success and error.
- [x] **Scalable Multi-Provider UUID Engine (`MetadataProvider`)**:
  - Refactored `providers.py` to use a dynamic two-tier `uuid5` derivation model (`Provider` enum, `EntityType` enum, pregenerated root UUIDs per provider).
  - Scalable structure allowing new providers (Spotify, Tidal, Qobuz, Apple Music) to be added with a single root UUID definition.

---

### Stage 3: Options UI & Multi-Provider Architecture (Completed)

- [x] **Plugin Settings Page (`StreamingOptionsPage`)**:
  - Registered `StreamingOptionsPage` under `api.register_options_page()`.
  - Configurable settings UI for minimum request delay in ms (`rate_limit_ms`), preferred cover art resolution (`cover_size`), and explicit track tagging (`tag_explicit`).
  - Integrated profile override support (`in_profile=True` and `OPTIONS` page widget mapping).
- [x] **Search UI Enhancements**:
  - Search result pagination (`index` and `limit` query parameters) and "Load More (X/Total)" button in `StreamingAlbumSearchDialog`.
  - In-memory cover art thumbnail caching (`_cover_cache`) preventing duplicate network requests on scroll, column re-sort, and pagination.
- [x] **Multi-Provider Abstract Layer**:
  - Created `BaseStreamingAPIHelper` in `api_helpers.py` defining standard search, release detail, track detail, and artwork methods across providers.
  - Implemented `get_api_helper_for_provider(provider, webservice)` factory registry.
  - Generic `load_streaming_album(api, provider, album_id, cluster)` loader supporting any current or future streaming service.
  - Extensible `StreamingCoverArtProvider` in `coverart.py` fetching artwork dynamically for any streaming provider.

---

### Stage 4: Code Quality, Pythonic EAFP & Reliability Refactoring (Completed)

#### 1. Trust Picard's Plugin API Guarantees (Remove Defensive LBYL)
- [x] **Simplify `coverart.py`**:
  - Removed defensive `getattr` fallback checks (`getattr(self, "api", None)` and `getattr(self.album, "metastreaming_provider", None)`). Picard guarantees `self.api` and `self.album` on `CoverArtProvider` instances.
  - Directly accesses `self.metadata.get(f"{self.provider.value}_albumid")` and `self.api.plugin_config["cover_size"]`.
- [x] **Simplify `_finish_deezer_release` in `deezerjson.py`**:
  - Simplified provider attribute access without defensive `hasattr` guards.

#### 2. Adopt Pythonic EAFP Over LBYL & Redundant Type Checks
- [x] **Clean Up `StrEnum` Handling (`providers.py`, `album.py`, `api_helpers.py`)**:
  - Removed `isinstance(x, str)` checks (`StrEnum` instances are `str` subclasses; `Provider(x)` conversion is idempotent).
  - Replaced manual `if key not in dict: raise ValueError` guards with EAFP `try / except (ValueError, KeyError)` blocks in `providers.py` and `api_helpers.py`.
- [x] **Refactor JSON Parsing in `deezerjson.py`**:
  - Replaced nested `isinstance` and key-existence checks (in genre and contributor parsing) with EAFP `try / except (KeyError, TypeError)` blocks and list comprehensions.
  - Removed control-flow `assert` statements from async network callbacks.

#### 3. Eliminate Repeated `PluginApi.get_api()` Calls
- [x] **Explicit Context Passing**:
  - Passed `api` explicitly through callback partials (`recordings_request_finished_proxy`, `_request_track`, `_track_request_finished`), eliminating frame-inspection calls (`PluginApi.get_api()`) inside per-track async callbacks.

#### 4. Fix Concurrency & Pagination Bugs
- [x] **Parallel Track Error Handling (`deezerjson.py`)**:
  - Added `album.cancel_tasks()` on track request failure to safely cancel remaining in-flight tasks and prevent race conditions.
- [x] **Pagination Offset Update (`albumsearch.py`)**:
  - Updated `self.current_index = index` in `StreamingAlbumSearchDialog.search()` so subsequent clicks on "Load More" advance correctly (`0 -> 25 -> 50 -> 75`).

---

### Stage 5: Deezer→MusicBrainz Tag Mapping Audit & Synthetic MBID Minimization (In Progress)

> **Verification method (per user decision):** based on Picard source code (`picard/mbjson.py`, `picard/album.py`, tag mapping table) and the two API example responses only — no Picard-tagged file artifact will be provided. All consumer traces below were verified against this source tree.

- [x] **Example Artifacts for the Same Album**:
  - `examples/deezer/album_dzr.json` (Deezer API album response) and `examples/MusicBrainz/album_mb.json` (MusicBrainz API release response) kept as the field-level baseline.
  - The planned third artifact (metadata from the same album tagged within Picard, `examples/Picard/`) is **dropped**: end-to-end verification is code/API-response based instead.
- `docs/reference/MusicBrainz Picard Tag Mapping.html` (the Picard tag mapping table, 96 tag rows) used as ground truth for which MBID tags actually reach written files.
  - [x] **Deezer→MusicBrainz Node Mapping Audit** (full classification in `docs/design/musicbrainz-deezer-mapping.md` → "Deezer Field Classification Audit"):
  - Every synthetic node key produced by `album_to_mb_release()`, `_mb_track_from_track()` and `_artist_credit_from_contributors()` (`deezerjson.py`) cross-checked against what Picard actually consumes in `picard/mbjson.py` (`release_to_metadata`, `release_group_to_metadata`, `track_to_metadata`, `recording_to_metadata`, `medium_to_metadata`, `artist_credit_to_metadata`, `label_info_from_node`, `add_genres_from_node`, `add_isrcs_to_metadata`) — with the hard dictionary accesses in `picard/album.py` verified as well.
  - Synthetic node shape compared against the genuine MusicBrainz release response (`album_mb.json`): Picard consumes none of `genres[].id` / `media[].id` / `label-info[].label.id` even from genuine responses, so these never need synthetic equivalents.
  - Suspects resolved:
    - `explicit` on track nodes → **mapped; to be surfaced via processor**: `track_to_metadata()` has no `explicit` branch, so the node key alone never passes through. Resolved by analysis — a track metadata processor will set the regular `metadata["explicit"] = "1"` tag from the node flag ([Stage 8](#stage-8-explicit-track-metadata-processor-planned), decision in [`docs/design/explicit-tag-analysis.md`](design/explicit-tag-analysis.md)); it then flows through the UI, scripts, and Picard's native freeform file writes.
    - `asin: None` → **mapped but ignored**: falsy, skipped by `_node_skip_empty_iter()` before mapping; removable.
    - `relations: []` on recording nodes → **NOT dead weight — functionally required**: `_needs_track_relationships()` (`picard/album.py`) returns `MISSING_TRACK_RELS` when the key is absent and "use track relationships" is enabled, which would trigger real MB recording lookups that 404 on synthetic IDs. Keep.
    - `status: "Official"` → mapped & consumed (`releasestatus`).
    - Contributor roles other than `Main` and `explicit_content_lyrics` / `explicit_content_cover` granularity remain flattened/unused (documented, no change).
- [x] **Code-Based Pipeline Verification** (replaces the deferred Picard-tagged diff):
  - Every Deezer-sourced tag traced through the full pipeline (Deezer JSON → synthetic MB node → `mbjson` parsing → Picard metadata → written file tags) by consumer analysis; classification recorded in `docs/design/musicbrainz-deezer-mapping.md`.
  - `docs/design/musicbrainz-deezer-mapping.md` updated with the audited, verified mapping/stripping report and the synthetic-MBID hazard analysis.
- [x] **Synthetic MBID Minimization Audit (Strictly Necessary Only)** — verdicts verified, implementation applied below:
  - **Keep (hard consumers verified):**
    | UUID | → tag | Verified consumers |
    | :-- | :-- | :-- |
    | `release` | `musicbrainz_albumid` | Album dict key; release-redirect check; file-placement on re-add; CAA release cover art; metadatabox `album_lookup`; search dialogs; all format tag mappings |
    | `release_group` | `musicbrainz_releasegroupid` | Hard access `get_release_group_by_id(rg_node["id"])` (`album.py`); RG cover art; lookups; format mappings |
    | `artist` | `musicbrainz_artistid` / `musicbrainz_albumartistid` | Hard access `n["artist"]["id"]` in `artist_credit_to_metadata` (`mbjson.py`); artist node dicts in `album.py`; VA checks; track matching; format mappings |
    | `track` | `musicbrainz_trackid` | `track_to_metadata`; TracksCache-based file matching; format mappings |
    | `recording` | `musicbrainz_recordingid` | Hard access `Track(track_node["recording"]["id"], …)` (`album.py`); TracksCache; AcoustID/ISRC flows; format mappings |
  - **Remove (zero consumers):**
    - `label.id` — `label_info_from_node()` (`mbjson.py`) reads only `label.name` / `catalog-number`; no `musicbrainz_labelid` tag exists in Picard core or the tag mapping table. Drop `generate_label_UUID` call (keep `name`), `EntityType.LABEL`, and the method.
    - `generate_recording_UUID()` — dead method (never called; the recording node inherits the track UUID via `dict(track)` copy). Drop it and `EntityType.RECORDING`.
  - **Hazards documented** (motivate Stage 7): synthetic UUIDs pass `mbid_validate()`; re-adding saved files triggers real MB WS 404s; CAA release-group fires one 404 per album load (silently swallowed — the release-level CAA provider skips pre-network on synthetic nodes); metadatabox lookup opens dead musicbrainz.org pages; ISRC submission and AcoustID submission would send synthetic recording IDs to MB/AcoustID.
- [x] **Apply Synthetic MBID Minimization** (done; verified against `album_dzr.json` through the real `mbjson` parsers):
  - Removed the label UUID generation in `album_to_mb_release()` (kept `label.name`), removed `generate_label_UUID` / `generate_recording_UUID` and `EntityType.LABEL` / `EntityType.RECORDING` from `providers.py`, removed the dead `asin` placeholder.
  - Verified the minimized node end-to-end: synthetic node generation against the real example JSON, `release_to_metadata()` album-level run (album/artist MBIDs, `label`, `releasestatus` all correct), and the `_setup_release_group()` sequence (`release_group_to_metadata` → metadata copy) for the RG UUID and `~primaryreleasetype`.
- [x] **Resolve `~explicit` handling (analysis-based decision, resolved 2026-10)**:
  - The `tag_explicit` option sets `track["explicit"]`, which `track_to_metadata()` ignores; the flag alone never reaches metadata — a bridge into `Metadata` is required regardless of tag name. Full analysis in [`docs/design/explicit-tag-analysis.md`](design/explicit-tag-analysis.md), based on the vendor reference fragments (Deezer field docs, Picard basic-tags, Mp3tag field mappings) and the format writers in `picard/formats/`: the Deezer flag is **valuable as track metadata** (MusicBrainz has no advisory data; it disambiguates explicit vs edited/clean release variants), and a **regular-named `explicit` tag does reach files** through Picard's native freeform path — the same path user-added tags ("Add New Tag…" in the metadata box) take (`TXXX:explicit` ID3, `----:com.apple.iTunes:explicit` MP4, `EXPLICIT` Vorbis, APEv2 freeform, WAV ID3 chunk; dropped on WMA/ASF by its `supports_tag` restriction).
  - **Decision:** materialize `metadata["explicit"] = "1"` via a track metadata processor reading `track_node["explicit"]` — user-visible, editable in the metadata box, scriptable as `%explicit%`, written freeform. Option title's stale "(~explicit)" parenthetical becomes "(explicit)"; granular `explicit_content_*` scale stays dropped; no format-specific surgery (no `rtng` writing). Implementation planned as [Stage 8](#stage-8-explicit-track-metadata-processor-planned).
- [x] **Cover Art Provider Enablement** (verified gap, **superseded by Stage 6**): `DeezerCoverArtProvider` registers as an *unknown* provider for `ca_providers` defaults → `enabled=False` (position 666) until manually enabled in **Options → Cover Art** — and until then no cover is fetched at all, while `CaaReleaseGroup` still fires one silently-swallowed 404 per album load. Rather than surfacing or auto-enabling it, Stage 6 removes the custom provider entirely and delivers the cover through the default-enabled `UrlRelationships` ("Allowed Cover Art URLs") provider instead.

---

### Stage 6: Cover Art Delivery via UrlRelationships Piggyback (Planned)

**Design record:** [cover-art-piggyback-mechanism.md](design/cover-art-piggyback-mechanism.md) — explains why this works: a `cover art link` URL relation injected into the synthetic release node feeds Picard's default-enabled `UrlRelationships` provider ("Allowed Cover Art URLs"), which queues the image through the **same** native download/identification pipeline as CAA covers — no custom provider, no per-user enablement step.

- [ ] **Inject a `cover art link` URL relation into the synthetic release node** (`deezerjson.py`, `album_to_mb_release()`):
  - Shape: `{"target-type": "url", "type": "cover art link", "url": {"resource": <album cover URL>}}` — exactly what `CoverArtProviderUrlRelationships.match_url_relations()` matches on.
  - URL from `api_helpers.get_album_cover_url(str(node["id"]), size=...)`, honoring the existing `cover_size` plugin option (default `xl`) — thread `api` through from `recordings_request_finished_proxy()`, which already holds it.
  - Do **not** touch `recording.relations = []` on track nodes — that key is functionally required (see Stage 5: prevents `_needs_track_relationships()` from firing real MB recording lookups that 404 on synthetic IDs). Only the release node gains relations.
- [ ] **Remove the custom cover art provider**:
  - Delete `coverart.py` (`StreamingCoverArtProvider`, `DeezerCoverArtProvider`), plus its import and the `api.register_cover_art_provider(DeezerCoverArtProvider)` call in `__init__.py`.
  - Rationale: plugin-registered providers are unknown to the `ca_providers` defaults → `enabled=False` (position 666) until manually ticked in Options → Cover Art, and even then they run last. That hidden manual step is why the provider is replaced rather than fixed (mechanism doc §2).
- [ ] **Keep the `cover_size` option** — unchanged in purpose, now consumed by the relation injection instead of the removed provider.
- [ ] **Verification** (re-use the Stage 5 audit harness):
  - Synthetic node shape: exactly one relation with `target-type == "url"`, `type == "cover art link"`, and a resource built from `get_album_cover_url()` honoring `cover_size`.
  - Tag purity: re-run the node → `mbjson.release_to_metadata()` pass and confirm no new tags leak from the injected relation (the `url` relations dispatcher only maps `amazon asin` → `asin` and `license` → `license`; `cover art link` is a tag no-op).
  - Front-image assertions: the queued `CoverArtImage` is type-less ⇒ `is_front_image()` is True by definition ⇒ `maintype == 'front'` and the status bar shows "Front".
- **User-facing caveats**:
  - Requires "Allowed Cover Art URLs" (UrlRelationships) enabled — it is default-enabled; a user who disabled it gets no Deezer cover (same behavior as MB releases whose artwork arrives only via ARs).
  - `CaaReleaseGroup` still fires one silently-swallowed 404 JSON request per album load (it runs before UrlRelationships; harmless, no user-visible error — eliminating it would need a genuine RG MBID, rejected in mechanism doc §8).
  - The relation is export-persistent: it survives session reload via `_release_node_cache`, so reloads re-fetch only if the front image was cleared.

---

### Stage 7: Synthetic MBID Tag Exclusion & Verification

- [ ] **Configurable Synthetic MBID Disk Exclusion**:
  - Register `save_synthetic_mbids` in `api.plugin_config` (boolean, default: `False`, `title="Save synthetic MusicBrainz IDs to files"`, `in_profile=True`).
  - Add checkbox option control to `StreamingOptionsPage`.
- [ ] **Selective Tag Stripping in Pre-Save Processor**:
  - Register `register_file_pre_save_processor(pre_save_strip_synthetic_mbids)`.
  - Check whether `file.orig_metadata` contained pre-existing MBIDs before loading into Picard.
  - Compare current synthetic MBID tags against calculated streaming UUIDs (`MetadataProvider.generate_uuid(...)`).
  - Strip only those synthetic MBIDs that match generated values for the active streaming release, preserving any pre-existing original MBID tags that were on the file before loading into Picard.
- [ ] **RAM & UI State Preservation in Post-Save Processor**:
  - Register `register_file_post_save_processor(post_save_restore_synthetic_mbids)`.
  - Restore stashed synthetic MBIDs into `file.metadata` and `file.orig_metadata` so Picard's UI, album grouping, and status icons remain intact in RAM after file save without unsaved tag diffs.

---

### Stage 8: `explicit` Track Metadata Processor (Planned)

> Decision record: [`explicit-tag-analysis.md`](design/explicit-tag-analysis.md) — why the Deezer explicit flag is materialized as the regular, user-visible `explicit` tag (editable in the metadata box, scriptable as `%explicit%`, written through Picard's native freeform path like any user-added tag) rather than an internal `~`-variable.

- [ ] **Materialize `explicit` in track metadata**:
  - Register a track metadata processor via `api.register_track_metadata_processor()` with signature `(api, track, metadata, track_node, release_node=None)` (`picard/plugin3/api_impl.py:892`).
  - When `track_node.get("explicit")` is truthy (set by `_mb_track_from_track()` from `explicit_lyrics` under the `tag_explicit` option), set `metadata["explicit"] = "1"`; no-op otherwise (fresh `Metadata` per parse, no stale-value handling needed).
  - The tag flows through the standard paths: metadata box (visible, editable, deletable per track), tagger scripts (`%explicit%`), and file writing via the native freeform fallbacks — `TXXX:explicit` (ID3v2), `----:com.apple.iTunes:explicit` (MP4), `EXPLICIT` (Vorbis comments), freeform APEv2 item, WAV ID3v2 chunk. Not written on WMA (ASF `supports_tag` restriction) — accepted, no plugin-side bypass.
- [ ] **Option title fix**: change the checkbox title in `options.py` from "Tag explicit tracks (~explicit)" to "Tag explicit tracks (explicit)" (plain `_()` string; update the plugin translation key if one exists for it).
- [ ] **Test-first implementation** (repository guideline):
  - Write a unit test reproducing the gap: a synthetic node whose track carries `explicit: True` must produce track metadata with `explicit == "1"`; with `explicit` absent or `tag_explicit` disabled, no `explicit` key. Keep as a permanent regression test.
- [ ] **Verification**:
  - `release_to_metadata()` / `track_to_metadata()` output unchanged except the added `explicit` tag; no node mutation; no file-format code paths touched — the freeform writes are Picard's own.
  - `explicit` is the plugin's only deliberate freeform tag; everything else stays inside Picard's tag mapping (tag-purity guarantee re-scoped in the decision record).
  - Granular `explicit_content_lyrics` / `explicit_content_cover` remain dropped per the minimization audit.
  - `ruff format` + `ruff check` on touched files.
