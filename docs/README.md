# MetaStreaming ("Streaming Metadata") — Documentation

Documentation for the **Streaming Metadata** Picard v3 plugin (`picard/plugins/meta-streaming/`, MANIFEST uuid `359c2dd1-a6a1-4e05-a441-d3e93bba7a43`).

## What the plugin does

The plugin lets MusicBrainz Picard load album metadata from **Deezer** (and, by design, other streaming services in the future) as a direct alternative to the MusicBrainz database. Search for albums from a cluster or by free-text query, load a result, and Picard tags the matched files exactly as it would for a MusicBrainz release — native file matching, tagger scripts, cover art and session persistence all work unmodified.

It achieves this with a **Synthetic MusicBrainz Adapter**: Deezer JSON responses are translated into the internal MusicBrainz "release node" format that Picard core already consumes, with deterministic synthetic MBIDs generated from a two-tier `uuid5` scheme, and the node is fed through Picard's own album-parsing pipeline.

## Documentation map

### Start here

| Document | Audience | Content |
| :-- | :-- | :-- |
| [architecture.md](architecture.md) | developers, curious users | The core idea: the Synthetic MusicBrainz Adapter pattern, component roles, why it works |
| [dataflow.md](dataflow.md) | developers | End-to-end runtime walkthrough: search → load → node assembly → native parsing |
| [uuid-scheme.md](uuid-scheme.md) | developers | Synthetic MBID derivation: two-tier `uuid5` namespaces, determinism, minimization |
| [providers.md](providers.md) | developers | Multi-provider abstraction and a step-by-step guide for adding a new streaming service |
| [configuration.md](configuration.md) | users, developers | Options reference: rate limit, cover size, explicit tagging, persistence |
| [limitations.md](limitations.md) | users, developers | Consolidated known limitations and hazards of synthetic MBIDs |

### Design records and process

| Document | Content |
| :-- | :-- |
| [roadmap.md](roadmap.md) | Development roadmap: completed stages 1–5 and planned stages 6–7 |
| [design/cover-art-piggyback-mechanism.md](design/cover-art-piggyback-mechanism.md) | Stage 6 design record: why delivering cover art via an injected `cover art link` URL relation through the native `UrlRelationships` provider works |
| [design/explicit-tag-analysis.md](design/explicit-tag-analysis.md) | Decision record: the Deezer explicit flag is materialized as the user-visible `explicit` tag (freeform-written via Picard's native path), not an internal variable |
| [design/track-response-analysis.md](design/track-response-analysis.md) | Analysis: three track-data shapes, additional-tag candidates (`bpm` recommended), pipeline optimization (keep the fan-out) |
| [design/musicbrainz-deezer-mapping.md](design/musicbrainz-deezer-mapping.md) | Verified field-level audit: every Deezer field vs. the synthetic node vs. what Picard actually consumes |

### Reference

| Document | Content |
| :-- | :-- |
| [reference/module-map.md](reference/module-map.md) | File-by-file reference of the plugin package |
| [reference/deezer-api.md](reference/deezer-api.md) | Deezer API endpoints used by the plugin and the example API-response artifacts |
| [reference/deezer/global-parameters.md](reference/deezer/global-parameters.md) | Deezer API doc fragment: global parameters (pagination, access token, request methods) |
| [reference/deezer/album.md](reference/deezer/album.md) | Deezer API doc fragment: album object fields, related actions, connections |
| [reference/deezer/track.md](reference/deezer/track.md) | Deezer API doc fragment: track object fields, actions, related actions |
| [reference/deezer/genre.md](reference/deezer/genre.md) | Deezer API doc fragment: genre/editorial object fields, connections |
| [reference/deezer/search.md](reference/deezer/search.md) | Deezer API doc fragment: search endpoints, optional parameters, advanced search |
| [reference/multi-value-tags.md](reference/multi-value-tags.md) | Reference note: how multi-value (list) tags are written to files per format, vs. joined strings |
| [reference/picard/basic-tags.md](reference/picard/basic-tags.md) | Picard doc fragment: basic tags (from MusicBrainz, plugin/script-populated, iTunes-specific) |
| [reference/picard/advanced-tags.md](reference/picard/advanced-tags.md) | Picard doc fragment: advanced tags (track relationship and genre tags) |
| [reference/mp3tag/tags.md](reference/mp3tag/tags.md) | Mp3tag doc fragment: tag field mappings across ID3v2, MP4, Matroska, ASF, RIFF INFO |
| [reference/MusicBrainz API - MusicBrainz.html](reference/MusicBrainz%20API%20-%20MusicBrainz.html) | Saved web page: MusicBrainz API release schema reference |
| [reference/MusicBrainz Picard Tag Mapping.html](reference/MusicBrainz%20Picard%20Tag%20Mapping.html) | Saved web page: Picard tag mapping table (which tags are written to files) |

## Quick start for users

1. Install the plugin (Picard → Options → Plugins, or `picard-cli plugins install <path>`).
2. Load files into Picard and cluster them.
3. Right-click the cluster → **Get metadata from streamings** (or use the plugin's search dialog manually).
4. Pick a result and press **Load into Picard**; files are matched and tagged like any MusicBrainz release.

Options live under **Options → Plugins → Streaming Metadata**: request rate limit, preferred cover art size, and explicit-track tagging. See [configuration.md](configuration.md).

## Status

Stages 1–5 of the [roadmap](roadmap.md) are complete (API v3 migration, parallel loading, options UI, multi-provider layer, mapping audit + MBID minimization), and Stages 8–9 (the `explicit` / `deezer_track_id` / `bpm` track metadata processor, genre-list materialization, ID-tag naming convention, fan-out decision) are implemented and tested. Stage 6 (cover art via URL-relationship piggyback) and Stage 7 (optional synthetic-MBID stripping on save) are planned — see [limitations.md](limitations.md) for the currently visible consequences.