# MetaStreaming Plugin Roadmap

This document outlines the development roadmap and migration plan for the MetaStreaming (Deezer API) Picard v3 plugin.

---

## Overview & Architecture Goals

The primary goal of this plugin is to allow MusicBrainz Picard users to search for and load album metadata from Deezer (and future streaming services) as a direct alternative to MusicBrainz.

Because Picard's domain model is built around MusicBrainz UUIDs and schemas, the plugin utilizes a **Synthetic MusicBrainz Adapter** pattern:
1. **Dynamic Two-Tier UUID Derivation**: Generates stable, collision-free UUIDs (`uuid5`) for streaming entities across multiple providers:
   - **Provider Root Namespace**: Each streaming provider (Deezer, Spotify, Tidal, Qobuz, Apple Music) has one pregenerated root UUID.
   - **Entity Namespace**: Entity-type namespaces (`release`, `release_group`, `artist`, `label`, `track`, `recording`) are derived dynamically: `uuid5(provider_root_uuid, entity_type)`.
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
- [x] **Cover Art Provider (`DeezerCoverArtProvider`)**: Registered a dedicated cover art provider that fetches full-resolution XL artwork from Deezer (`size=xl`). This sets `front_image_found = True` and eliminates CAA 404 errors on synthetic UUIDs.
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
  - Mapped explicit content tags (`~explicit = '1'`) based on `explicit_lyrics`.
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
