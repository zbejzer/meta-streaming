# Picard — Advanced Tags

> Fragment of the official Picard documentation ([Tags & Variables → Advanced Tags](https://picard-docs.musicbrainz.org/variables/tags_advanced.html)). Copyright © MetaBrainz Foundation, licensed [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0). Converted from HTML for offline reference. Companion fragment: [basic-tags.md](basic-tags.md).

You can make additional tags available by enabling the [Use track relationships](https://picard-docs.musicbrainz.org/config/options_metadata.html) and/or the [Use genres from MusicBrainz](https://picard-docs.musicbrainz.org/config/options_genres.html) settings in Picard.

Some tags provide the MusicBrainz Identifier (MBID) of the entity. The MBID is a 32-character identifier assigned to an entity (e.g.: artist, album, track or work) to uniquely identify the entity. For more information about MBIDs, please see the [MusicBrainz Identifier](https://musicbrainz.org/doc/MusicBrainz_Identifier) page in the MusicBrainz documentation.

> **Note**
>
> Tags will not be created and will not be available as variables if there was no value retrieved for the tag from the MusicBrainz database.
>
> Some of these tags are only supported for certain file types or tag formats. Please see the [Picard Tag Mapping](https://picard-docs.musicbrainz.org/appendices/tag_mapping.html) section for details.

## Track Relationship Tags

If you enable "Use track relationships" in the Option settings, you get these extra tags:

- **`arranger`** — The names of the arrangers associated with the track. These can include the instrument and orchestra arrangers, and could be associated with the release, recording or work. (since Picard 0.10)
- **`composer`** — The names of the composers for the associated work.
- **`composersort`** — The sort names of the composers for the associated work.
- **`conductor`** — The names of the conductors associated with the track. These can include the conductor and chorus master, and could be associated with the release or recording.
- **`director`** — The director of a track as provided by the *Video Director* or *Audio Director* relationship in MusicBrainz. (Since Picard 2.6, updated in Picard 2.9)
- **`djmixer`** — The names of the DJ mixers for the track. (since Picard 0.9)
- **`engineer`** — The names of the engineers associated with the track.
- **`language`** — Work lyric language as per [ISO 639-3](https://en.wikipedia.org/wiki/ISO_639-3) if a related work exists. (since Picard 0.10)
- **`license`** — The licenses associated with the track, either through the release or recording relationships. (since Picard 1.0)
- **`lyricist`** — The names of the lyricists for the associated work.
- **`mixer`** — The names of the "*Mixed By*" engineers associated with the track. (since Picard 0.9)
- **`musicbrainz_workid`** — The MBID for the Work if a related work exists.
- **`musicbrainz_composerid`** — A multi-value tag containing the MusicBrainz Identifier (MBID) for the composer(s) of the associated work (since Picard 3.0). The MBIDs appear in the same order as the corresponding names in the `composer` tag.
- **`performer:<type>`** — The names of the performers for the specified type. These types include:
  - vocals or instruments for the associated release or recording, where `<type>` can be "*vocal*", "*guest guitar*", "*solo violin*", etc.
  - the orchestra for the associated release or recording, where `<type>` is "*orchestra*"
  - the concert master for the associated release or recording, where `<type>` is "*concertmaster*"
- **`producer`** — The names of the producers for the associated release or recording.
- **`remixer`** — The names of the remixer engineers associated with the track.
- **`work`** — The name of the work associated with the track. (since Picard 1.3)
- **`writer`** — A multi-value tag containing the names of the writers associated with the related work. (since Picard 1.0). This is not written to most file formats automatically. You can merge this with composers with a script like:

  ```text
  $copymerge(composer, writer)
  ```

> **Note**
>
> Some tags such as `performer` are available as both track and release level relationships, and the values may be different depending on which relationship options are enabled.

## Genre Tags

If you enable "Use genres from MusicBrainz", you get:

- **`genre`** — A multi-value tag containing the specified genre information from MusicBrainz (since Picard 2.1, earlier versions used folksonomy tags).

## Relevance to this plugin

- The "Use track relationships" setting is why the synthetic track nodes carry the `recording.relations = []` sentinel: with the setting enabled, an *absent* `relations` key makes Picard attempt real MusicBrainz recording lookups that 404 on synthetic IDs (see [architecture](../../architecture.md) and the [mapping audit](../../design/musicbrainz-deezer-mapping.md)). The sentinel keeps the setting safely inert on streaming-loaded albums — these advanced tags simply never materialize from Deezer data.
- The `genre` tag is populated from the plugin's synthetic `genres` nodes (`{name, count: 1}`) when "Use genres from MusicBrainz" is enabled.
- Picard's tag parsing acts on only two URL-relation types — `amazon asin` → `asin` and `license` → `license` — which is why the Stage 6 `cover art link` relation is a tag no-op (see the [piggyback design record](../../design/cover-art-piggyback-mechanism.md)).