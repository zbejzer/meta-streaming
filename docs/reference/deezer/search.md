# Deezer API — Search

> Fragment of the official Deezer API documentation ([developers.deezer.com/api](https://developers.deezer.com/api)), converted from HTML for offline reference. Companion fragments: [album.md](album.md), [track.md](track.md), [genre.md](genre.md), [global-parameters.md](global-parameters.md). How this plugin searches: [../deezer-api.md](../deezer-api.md) and [../../dataflow.md](../../dataflow.md) §2.

Search tracks. Live example: <https://api.deezer.com/search?q=eminem> ([API explorer](https://developers.deezer.com/api/explorer?url=search%3Fq%3Deminem)).

## Optional parameters (for all search methods)

| Name | Description |
| :-- | :-- |
| `strict` | Disable the fuzzy mode (`?strict=on`) |
| `order` | Possible values: `RANKING`, `TRACK_ASC`, `TRACK_DESC`, `ARTIST_ASC`, `ARTIST_DESC`, `ALBUM_ASC`, `ALBUM_DESC`, `RATING_ASC`, `RATING_DESC`, `DURATION_ASC`, `DURATION_DESC` |

## Result fields

The base `/search` endpoint returns **track** objects:

| Name | Description | Type |
| :-- | :-- | :-- |
| `id` | The track's Deezer id | int |
| `readable` | `true` if the track is readable in the player for the current user | boolean |
| `title` | The track's fulltitle | string |
| `title_short` | The track's short title | string |
| `title_version` | The track version | string |
| `isrc` | The track isrc | string |
| `link` | The url of the track on Deezer | url |
| `duration` | The track's duration in seconds | int |
| `rank` | The track's Deezer rank | int |
| `explicit_lyrics` | Whether the track contains explicit lyrics | boolean |
| `preview` | The url of the track's preview file. This file contains the first 30 seconds of the track | url |
| `artist` | [artist](https://developers.deezer.com/api/artist) object containing: `id`, `name`, `link`, `picture`, `picture_small`, `picture_medium`, `picture_big`, `picture_xl` | object |
| `album` | [album](https://developers.deezer.com/api/album) object containing: `id`, `title`, `cover`, `cover_small`, `cover_medium`, `cover_big`, `cover_xl` | object |

## Advanced search

Deezer provides a hidden feature that could help you to find artists, albums or tracks. This feature is called Advanced Search. The only thing you have to do is to specify the need that you expect:

| Name | Description | Type | Example |
| :-- | :-- | :-- | :-- |
| `artist` | The artist name | string | [`https://api.deezer.com/search?q=artist:"aloe blacc"`](https://developers.deezer.com/api/explorer?url=search%3Fq=artist%3A%22aloe%20blacc%22) |
| `album` | The album's title | string | [`https://api.deezer.com/search?q=album:"good things"`](https://developers.deezer.com/api/explorer?url=search%3Fq=album%3A%22good%20things%22) |
| `track` | The track's title | string | [`https://api.deezer.com/search?q=track:"i need a dollar"`](https://developers.deezer.com/api/explorer?url=search%3Fq=track%3A%22i%20need%20a%20dollar%22) |
| `label` | The label name | string | [`https://api.deezer.com/search?q=label:"because music"`](https://developers.deezer.com/api/explorer?url=search%3Fq=label%3A%22because%20music%22) |
| `dur_min` | The track's minimum duration in seconds | int | [`https://api.deezer.com/search?q=dur_min:300`](https://developers.deezer.com/api/explorer?url=search%3Fq=dur_min%3A300) |
| `dur_max` | The track's maximum duration in seconds | int | [`https://api.deezer.com/search?q=dur_max:500`](https://developers.deezer.com/api/explorer?url=search%3Fq=dur_max%3A500) |
| `bpm_min` | The track's minimum bpm | int | [`https://api.deezer.com/search?q=bpm_min:120`](https://developers.deezer.com/api/explorer?url=search%3Fq=bpm_min%3A120) |
| `bpm_max` | The track's maximum bpm | int | [`https://api.deezer.com/search?q=bpm_max:200`](https://developers.deezer.com/api/explorer?url=search%3Fq=bpm_max%3A200) |

You can also mix your search, by adding a space between each field, to be more specific:

- [`https://api.deezer.com/search?q=artist:"aloe blacc" track:"i need a dollar"`](https://developers.deezer.com/api/explorer?url=search%3Fq=artist%3A%22aloe%20blacc%22%20track%3A%22i%20need%20a%20dollar%22)
- [`https://api.deezer.com/search?q=bpm_min:120 dur_min:300`](https://developers.deezer.com/api/explorer?url=search%3Fq=bpm_min%3A120%20dur_min%3A300)

## Connections

| Name | Description | Returns |
| :-- | :-- | :-- |
| [search / album](https://developers.deezer.com/api/search/album) | Search albums | A list of objects of type [album](https://developers.deezer.com/api/album) |
| [search / artist](https://developers.deezer.com/api/search/artist) | Search artists | A list of objects of type [artist](https://developers.deezer.com/api/artist) |
| [search / history](https://developers.deezer.com/api/search/history) | Get user search history | Lists of objects of type [track](https://developers.deezer.com/api/track), [album](https://developers.deezer.com/api/album), [artist](https://developers.deezer.com/api/artist), [playlist](https://developers.deezer.com/api/playlist), [podcast](https://developers.deezer.com/api/podcast), [radio](https://developers.deezer.com/api/radio) |
| [search / playlist](https://developers.deezer.com/api/search/playlist) | Search playlists | A list of objects of type [playlist](https://developers.deezer.com/api/playlist) |
| [search / radio](https://developers.deezer.com/api/search/radio) | Search radio | A list of objects of type [radio](https://developers.deezer.com/api/radio) |
| [search / track](https://developers.deezer.com/api/search/track) | Search tracks | A list of objects of type [track](https://developers.deezer.com/api/track) |
| [search / user](https://developers.deezer.com/api/search/user) | Search users | A list of objects of type [user](https://developers.deezer.com/api/user) |

## Usage in this plugin

- The plugin uses the **`search / album`** connection (`GET /search/album` with `q`/`index`/`limit` — pagination via [global-parameters.md](global-parameters.md)); its results are **album** objects (fields documented in [album.md](album.md)), converted to dialog rows by `albumsearch_to_metadata()`.
- The Advanced Search fields are what the cluster query builder (`build_deezer_query()`) emits — `artist:"…" album:"…"` — and what the dialog's free-text box passes through when Picard's "Use advanced search syntax" option is enabled; otherwise raw query text (quotes stripped) is sent and results are broader.
- Not exercised: the `strict` and `order` parameters (a candidate enhancement, e.g. `order=RANKING`), and the base `/search` (track) endpoint and other connections — the plugin searches albums only.