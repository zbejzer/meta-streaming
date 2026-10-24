# Module Map — Plugin Package Reference

> File-by-file reference of `picard/plugins/meta-streaming/`. Behavioral detail lives in [../dataflow.md](../dataflow.md) and [../architecture.md](../architecture.md); this page is the "what lives where" index.

## Package layout

```text
meta-streaming/
├── MANIFEST.toml          Plugin v3 manifest (uuid, name, api 3.0, categories)
├── LICENSE                GPL-3.0-or-later
├── __init__.py            Lifecycle + registrations
├── album.py               Provider-agnostic album loader
├── albumsearch.py         Search dialog UI
├── api_helpers.py         Transport abstraction + Deezer implementation
├── coverart.py            Streaming cover-art providers
├── deezerjson.py          Deezer JSON → synthetic MB node translation
├── options.py             Options page
├── providers.py           Synthetic UUID engine
├── locale/en.toml         Plugin translation strings (action title, manifest name/description)
├── docs/                  This documentation
└── examples/              Ground-truth API artifacts (deezer/, MusicBrainz/)
```

## `__init__.py` — lifecycle

| Symbol | Role |
| :-- | :-- |
| `GetMetaStreaming(BaseAction)` | Cluster action "Get metadata from streamings"; opens `StreamingAlbumSearchDialog` seeded from the cluster (`show_similar_albums`). Logs a debug line when the selection is not a cluster. |
| `enable(api)` | Registers: options `rate_limit_ms` / `cover_size` / `tag_explicit` (all `in_profile=True`), the Deezer rate-limit floor via `ratecontrol.set_minimum_delay_for_url`, dialog-header persistence (`plugin_persist`), the cluster action, the track metadata processor (`track_metadata_processor` from `deezerjson.py`), `DeezerCoverArtProvider`, and `StreamingOptionsPage`. Unregistration on disable is handled by the plugin API. |

## `providers.py` — identity engine

| Symbol | Role |
| :-- | :-- |
| `Provider(StrEnum)` | `DEEZER`, `SPOTIFY`, `TIDAL`, `QOBUZ`, `APPLE_MUSIC` (only Deezer implemented). |
| `EntityType(StrEnum)` | `RELEASE`, `RELEASE_GROUP`, `ARTIST`, `TRACK` — minimized set (label/recording removed by the Stage 5 audit). |
| `PROVIDER_ROOT_UUIDS` | One frozen root UUID per provider; tier 0 of the namespace scheme. |
| `MetadataProvider` | Two-tier `uuid5` derivation; `get_entity_namespace`, `generate_uuid`, and the four `generate_*_UUID` convenience methods. `Names = Provider` backward-compat alias. Raises `ValueError` for unknown providers (EAFP over `try/except (ValueError, KeyError)`). |

Full scheme: [../uuid-scheme.md](../uuid-scheme.md).

## `api_helpers.py` — transport

| Symbol | Role |
| :-- | :-- |
| `escape_deezer_query` / `build_deezer_query` | Deezer query-string syntax helpers (`field:"value"` joining; quotes stripped from values). |
| `BaseStreamingAPIHelper(APIHelper, ABC)` | Abstract transport: `search_albums`, `get_release_by_id`, `get_track_by_id`, `get_album_cover_url`. |
| `DeezerAPIHelper` | Deezer implementation over `https://api.deezer.com`: `/search/album` (with `q`/`index`/`limit`, `priority=True, important=True, mblogin=False`), `/album/{id}`, `/track/{id}`, `/album/{id}/tracks` (defined, currently unused), `/album/{id}/image?size=`. `find` alias kept for compatibility. |
| `_API_HELPER_REGISTRY` / `get_api_helper_for_provider` | Provider → helper-class registry and the single instantiation factory (raises `ValueError` for unregistered providers). |

## `album.py` — loader

| Symbol | Role |
| :-- | :-- |
| `load_streaming_album(api, provider_name, album_id, cluster, priority, refresh)` | The generic loader: UUID derivation, release-group registration, album creation + `album_added`, `metastreaming_provider` stamp, critical-task guard, full state reset, `add_album_task` with a request factory, cluster file placement. Returns the `Album`. |
| `load_deezer_album(api, deezer_album_id, …)` | Convenience wrapper binding `Provider.DEEZER`. |

## `deezerjson.py` — translation & fan-out

| Symbol | Role |
| :-- | :-- |
| `_TRACK_TO_MB_TRACK` / `_ALBUM_TO_MB_RELEASE` / `_ALBUMSEARCH_TO_METADATA` | Field maps: track node (incl. `bpm`), album node (genres emitted with `count: 100` — see [design/track-response-analysis.md](design/track-response-analysis.md) §4), search-result metadata. |
| `_artist_credit_from_contributors(node, provider)` | Builds `artist-credit` from `contributors` (or `artist`): joinphrases `", "` / `" & "`, synthetic artist UUIDs (name fallback when no `id`). |
| `_mb_track_from_track(node, provider, api)` | Track + recording node builder: synthetic track UUID, ms duration, position/number, artist-credit, `recording.isrcs`, `recording.relations = []` sentinel, optional `explicit` flag. |
| `album_to_mb_release(node, provider)` | Release node builder: synthetic id, `status: "Official"`, mapped fields, label-info (name only), genres, `release-group` subnode, empty `media`. |
| `recordings_request_finished_proxy(api, album, task_id, document, http, error)` | Album-response callback: builds the node, parks it as `metastreaming_mb_node`, dispatches parallel `_request_track` per track (or finishes immediately when no tracks). |
| `_request_track` / `_track_request_finished` | Per-track album task + response callback: builds the track node, slots it into `media[disk][pos]`, grows mediums, finalizes when no critical tasks remain; cancels remaining tasks on error or missing node. |
| `_finish_deezer_release(album, mb_document, http, error)` | Single finalizer: `Album._parse_release` hand-off, `deezer_album_id` stamp, metadata processors, error capture, transient-attribute cleanup, `_finalize_loading`. |
| `track_metadata_processor(api, track, metadata, track_node, release_node=None)` | Track metadata processor (Stages 8–9): promotes `deezer_track_id` (always), `bpm` (standard tag, when Deezer reports `> 0`, integral values normalized), and `explicit = "1"` (gated on `tag_explicit` at parse time) from the synthetic node into final track metadata; no-op for genuine MusicBrainz nodes. Covered by `test/meta_streaming/test_explicit_tag.py`. |
| `_clean_attributes(album)` | Removes transient `metastreaming_provider` / `metastreaming_mb_node`. |
| `albumsearch_to_metadata(node, metadata)` | Search-result → `Metadata` mapping (`album`, `tracks`, `deezer_album_id`, `deezer_albumartist_id`, `albumartist`, `source = "Deezer"`). |

## `albumsearch.py` — search UI

| Symbol | Role |
| :-- | :-- |
| `StreamingAlbumSearchDialog(SearchDialog)` | Columns Name/Artist/Tracks/Source/ID/Cover; class-level `_cover_cache` (QPixmap per Deezer id); pagination state (`current_index`, `results_limit = 25`, `total_results`); `Load More` button with `count/total` label. |
| `search` / `load_more_results` / `show_similar_albums` | Query flow: free text (advanced syntax honored via `use_advanced_search`) or cluster-derived `artist`+`album` query; pagination re-issues with `index += limit`. |
| `handle_reply` | Result parsing, `Load More` state updates. |
| `fetch_coverarts` / `fetch_coverart` / `_cover_downloaded` / `fetch_cleanup` | Lazy visible-cell thumbnail fetch (`size=medium`), cache hits, abort on close/re-search, error cells. |
| `restore_table_header_state` / `save_table_header_state` | Dialog header persistence via `api.plugin_persist` (key `streamingalbumsearchdialog_header_state`). |
| `accept_event` / `load_selection` | "Load into Picard" → `load_deezer_album(api, id, cluster=self.cluster)`. |

## `coverart.py` — cover-art providers

| Symbol | Role |
| :-- | :-- |
| `StreamingCoverArtProvider(CoverArtProvider)` | Generic streaming provider: reads `{provider.value}_albumid` from album metadata, builds the URL via the provider helper honoring `cover_size`, queues `CoverArtImage(url, types=["front"])`. |
| `DeezerCoverArtProvider` | Deezer subclass (`NAME = "Deezer Cover Art"`). |

Enablement caveat (registered disabled at position 666) and the Stage 6 replacement plan: [../limitations.md](../limitations.md), [design/cover-art-piggyback-mechanism.md](design/cover-art-piggyback-mechanism.md).

## `options.py` — settings UI

| Symbol | Role |
| :-- | :-- |
| `StreamingOptionsPage(OptionsPage)` | Page `meta_streaming` under `plugins`; widgets bound via `OPTIONS: PageOptionConfigs` (`rate_limit_spinbox`, `cover_size_combo`, `explicit_checkbox`); `save()` re-applies the Deezer rate limit. Details: [../configuration.md](../configuration.md). |

## Supporting artifacts

- `examples/deezer/album_dzr.json`, `examples/deezer/album_tracks_dzr.json`, `examples/deezer/track_dzr.json`, `examples/MusicBrainz/album_mb.json` — ground-truth API artifacts used by the Stage 5 audit ([design/musicbrainz-deezer-mapping.md](design/musicbrainz-deezer-mapping.md), [reference/deezer-api.md](deezer-api.md)) and the track-response analysis ([design/track-response-analysis.md](design/track-response-analysis.md)).
- `locale/en.toml` — plugin translation keys (`action.get_meta_streaming`, `manifest.name`, `manifest.description`).
- `MANIFEST.toml` — plugin identity; `api = ['3.0']`, categories `metadata` + `coverart`.