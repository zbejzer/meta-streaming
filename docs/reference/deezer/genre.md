# Deezer API — Genre Object

> Fragment of the official Deezer API documentation ([developers.deezer.com/api](https://developers.deezer.com/api)), converted from HTML for offline reference. Companion fragments: [album.md](album.md), [track.md](track.md), [global-parameters.md](global-parameters.md). How this plugin consumes genres: [../deezer-api.md](../deezer-api.md) and [../../design/musicbrainz-deezer-mapping.md](../../design/musicbrainz-deezer-mapping.md).

A genre object (also referred to as *editorial* in the Deezer API).

Live example: <https://api.deezer.com/genre/0> ([API explorer](https://developers.deezer.com/api/explorer?url=genre/0)).

## Fields

| Name | Type | Description |
| :-- | :-- | :-- |
| `id` | int | The editorial's Deezer id |
| `name` | string | The editorial's name |
| `picture` | url | The url of the genre picture. Add a `size` parameter to the url to change size: `small`, `medium`, `big`, `xl` |
| `picture_small` | url | The url of the genre picture in size small |
| `picture_medium` | url | The url of the genre picture in size medium |
| `picture_big` | url | The url of the genre picture in size big |
| `picture_xl` | url | The url of the genre picture in size xl |

## Connections

| Name | Description | Returns |
| :-- | :-- | :-- |
| [genre / artists](https://developers.deezer.com/api/genre/artists) | Returns all artists for a genre | An object of type [artist](https://developers.deezer.com/api/artist) |
| [genre / radios](https://developers.deezer.com/api/genre/radios) | Returns all radios for a genre | An object of type [radio](https://developers.deezer.com/api/radio) |

## Usage in this plugin

- The plugin consumes only `genres.data[].name` from the genre objects embedded in the album response (mapped to the `genre` tag with `count: 1` — the only fields Picard's `add_genres_from_node()` reads).
- Genre `id` and the `picture` family have no tag value and are dropped; the `genre/artists` and `genre/radios` connections are not exercised.