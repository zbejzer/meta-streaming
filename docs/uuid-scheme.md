# Synthetic UUID Scheme

> How the plugin generates stable MusicBrainz-shaped IDs for streaming entities. Context: [architecture.md](architecture.md); why some IDs were deliberately *not* generated: [design/musicbrainz-deezer-mapping.md](design/musicbrainz-deezer-mapping.md).

## 1. Why synthetic MBIDs at all

The synthetic release node must carry UUIDs wherever a genuine MusicBrainz node carries MBIDs, because Picard core **hard-accesses** them:

- `get_release_group_by_id(rg_node["id"])` (`picard/album.py`)
- `n["artist"]["id"]` in `artist_credit_to_metadata` (`picard/mbjson.py`)
- `Track(track_node["recording"]["id"], …)` (`picard/album.py`)
- album dict keying in `tagger.albums`, TracksCache matching, `mbid_validate()` on file load, and every format's `musicbrainz_*` tag mapping.

Generating them is unavoidable. The design question is *how*, and the answer has three requirements:

1. **Stable** — the same provider item must always map to the same UUID: re-loading an album must reuse the existing `Album` object, release-group grouping must deduplicate, and session files must round-trip.
2. **Collision-free** — different providers, different entity types, and different items must never clash.
3. **Scalable** — adding a provider (or entity type) must not require registering per-item IDs.

## 2. The two-tier `uuid5` derivation

The scheme (`providers.py`) uses RFC 4122 name-based UUIDv5 (SHA-1 over a namespace UUID + a name string) in two tiers:

```text
Tier 0:  PROVIDER_ROOT_UUIDS[provider]                     (one pregenerated constant per provider)
Tier 1:  entity_namespace = uuid5(provider_root, entity_type)   (derived dynamically)
Tier 2:  item_uuid         = uuid5(entity_namespace, item_id)    (derived dynamically)
```

So a final ID is the pure function:

```python
uuid = uuid5(uuid5(PROVIDER_ROOT_UUIDS[provider], entity_type.value), str(item_id))
```

Properties that fall out of this construction:

- **Deterministic**: no storage, no registry, no randomness. The UUID depends only on `(provider root, entity type, provider item id)` — identical on every machine, forever.
- **Collision-free across providers**: each provider has an independent root namespace, so identical numeric IDs from different services cannot collide.
- **Collision-free across entity types**: each entity type is hashed in its own namespace derived from the root, so a release and a release-group of the same item hash differently.
- **Cheap extension**: a new provider needs exactly **one** new root UUID (Tier 0); entity namespaces and all item UUIDs derive automatically. A new entity type needs no constants at all.

### Concrete example (Deezer, root `67e48b9e-dd7e-11ef-9282-325096b39f47`)

| Item | Value |
| :-- | :-- |
| `release` entity namespace | `5a199062-623e-5519-bb31-9982ec0c88b7` |
| `release_group` entity namespace | `4c8a3948-a377-5240-ab35-cf49f1ffe7e0` |
| `artist` entity namespace | `aca96a5e-9660-5513-891d-78706434899b` |
| `track` entity namespace | `dc15f573-8e11-535c-b49e-77a77e64bba6` |
| Deezer album `12400342` → release UUID | `53973a32-1e5f-5d64-8825-b99ab5ea07b0` |
| Deezer album `12400342` → release-group UUID | `d6acb629-4e0c-5d28-b129-a7ff3fe6047d` |
| Deezer artist `186` (Phil Collins) → artist UUID | `c36c8ec7-d644-5a8b-9ff2-0eed8469a36a` |

## 3. Provider roots

Pregenerated root UUIDs (constants in `providers.py` — changing any of them changes *every* derived ID, so they are effectively frozen):

| Provider | Root UUID | Status |
| :-- | :-- | :-- |
| `deezer` | `67e48b9e-dd7e-11ef-9282-325096b39f47` | implemented |
| `spotify` | `138a0f0d-ef34-4b82-9382-f5421d8b2e11` | reserved |
| `tidal` | `9a823b12-9c12-4211-a832-11849a029312` | reserved |
| `qobuz` | `4c312984-7a11-490b-923a-f11182743810` | reserved |
| `apple_music` | `8a2e1932-b012-411a-8219-c4391a827402` | reserved |

`Provider` and `EntityType` are `StrEnum`s, so they interoperate with plain strings idiomatically (`Provider(x)` is idempotent for `StrEnum` values).

## 4. Entity types — and the minimization audit

Only entity types with verified consumers in Picard core are generated (Stage 5 audit, full traces in the [mapping report](design/musicbrainz-deezer-mapping.md)):

| `EntityType` | Consumed as | Notes |
| :-- | :-- | :-- |
| `release` | `musicbrainz_albumid` | Album dict key, cover-art routing, file placement on re-add |
| `release_group` | `musicbrainz_releasegroupid` | Hard access in `picard/album.py`; RG cover art |
| `artist` | `musicbrainz_artistid` / `musicbrainz_albumartistid` | Hard access in `artist_credit_to_metadata` |
| `track` | `musicbrainz_trackid` | Track matching; **recording nodes reuse the track UUID** |

Deliberately **removed** (zero consumers, verified):

- `label` — `label_info_from_node()` reads only `name`/`catalog-number`; no `musicbrainz_labelid` tag exists anywhere in Picard. The node keeps `label-info[].label.name` only.
- `recording` (as a separate namespace) — `generate_recording_UUID()` was dead code; the recording node is a `dict(track)` copy and therefore already carries the track UUID, which is exactly what `Track(track_node["recording"]["id"], …)` consumes. AcoustID/ISRC flows key off the same value.
- `asin` placeholder — falsy values are skipped by `_node_skip_empty_iter()` before mapping anyway.

The recording-reuses-track decision is the reason a synthetic release produces `musicbrainz_trackid == musicbrainz_recordingid` for each track — harmless for tagging and matching, and one fewer namespace to maintain.

## 5. The `MetadataProvider` API

```python
MetadataProvider(provider, actual_id="")      # ValueError on unknown provider
.get_entity_namespace(entity_type) -> UUID    # tier 1
.generate_uuid(entity_type, item_id=None)     # tier 2; item_id defaults to the constructor's actual_id
.generate_release_UUID(item_id=None)
.generate_releasegroup_UUID(item_id=None)
.generate_artist_UUID(item_id=None)
.generate_track_UUID(item_id=None)
```

- `actual_id` is the provider's native key (for Deezer, the numeric album/artist/track id as a string). Artist UUIDs fall back to hashing the artist *name* when the contributor node has no `id` — still deterministic within a provider.
- `Names = Provider` is kept as a backward-compatibility alias.
- The instance is attached to the loaded album as the transient `album.metastreaming_provider` and handed to every node-builder so all UUIDs for one load derive from one provider context.

## 6. Known hazard (by design, documented)

Synthetic UUIDs are well-formed UUIDv4-shaped strings and pass Picard's `mbid_validate()`, so core will treat them as real MBIDs in flows that talk *to* MusicBrainz: re-adding saved files triggers MB lookups that 404, metadatabox lookups open nonexistent musicbrainz.org pages, and ISRC/AcoustID submission would submit synthetic recording IDs. These are accepted trade-offs of the adapter pattern; Stage 7 of the [roadmap](roadmap.md) adds an optional pre-save strip, and the full list lives in [limitations.md](limitations.md).