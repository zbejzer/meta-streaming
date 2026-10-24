# Deezer API — Global Parameters

> Fragment of the official Deezer API documentation ([developers.deezer.com/api](https://developers.deezer.com/api)), converted from HTML for offline reference. Companion fragment: [album.md](album.md). How this plugin uses these endpoints: [../deezer-api.md](../deezer-api.md).

Deezer API provides some global parameters in order to simplify and organize your requests.

## Pagination parameters

When the return of your request is a list of objects, you do not have to get the whole result at once — you can paginate it. Some parameters can be used to constrain the number of objects the request returns.

| Parameter | Meaning |
| :-- | :-- |
| `index` | The offset of the first object you want to get |
| `limit` | The maximum number of objects to return |

### Request examples

- <https://api.deezer.com/playlist/4341978/tracks?index=0&limit=10>
- <https://api.deezer.com/playlist/4341978/tracks?index=3&limit=7>
- <https://api.deezer.com/playlist/4341978/tracks?limit=2>

## Access token

Deezer API uses the OAuth 2.0 protocol for authentication and authorization as described [here](https://developers.deezer.com/api/oauth). This protocol provides an access token according to the [permissions](https://developers.deezer.com/api/permissions) you need to interact with the user, and what they accept to share with your application.

Once you get it, you can use it easily thanks to the **`access_token`** parameter in your request. This token expires after a defined duration automatically, and has to be renewed.

## Request methods

Deezer API is a RESTful API: use GET HTTP requests to get information, POST HTTP requests to update/add data, and DELETE HTTP requests to delete it.

A special parameter **`request_method`** is provided in order to override the HTTP request and allows POST or DELETE semantics using a GET HTTP request instead.

### Request example

```text
https://api.deezer.com/album/302127?note=5&request_method=POST
```

## Relevance to this plugin

The plugin only performs **anonymous GET** requests (no `access_token`, `mblogin=False`), and uses `index`/`limit` pagination for the album search (`GET /search/album`, page size 25). The `request_method` override and OAuth flows are not exercised.