# Multi-Provider Architecture & Extension Guide

> The plugin is built to support several streaming services behind one loader and one ID engine. Deezer is the implemented provider; Spotify, Tidal, Qobuz and Apple Music are pre-provisioned in the ID engine. Related docs: [uuid-scheme.md](uuid-scheme.md), [dataflow.md](dataflow.md).

## 1. The layer stack

```text
┌──────────────────────────────────────────────────────────────────┐
│ UI            StreamingAlbumSearchDialog (provider-agnostic UI)  │
├──────────────────────────────────────────────────────────────────┤
│ Loader        load_streaming_album(api, provider, album_id, …)   │
│               (album.py — knows nothing about Deezer specifics)  │
├──────────────────────────────────────────────────────────────────┤
│ Translation   deezerjson.py — provider JSON → synthetic MB node  │
│               (the only Deezer-shaped module in the load path)   │
├──────────────────────────────────────────────────────────────────┤
│ Transport     BaseStreamingAPIHelper → DeezerAPIHelper           │
│               (api_helpers.py; _API_HELPER_REGISTRY + factory)   │
├──────────────────────────────────────────────────────────────────┤
│ Identity      MetadataProvider + PROVIDER_ROOT_UUIDS             │
│               (providers.py — fully provider-generic)            │
├──────────────────────────────────────────────────────────────────┤
│ Core          Picard webservice (rate control, redirects),       │
│               Album._parse_release() — untouched                 │
└──────────────────────────────────────────────────────────────────┘
```

Division of responsibilities:

| Layer | Generic today? | What is provider-specific |
| :-- | :-- | :-- |
| Identity (`providers.py`) | Yes — final | Nothing; a new provider is one enum member + one root UUID |
| Transport (`api_helpers.py`) | Yes — abstract base `BaseStreamingAPIHelper` | One subclass implementing `search_albums`, `get_release_by_id`, `get_track_by_id`, `get_album_cover_url`; one `_API_HELPER_REGISTRY` entry |
| Loader (`album.py`) | Yes | Nothing; task IDs embed `provider.value` automatically |
| Translation (`deezerjson.py`) | **Deezer-specific** | The JSON→node field mapping and the album/track response callbacks; a new provider adds a sibling module (e.g. `spotifyjson.py`) and rewires the callbacks |
| UI (`albumsearch.py`) | Mostly generic | Search request goes through the helper; today it instantiates `DeezerAPIHelper` directly (see §3) |
| Cover art (`coverart.py`) | Yes — `StreamingCoverArtProvider` reads `{provider}_albumid` and asks the helper for the URL | Nothing beyond a subclass setting `NAME`/`TITLE`/`provider` |
| Options (`options.py`) | Partly | `rate_limit_ms` currently applies to the Deezer domain only (§3) |

## 2. How the pieces connect

1. `get_api_helper_for_provider(provider, webservice)` (`api_helpers.py`) is the single factory: it validates the `Provider` value and instantiates the registered helper class. EAFP style — an unknown provider raises `ValueError`.
2. `load_streaming_album()` (`album.py`) is provider-agnostic: it derives UUIDs via `MetadataProvider`, stamps `album.metastreaming_provider`, and lets the helper issue the release request. `load_deezer_album()` is a thin convenience wrapper over it.
3. The response callback (`recordings_request_finished_proxy`) is where provider JSON becomes provider-neutral: it calls `album_to_mb_release()` and fans out per-track requests. Once a second provider exists, the callback selection should be routed through a registry mirroring `_API_HELPER_REGISTRY` (a `json_translators: dict[Provider, module]` mapping is the natural shape).
4. Per-track assembly (`_track_request_finished`) is already provider-neutral: it only consumes the synthetic node and the track JSON's `track_position` / `disk_number` conventions — a new provider's translation module should normalize to the same conventions rather than change this code.

## 3. Known Deezer-specific leftovers

- `albumsearch.search()` constructs `DeezerAPIHelper(api.web_service)` directly instead of using the factory (works because Deezer is the only provider; fix when adding the second one).
- `ratecontrol.set_minimum_delay_for_url("https://api.deezer.com", …)` is applied in `__init__.py:enable()` and `options.py:save()`; a new provider's domain needs its own call (ideally driven from the helper's `API_URL`).
- The search dialog's Source column and `source = "Deezer"` metadata string are hardcoded; generalize to `provider.value.capitalize()`.
- `enable()` registers `DeezerCoverArtProvider` explicitly; per-provider cover subclasses follow the same pattern.

## 4. Adding a new provider — checklist

Example for a hypothetical `spotify` implementation:

1. **Identity** (`providers.py`)
   - Add `SPOTIFY = "spotify"` to `Provider` (root UUID already exists).
   - Nothing else: entity namespaces and item UUIDs derive automatically. ⚠️ Item IDs must be the provider's *stable native key* as a string (Spotify base-62 IDs are fine); if a provider has mutable IDs, resolve to an immutable one first.
   - **ID-tag naming convention**: provenance tags follow `{provider}_{type}_{id}_id` (e.g. `deezer_album_id`, `deezer_track_id`, `deezer_albumartist_id`); a Spotify implementation would use `spotify_album_id`, `spotify_track_id`, `spotify_albumartist_id` — stamp/processor/cover-art lookups parameterized by `provider.value` already produce these names.
2. **Transport** (`api_helpers.py`)
   - Subclass `BaseStreamingAPIHelper`, set `provider` and `API_URL`, implement the four abstract methods, map any extra endpoints (`_get_by_id` pattern).
   - Register in `_API_HELPER_REGISTRY`.
   - Respect auth needs via the underlying `APIHelper` (`mblogin=False` for anonymous APIs).
3. **Translation** (new module, sibling of `deezerjson.py`)
   - Implement `album_to_mb_release(node, provider)`, `_mb_track_from_track(...)`-equivalent, and the two response callbacks (`*_request_finished_proxy`, `*_track_request_finished`), reusing `MetadataProvider`, `_node_skip_empty_iter` and the synthetic-node contract from [architecture.md](architecture.md) §3 (including the `recording.relations = []` sentinel).
   - Normalize durations to ms, positions to 1-based ints, artist credits to the `artist-credit` shape.
   - Wire the callbacks into `load_streaming_album()`'s request factory (parameterize by provider, as `deezerjson` is passed by name today).
4. **Cover art** (`coverart.py`)
   - Subclass `StreamingCoverArtProvider` with `provider = Provider.SPOTIFY` — the base class already keys off `{provider}_albumid` metadata and `get_album_cover_url()`.
   - Note the enablement caveat in [limitations.md](limitations.md); Stage 6's URL-relation piggyback supersedes this mechanism entirely.
5. **Options / rate limit**
   - Either a per-provider delay option or one delay applied to each provider's `API_URL` in `enable()` / `save()`.
6. **UI polish**
   - Replace the direct `DeezerAPIHelper` construction in `albumsearch.py` with `get_api_helper_for_provider`, generalize the Source column, and add the provider to the search dialog's source metadata.
7. **Docs**
   - Add the provider to [configuration.md](configuration.md) if it gains options, to [reference/deezer-api.md](reference/deezer-api.md)'s sibling endpoint list, and record the addition in [roadmap.md](roadmap.md).

## 5. Design invariants to preserve

- **One loader, many providers**: `load_streaming_album()` must stay provider-agnostic; all provider knowledge lives below the loader or in the translation module.
- **Node contract first**: a provider is "supported" when its synthetic node survives `Album._parse_release()` — verified the way Stage 5 did it (consumer tracing against `mbjson`), not merely when the request succeeds.
- **Deterministic IDs only**: never introduce per-run state (counters, timestamps, random) into UUID derivation.
- **No core coupling**: keep relying only on the public plugin API (`picard.plugin3.api`) and stable core entry points (`Album._parse_release`, webservice, ratecontrol); no monkey-patching (it was deliberately removed in Stages 2–3).