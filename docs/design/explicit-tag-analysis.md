# Decision Record — Should Deezer's Explicit Flag Reach Track Metadata?

> Resolves the Stage 5 item "Resolve `~explicit` handling" from [`roadmap.md`](../roadmap.md). Evidence: the vendor reference fragments — [`../reference/deezer/album.md`](../reference/deezer/album.md) (Deezer fields), [`../reference/picard/basic-tags.md`](../reference/picard/basic-tags.md) (Picard's tag set), [`../reference/mp3tag/tags.md`](../reference/mp3tag/tags.md) (per-format file mappings) — plus the field-level audit in [musicbrainz-deezer-mapping.md](musicbrainz-deezer-mapping.md), `picard/mbjson.py`, and the format writers in `picard/formats/`.

## 1. The data

| Deezer field | Type | Meaning |
| :-- | :-- | :-- |
| `explicit_lyrics` (track + album) | boolean | "Whether the track contains explicit lyrics" |
| `explicit_content_lyrics` (track + album) | int 0–7 | 0 Not Explicit · 1 Explicit · 2 Unknown · 3 Edited · 4 Partially Explicit (album "lyrics" only) · 5 Partially Unknown (album "lyrics" only) · 6 No Advice Available · 7 Partially No Advice Available (album "lyrics" only) |
| `explicit_content_cover` (track + album) | int 0–7 | Same scale, for the cover art |

Current behavior: the `tag_explicit` option (default on) makes `_mb_track_from_track()` set `track["explicit"] = True` on the synthetic track node — and nothing else. `track_to_metadata()` has no `explicit` branch (verified against `picard/mbjson.py`), so the node key alone never passes through: **some bridge into `Metadata` is required regardless of the tag name chosen.**

## 2. Is the data valuable?

**Yes — uniquely so, as track metadata:**

1. **MusicBrainz has no advisory data at all.** The mapping report's "Missing Information Analysis" lists the explicit content flags as Deezer-only information; no MusicBrainz field carries it. The plugin is the only source of this signal in the entire tagging flow — dropping it forfeits information no other source can provide.
2. **It disambiguates release variants.** Deezer serves explicit and clean/edited variants of the same album as separate album objects with near-identical titles (`explicit_content_lyrics = 3` means "Edited"). The per-track boolean lets users tell them apart after loading — decision-relevant for parental-control, broadcast, and library-curation contexts.
3. **The cost is one trivial processor.** The synthetic node already carries the flag; `register_track_metadata_processor()` hands plugins the raw `track_node` dict (`picard/plugin3/api_impl.py:892`, signature `(api, track, metadata, track_node, release_node)`), and core invokes track processors during album parsing (`picard/album.py:723`).

The granular 0–7 scale, by contrast, stays **dropped**: several of its states are album-"lyrics"-scoped rather than per-track, and nothing in Picard or any file format consumes the granularity. The boolean is the reliable, per-track signal — consistent with the Stage 5 audit verdict on `explicit_content_*`.

## 3. Can it reach files? — yes, as a user-visible tag

An earlier revision of this record claimed the flag "cannot become a file tag through the native pipeline" because Picard's documented tag set has no advisory entry. **That reasoning was wrong**, and it matters: Picard's *documented* tag list only describes what is populated from MusicBrainz data — it is not a whitelist of what Picard can write. Arbitrary tags are a sanctioned, first-class Picard workflow:

- **The UI supports them**: the metadata box offers "Add New Tag…" (`picard/ui/metadatabox/__init__.py:349`), and user-added tags flow through the standard save path like any other tag.
- **The format writers write them natively** (all verified in the bundled 3.0.2 sources):

| Format | `explicit` written? | Representation | Code |
| :-- | :-- | :-- | :-- |
| MP3 (ID3v2) | yes | `TXXX:explicit` freeform frame | `id3.py:589→594` → `_save_custom_tag` (id3.py:940) |
| MP4 (M4A) | yes | `----:com.apple.iTunes:explicit` freeform atom | `mp4.py:413–416` (`_get_tag_name` final branch) |
| FLAC / Ogg / Opus / Speex | yes | `EXPLICIT=1` comment (Vorbis comments are freeform by design) | `vorbis.py:446` |
| APEv2 | yes | `explicit=1` freeform item | `apev2.py:309` |
| WAV | yes | ID3v2 chunk (`TXXX:explicit`); the RIFF INFO chunk is a fixed standard set and does not carry it | `wav.py` (ID3-chunk based) |
| WMA (ASF) | **no** | `supports_tag()` is restricted to known `WM/…`/standard names (`asf.py:331`); unmapped names are dropped | `asf.py:331–336` |

- **External tooling round-trips them**: Mp3tag's field-mapping reference handles unmapped fields generically ("Other fields": `TXXX:fieldname` / `----:com.apple.iTunes:fieldname` / `T=30 fieldname`), so a written `explicit` tag survives Extended-Tags editing in Mp3tag.
- **Tilde names are the exception, not the rule**: only `~`-prefixed variables are excluded from file writing (`supports_tag()` in every format skips `~`-names). A regular tag name follows the user-tag path; `~explicit` would have been invisible in the UI and unwritten — strictly less useful than what the option always promised.

Two things remain true from the earlier analysis:

- **No standard advisory tag exists in the format ecosystem** (Mp3tag's table: the only advisory mapping anywhere is the MP4-exclusive `rtng`/`ITUNESADVISORY` atom). A written `explicit` tag is a freeform, community-convention tag — not a format-standard one.
- **Picard has no mapping to `rtng`**, so the plugin cannot produce the iTunes advisory atom through Picard's native path — and bypassing Picard's writers with plugin-side mutagen surgery is out of scope (see §5).

**Purity principle, re-scoped**: the Stage 5 audit's guarantee was that nothing *leaks unintentionally* from the synthetic node translation — every tag Picard derives from the node was verified against Picard's own mapping. A deliberate, documented, option-controlled tag that appears in the metadata box where the user can edit or remove it per-track is the same category as a user-added tag, not leakage. The plugin adds exactly one such tag (`explicit`) and nothing else.

## 4. Decision

1. **Materialize the regular `explicit` tag** (value `"1"`) via a track metadata processor — planned as [roadmap Stage 8](../roadmap.md): when `track_node["explicit"]` is truthy (set by `_mb_track_from_track` from `explicit_lyrics`), set `metadata["explicit"] = "1"`; no-op otherwise (a fresh `Metadata` is built per parse, so no stale-value handling is needed).
2. **Why the regular name over `~explicit`**: visible and editable in the metadata box (user can delete it like any UI-added tag), scriptable as `%explicit%`, written as a freeform tag on MP3/MP4/FLAC/Ogg/APE/WAV where players and tools can read it, and round-trippable through Mp3tag. The tilde variant would have been invisible, unwritten, and inferior to what the option title always promised.
3. **The `tag_explicit` option remains the user's control**, default `True` — it now does what its title says. Unticking keeps files free of the tag. The stale "(~explicit)" parenthetical in the option title becomes "(explicit)" (Stage 8, `options.py` — a plain `_()` string, not a `const/` domain string).
4. **No format-specific surgery**: the tag goes through Picard's native freeform path only. WMA files simply do not carry it (ASF restriction); no plugin bypass to be added.
5. **Keep the granular `explicit_content_*` scale dropped.**

## 5. Rejected alternatives

| Alternative | Why rejected |
| :-- | :-- |
| `~explicit` internal variable only | Invisible in the UI, never written to files, not referenceable as `%explicit%` — strictly weaker than the user-visible tag the option promised. Retained only as this record's earlier, corrected position. |
| Write `rtng` / `ITUNESADVISORY` for MP4 files | Picard has no mapping to `rtng`; would require bypassing Picard's writers with plugin-side mutagen surgery — violating the adapter pattern for one narrow format. Revisit only if Picard core ever grows native advisory-tag support. |
| Surface the full 0–7 scale as `explicit_content_lyrics` | Album-scoped states with no consumer anywhere; dead weight per the minimization principle. |
| Drop the option / drop the flag | Loses uniquely available, decision-relevant data that MusicBrainz cannot provide. |

## 6. Verification pointers for Stage 8

- **Unit test (test-first)**: parse a synthetic node whose track carries `explicit: True` → the track's metadata contains `explicit == "1"`; with `explicit` absent or with `tag_explicit` disabled → no `explicit` key. Keep as a permanent regression test.
- **Purity**: the processor performs a single metadata addition — no node mutation, no file-format code paths; `release_to_metadata()`/`track_to_metadata()` output is otherwise unchanged, and `explicit` is the plugin's only deliberate freeform tag.
- **Format spot-check**: saved MP3 → `TXXX:explicit` frame; saved MP4 → `----:com.apple.iTunes:explicit` atom; saved WMA → no such tag.
- **Lint**: `ruff format` + `ruff check` on every touched file.