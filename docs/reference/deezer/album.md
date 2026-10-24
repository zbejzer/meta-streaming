# Deezer API — Album Object

> Fragment of the official Deezer API documentation ([developers.deezer.com/api](https://developers.deezer.com/api)), converted from HTML for offline reference. Companion fragment: [global-parameters.md](global-parameters.md). How this plugin consumes these fields: [../deezer-api.md](../deezer-api.md) and the field-level audit in [../../design/musicbrainz-deezer-mapping.md](../../design/musicbrainz-deezer-mapping.md).

An album object.

Live example: <https://api.deezer.com/album/302127> ([API explorer](https://developers.deezer.com/api/explorer?url=album/302127)). A captured response for the same album used as this plugin's ground truth: `examples/deezer/album_dzr.json`.

## Fields

| Name | Type | Description |
| :-- | :-- | :-- |
| `id` | int | The Deezer album id |
| `title` | string | The album title |
| `upc` | string | The album UPC |
| `link` | url | The url of the album on Deezer |
| `share` | url | The share link of the album on Deezer |
| `cover` | url | The url of the album's cover. Add a `size` parameter to the url to change size: `small`, `medium`, `big`, `xl` |
| `cover_small` | url | The url of the album's cover in size small |
| `cover_medium` | url | The url of the album's cover in size medium |
| `cover_big` | url | The url of the album's cover in size big |
| `cover_xl` | url | The url of the album's cover in size xl |
| `md5_image` | string | *(no description in the original documentation)* |
| `genre_id` | int | The album's first genre id (you should use the genre list instead); `-1` for not found |
| `genres` | list | List of genre objects |
| `label` | string | The album's label name |
| `provider` | string | The album's provider name |
| `nb_tracks` | int | *(no description in the original documentation)* |
| `duration` | int | The album's duration (seconds) |
| `fans` | int | The number of album's fans |
| `release_date` | date | The album's release date |
| `record_type` | string | The record type of the album (EP / ALBUM / etc.) |
| `available` | boolean | *(no description in the original documentation)* |
| `alternative` | object | Returns an alternative album object if the current album is not available |
| `tracklist` | url | API link to the tracklist of this album |
| `explicit_lyrics` | boolean | Whether the album contains explicit lyrics |
| `explicit_content_lyrics` | int | Explicit content lyrics value (see value scale below) |
| `explicit_content_cover` | int | Explicit cover value (same value scale) |
| `contributors` | list | List of contributors on the album |
| `fallback` | object | Returns fallback album with id and status |
| `artist` | object | [artist](https://developers.deezer.com/api/artist) object containing: `id`, `name`, `picture`, `picture_small`, `picture_medium`, `picture_big`, `picture_xl` |
| `tracks` | list | List of [track](https://developers.deezer.com/api/track) objects (see track fields below) |

### Explicit content value scale

Both `explicit_content_lyrics` and `explicit_content_cover` use the same scale:

| Value | Meaning |
| :-- | :-- |
| `0` | Not Explicit |
| `1` | Explicit |
| `2` | Unknown |
| `3` | Edited |
| `4` | Partially Explicit (Album "lyrics" only) |
| `5` | Partially Unknown (Album "lyrics" only) |
| `6` | No Advice Available |
| `7` | Partially No Advice Available (Album "lyrics" only) |

### Track fields (objects in `tracks`)

| Name | Type | Description |
| :-- | :-- | :-- |
| `id` | int | The track's Deezer id |
| `readable` | boolean | `true` if the track is readable in the player for the current user |
| `title` | string | The track's fulltitle |
| `title_short` | string | The track's short title |
| `title_version` | string | The track version |
| `link` | url | The url of the track on Deezer |
| `duration` | int | The track's duration in seconds |
| `rank` | int | The track's Deezer rank |
| `explicit_lyrics` | boolean | Whether the track contains explicit lyrics |
| `preview` | url | The url of the track's preview file. This file contains the first 30 seconds of the track |
| `artist` | object | [artist](https://developers.deezer.com/api/artist) object containing: `id`, `name` |
| `album` | object | [album](https://developers.deezer.com/api/album) object containing: `id`, `title`, `cover`, `cover_small`, `cover_medium`, `cover_big`, `cover_xl` |

## Related actions

Actions related to `album` through user library methods ([user / albums](https://developers.deezer.com/api/user/albums)):

| `request_method` | Needed permissions | Description | Required params |
| :-- | :-- | :-- | :-- |
| POST | `manage_library` | Add album(s) to the user's library | — |
| DELETE | `manage_library`, `delete_library` | Remove an album from the user's library | `album_id` (int) — the id of the album |

## Connections

| Name | Description | Returns |
| :-- | :-- | :-- |
| [album / fans](https://developers.deezer.com/api/album/fans) | Returns a list of album's fans, represented by an array of User objects | A list of objects of type [user](https://developers.deezer.com/api/user) |
| [album / tracks](https://developers.deezer.com/api/album/tracks) | Returns a list of album's tracks, represented by an array of Track objects | A list of objects of type [track](https://developers.deezer.com/api/track) |

## Usage in this plugin

- The plugin reads the album object via `GET /album/{id}` and maps only the fields with consumers in Picard core: `id`, `title`, `upc`, `release_date`, `label`, `genres.data[].name`, `record_type`, and `contributors`/`artist`. Everything else is dropped — the full classification is in the [mapping audit](../../design/musicbrainz-deezer-mapping.md).
- The embedded `tracks` list **lacks** `disk_number`, `track_position` and `isrc`. Those fields are available on both `GET /album/{id}/tracks` (see `examples/deezer/album_tracks_dzr.json`) and the full `GET /track/{id}` object, but only the latter carries `contributors` — the accurate artist-credit source for featuring tracks — which is why the plugin fetches every track individually. The three-shape comparison and optimization analysis: [../../design/track-response-analysis.md](../../design/track-response-analysis.md).
- Cover artwork is fetched from the `cover` URL with the `size` parameter (`medium` for search thumbnails, the `cover_size` option — default `xl` — for full artwork).