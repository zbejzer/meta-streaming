# MusicBrainz vs. Deezer Album API Mapping Report

This document maps fields from the MusicBrainz API release response (`album_mb.json`) to the equivalent Deezer API album response (`album_dzr.json`).

## Field Mapping Table

| MusicBrainz Field (`album_mb.json`) | Deezer Field (`album_dzr.json`) | Description / Notes |
| :--- | :--- | :--- |
| `id` | `id` *(implicit in track/artist structure, URL)* | MusicBrainz Release MBID vs Deezer numeric album ID. |
| `title` | `title` | Release title (e.g., *"Hello, I Must Be Going (2016 Remaster)"*). |
| `artist-credit` | `artist` / `contributors` | Main artist credits and contributors (e.g., *Phil Collins*). |
| `barcode` | `upc` | Universal Product Code / EAN barcode. |
| `date` | `release_date` | Release date (MusicBrainz uses `date`, Deezer uses `release_date`). |
| `label-info` / `label-info-list` | `label` | Record label associated with the release (e.g., *Rhino*). |
| `media` → `track-list` | `tracks` / `tracks.data` | Track listings, track titles, and positions. |
| `media` → `track-list` → `length` | `tracks.data.duration` | Track duration in milliseconds (MusicBrainz) vs seconds (Deezer). |
| `release-group` → `primary-type` | `record_type` | Release/record type (e.g., `"Album"`). |
| `genres` / `tags` | `genres` | Musical genres/tags associated with the release or artist. |

---

## Missing Information Analysis

### 1. Information Present in Deezer but **Missing** in MusicBrainz:
- **Streaming & Fan Metrics:** Fan count (`fans`), explicit content flags (`explicit_lyrics`, `explicit_content_lyrics`, `explicit_content_cover`), and availability status (`available`).
- **Media Previews & Links:** 30-second audio preview streaming URLs (`preview`), web links/sharing URLs (`link`, `share`, `tracklist`).
- **Artwork Hashes / URLs:** Deezer cover image identifiers (`cover`, `cover_small`, `cover_medium`, `cover_big`, `cover_xl`, `md5_image`), whereas MusicBrainz relies on Cover Art Archive (CAA) IDs/URLs.

### 2. Information Present in MusicBrainz but **Missing** in Deezer:
- **Unique Identifiers (MBIDs):** Globally unique identifiers for the release (`id`), release group, artist (`artist.id`), recordings (`recording.id`), and tracks (`track.id`).
- **Detailed Release Metadata:** Country of release (`country`), release status (`status`: *Official*, etc.), packaging info, disambiguation comments (`disambiguation`), and explicit ISO language/script codes.
- **ISRC & ASIN Codes:** International Standard Recording Codes (ISRCs) for individual tracks and Amazon Standard Identification Numbers (ASINs) where linked.
- **Rich Tagging & Folksonomy:** Detailed tag counts and genre frequency lists (`tags` with counts).
