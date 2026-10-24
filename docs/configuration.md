# Configuration Reference

> User-facing options and persistence of the Streaming Metadata plugin. Settings UI: `options.py` (`StreamingOptionsPage`), registered under **Options → Plugins → Streaming Metadata** (`NAME = "meta_streaming"`, `PARENT = "plugins"`).

## 1. Plugin options (`api.plugin_config`)

All three options are registered in `enable()` with `in_profile=True`, so they participate in Picard's shareable profiles.

| Option | Type / Default | Bounds | Widget | Effect |
| :-- | :-- | :-- | :-- | :-- |
| `rate_limit_ms` | int, `100` | 50–2000 (spinbox step 25) | `rate_limit_spinbox` | Minimum delay between requests to `https://api.deezer.com`. Applied via `ratecontrol.set_minimum_delay_for_url()` on plugin enable and re-applied on options save. Protects against Deezer throttling while the parallel track fan-out runs. |
| `cover_size` | str, `"xl"` | one of `xl`, `big`, `medium`, `small` | `cover_size_combo` (XL 1000×1000, Large 500×500, Medium 250×250, Small 56×56) | Preferred full-resolution artwork size, consumed by the cover-art provider when constructing the cover URL (`get_album_cover_url(album_id, size=…)`). Does **not** affect search-dialog thumbnails, which always use `medium` for responsiveness. After Stage 6 it will feed the injected `cover art link` URL instead (see [design/cover-art-piggyback-mechanism.md](design/cover-art-piggyback-mechanism.md)). |
| `tag_explicit` | bool, `True` | — | `explicit_checkbox` | When enabled, explicit tracks (Deezer `explicit_lyrics`) get the user-visible `explicit` tag (`"1"`) via the track metadata processor — editable in the metadata box, scriptable as `%explicit%`, and written through Picard's native freeform path (`TXXX:explicit` on MP3, `----:com.apple.iTunes:explicit` on MP4, `EXPLICIT` on Vorbis, freeform on APEv2/WAV; not on WMA). The same processor also preserves `deezer_track_id` per track. Evaluated at parse time — untick and reload to keep files free of the tag. Decision record: [design/explicit-tag-analysis.md](design/explicit-tag-analysis.md). |

`rate_limit_ms` is the only option with runtime side effects beyond tagging: it shapes Picard's global per-host rate control. Lower values speed up parallel track loading; the default `100` ms balances speed against Deezer's tolerance. Bounds in the option registration and the spinbox range must stay in sync.

## 2. Persistence (`api.plugin_persist`)

| Key | Type | Content |
| :-- | :-- | :-- |
| `streamingalbumsearchdialog_header_state` | `QtCore.QByteArray` | Column layout (widths, order) of the `StreamingAlbumSearchDialog` table. Saved on dialog close, restored on next open via the `@restore_method`-decorated `restore_table_header_state()`. |

Persistence state is namespaced by the plugin's MANIFEST uuid, so it survives plugin updates and does not clash with other plugins.

## 3. What is *not* configurable (yet)

- **Synthetic-MBID stripping before save** — planned as a `save_synthetic_mbids` boolean option in [roadmap](roadmap.md) Stage 7 (default off, with a pre-save processor that strips only generated UUIDs and preserves pre-existing MBID tags).
- **Per-provider settings** — options are global to the plugin; per-provider rate limits/sizes are a natural extension once a second provider lands (see [providers.md](providers.md) §4).
- **Search page size** — fixed at 25 results per page in `albumsearch.py`.

## 4. How option binding works

`StreamingOptionsPage` declares the `OPTIONS: PageOptionConfigs` mapping (`option name → widget attribute`), which lets Picard's options framework handle profile overrides; `load()` / `save()` read and write `self.api.plugin_config[...]` and, for `rate_limit_ms`, additionally push the value into `ratecontrol` because that setting has an immediate runtime effect rather than being read per-request.