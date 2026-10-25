# Deezer API Endpoints Used

> The HTTP surface the plugin exercises, and the example artifacts that document the response shapes. Behavior context: [../dataflow.md](../dataflow.md). A sibling document per future provider should follow this pattern (see [../providers.md](../providers.md) §4).

Official documentation fragments (converted to Markdown) live in [deezer/](deezer/): [deezer/global-parameters.md](deezer/global-parameters.md) (pagination, access token, request methods), [deezer/album.md](deezer/album.md) (album object fields, actions, connections), [deezer/track.md](deezer/track.md) (track object), [deezer/genre.md](deezer/genre.md) (genre/editorial object) and [deezer/search.md](deezer/search.md) (search endpoints, optional parameters, advanced search).

All requests go through Picard's webservice via `DeezerAPIHelper` (`api_helpers.py`), so redirects and per-host rate control are handled by core. The plugin sets a minimum request delay for `https://api.deezer.com` from the `rate_limit_ms` option; on redirect, the delay is transferred to the CDN host natively (`ratecontrol.copy_minimal_delay`).

## Endpoints

| Endpoint | Used by | Purpose | Notes |
| :-- | :-- | :-- | :-- |
| `GET /search/album?q=&index=&limit=` | `DeezerAPIHelper.search_albums()` | Album search for the dialog | `index` is the pagination offset (page size 25), `limit` the page size; response `{data: [...], total, next?}`. Requests are `priority=True, important=True, mblogin=False`. |
| `GET /album/{id}` | `DeezerAPIHelper.get_release_by_id()` | Full album object | The response embeds `tracks.data` (id/title/duration per track — *without* `isrc`/`disk_number`/`track_position`) which lists the tracks for the parallel per-track fan-out; also carries `contributors`, `genres.data`, `label`, `upc`, `release_date`, `record_type`, cover URLs. |
| `GET /track/{id}` | `DeezerAPIHelper.get_track_by_id()` | Per-track detail | The **only** response shape with `contributors` (accurate artist-credit incl. featuring artists); also supplies `track_position`, `disk_number`, `duration` (seconds), `isrc`, `explicit_lyrics`, plus `bpm`/`gain`/track `release_date`. Dispatched as one album task per track, in parallel. |
| `GET /album/{id}/tracks` | `DeezerAPIHelper.get_tracklist_by_id()` | Tracklist resource | Documented response with example artifact; adds `isrc`/`disk_number`/`track_position` over the album-embedded list but **lacks `contributors`** — not used by the loader; a potential fan-out replacement analyzed in [../design/track-response-analysis.md](../design/track-response-analysis.md). |
| `GET /album/{id}/image?size={small\|medium\|big\|xl}` | `get_album_cover_url()` + dialog thumbnails | Cover artwork bytes | `size=medium` (250×250) for dialog thumbnails; the `cover_size` option (default `xl` = 1000×1000) for full artwork. Redirects to the CDN (`cdn-images.dzcdn.net`), where the rate-control delay is copied to the new host. |

No authentication is required for these public endpoints; `mblogin=False` keeps Picard from attaching MusicBrainz credentials.

## Request semantics worth knowing

- **Search vs. cluster queries**: free-text queries honor Picard's "Use advanced search syntax" option; otherwise quotes are stripped (`escape_deezer_query`). Cluster queries are built as `artist:"…" album:"…"`.
- **Throttling**: Deezer enforces request-rate limits; the plugin's `rate_limit_ms` floor (default 100 ms, bounds 50–2000) applies to every call in the table above.
- **Empty-value skipping**: responses with empty/missing optional fields rely on `mbjson._node_skip_empty_iter()` in the translation layer, mirroring how Picard treats genuine MB responses.

## Example artifacts (same album, both APIs)

| File | Content |
| :-- | :-- |
| `examples/deezer/album_dzr.json` | Deezer album `12400342` — "Hello, I Must Be Going (2016 Remaster)" (Phil Collins, Rhino, 2013): full album object incl. `contributors` (role `Main`), `genres.data`, `tracks.data` (album-embedded track list, *without* `isrc`/`disk_number`/`track_position`), cover URL family (`cover`…`cover_xl`), `upc`, `release_date`, `record_type`, `explicit_lyrics`. |
| `examples/deezer/album_tracks_dzr.json` | Response of `GET /album/12400342/tracks` for the same album: the tracklist shape — per-track `isrc`, `disk_number`, `track_position` present, but no `contributors` and no `role` on the artist objects. |
| `examples/deezer/track_dzr.json` | Full `GET /track/{id}` response for track `3135553` ("One More Time", Daft Punk): the only shape with `contributors` (here role `Main` on the artist itself), plus `bpm`, `gain`, track-level `release_date`, `available_countries`, `track_token`. |
| `examples/MusicBrainz/album_mb.json` | MusicBrainz release response for the same album — the shape the synthetic node must satisfy: `artist-credit` (with sort-names, disambiguation, tags), `label-info`, `media[].tracks` (ms lengths, `recording` nodes with ISRCs and relations), `release-group` (`primary-type`), `status`, `country`, `cover-art-archive`. |

These artifacts are the ground truth used by the Stage 5 audit (`album_mb.json` vs. `album_dzr.json`) and by the track-response analysis ([../design/track-response-analysis.md](../design/track-response-analysis.md)): every synthetic-node key was verified against what `picard/mbjson.py` actually consumes from a genuine response like `album_mb.json`, and the three Deezer track-data shapes are compared for field availability. The full field-level classification lives in [../design/musicbrainz-deezer-mapping.md](../design/musicbrainz-deezer-mapping.md); the saved web references for the MB release schema and Picard's tag mapping table are in this directory ([MusicBrainz API - MusicBrainz.html](MusicBrainz%20API%20-%20MusicBrainz.html), [MusicBrainz Picard Tag Mapping.html](MusicBrainz%20Picard%20Tag%20Mapping.html)).