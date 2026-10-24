# Deezer API — Track Object

> Fragment of the official Deezer API documentation ([developers.deezer.com/api](https://developers.deezer.com/api)), converted from HTML for offline reference. Companion fragments: [album.md](album.md), [genre.md](genre.md), [global-parameters.md](global-parameters.md). How this plugin consumes these fields: [../deezer-api.md](../deezer-api.md) and the field-level audit in [../../design/musicbrainz-deezer-mapping.md](../../design/musicbrainz-deezer-mapping.md).

A track object.

Live example: <https://api.deezer.com/track/3135556> ([API explorer](https://developers.deezer.com/api/explorer?url=track/313556)). A captured response for a track of this plugin's ground-truth album: `examples/deezer/track_dzr.json`.

## Fields

| Name | Type | Description |
| :-- | :-- | :-- |
| `id` | int | The track's Deezer id |
| `readable` | boolean | `true` if the track is readable in the player for the current user |
| `title` | string | The track's fulltitle |
| `title_short` | string | The track's short title |
| `title_version` | string | The track version |
| `unseen` | boolean | The track unseen status |
| `isrc` | string | The track isrc |
| `link` | url | The url of the track on Deezer |
| `share` | url | The share link of the track on Deezer |
| `duration` | int | The track's duration in seconds |
| `track_position` | int | The position of the track in its album |
| `disk_number` | int | The track's album's disk number |
| `rank` | int | The track's Deezer rank |
| `release_date` | date | The track's release date |
| `explicit_lyrics` | boolean | Whether the track contains explicit lyrics |
| `explicit_content_lyrics` | int | The explicit content lyrics values (0: Not Explicit; 1: Explicit; 2: Unknown; 3: Edited; 6: No Advice Available) |
| `explicit_content_cover` | int | The explicit cover value (0: Not Explicit; 1: Explicit; 2: Unknown; 3: Edited; 6: No Advice Available) |
| `preview` | url | The url of the track's preview file. This file contains the first 30 seconds of the track |
| `bpm` | float | Beats per minute |
| `gain` | float | Signal strength |
| `available_countries` | list | List of countries where the track is available |
| `alternative` | track | Return an alternative readable track if the current track is not readable |
| `contributors` | list | Return a list of contributors on the track |
| `md5_image` | string | *(no description in the original documentation)* |
| `track_token` | string | The track token for media service |
| `artist` | object | [artist](https://developers.deezer.com/api/artist) object containing: `id`, `name`, `link`, `share`, `picture`, `picture_small`, `picture_medium`, `picture_big`, `picture_xl`, `nb_album`, `nb_fan`, `radio`, `tracklist`, `role` |
| `album` | object | [album](https://developers.deezer.com/api/album) object containing: `id`, `title`, `link`, `cover`, `cover_small`, `cover_medium`, `cover_big`, `cover_xl`, `release_date` |

Note that the track-level `explicit_content_*` scale is narrower than the album-level one documented in [album.md](album.md): the track documentation lists only values 0, 1, 2, 3 and 6 — the "Partially" states (4, 5, 7) are album-scoped.

## Actions

These actions are available by passing a GET parameter named `request_method` to the request (see [global-parameters.md](global-parameters.md)):

| `request_method` | Needed permissions | Description |
| :-- | :-- | :-- |
| POST | `manage_library` | Update a personal track |
| DELETE | `delete_library` | Delete a personal track |

## Related actions

Actions related to `track` through other resources:

- [playlist / tracks](https://developers.deezer.com/api/playlist/tracks): POST `manage_library` — add a track to the playlist (`songs`: comma-separated track ids) or order tracks in the playlist (`order`: comma-separated track ids); DELETE `manage_library`, `delete_library` — remove tracks from the playlist.
- [user / tracks](https://developers.deezer.com/api/user/tracks): POST `manage_library` — add track(s) to the user's favorites; DELETE `manage_library`, `delete_library` — remove a track from the user's favorites (`track_id`: int).

## Usage in this plugin

- The plugin fetches this object per track (`GET /track/{id}`, parallel album tasks) because it is the **only** response shape carrying all of: `track_position`, `disk_number`, `isrc`, and `contributors` (accurate artist-credit including featuring artists). See the three-shape availability matrix in [../../design/track-response-analysis.md](../../design/track-response-analysis.md).
- Consumed fields: `id` (synthetic track UUID + `deezer_track_id` provenance), `title`, `duration` (→ `length`), `track_position` (→ `tracknumber`), `disk_number` (→ `discnumber`), `isrc` (→ `isrc`), `explicit_lyrics` (→ `explicit` via the Stage 8 processor), `contributors`/`artist` (→ `artist-credit`).
- Not consumed: `bpm`, `gain`, track-level `release_date`, `available_countries`, `track_token`, `alternative`, `unseen`, `preview`, `rank`, `readable`, `title_short`, `title_version`, `link`, `share` — the assessment (including the `bpm` preservation candidate) is in [../../design/track-response-analysis.md](../../design/track-response-analysis.md).