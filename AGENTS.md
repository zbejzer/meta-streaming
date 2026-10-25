# AI Agent Context for the meta-streaming plugin

> **Scope:** Guidelines for AI agents working in `picard/plugins/meta-streaming/`. Read this together with the repository root [AGENTS.md](../../../AGENTS.md) — repo-wide Picard conventions (threading, metadata access, i18n, formatting, commits) are documented there and apply here. This file covers only what is specific to this plugin.

**What is this plugin?** "Streaming Metadata" (MANIFEST uuid `359c2dd1-a6a1-4e05-a441-d3e93bba7a43`, plugin API v3): loads album metadata from Deezer into Picard by translating Deezer JSON into synthetic MusicBrainz release nodes (the "Synthetic MusicBrainz Adapter") and feeding them through Picard's native album-parsing pipeline. Entry point: `enable(api)` in `__init__.py`.

## Docs are verified ground truth

Every factual claim in `docs/` — including the file:line citations into the bundled Picard 3.0.2 sources and the behavior tables — has been verified against the code. Assume it is true:

- **Consult the docs before grepping Picard core.** When a doc cites `picard/...:NNN`, that location is accurate; go straight there when you need the source itself.
- **Do not re-verify known facts** just to be safe. Spend verification effort on new claims only — and verify any new claim the same way before writing it into a doc.
- **Keep docs in sync with code changes.** Every change updates the roadmap and the affected documents in the same pass; a code change without its doc update is incomplete.
- `examples/deezer/*.json` are captured real API responses. Use them as fixtures; do not fabricate API shapes, and do not assume network access is available (it often is not).

## Documentation map

[docs/README.md](docs/README.md) is the index. Task → document:

| Task | Read |
| :-- | :-- |
| Understand how the plugin works | `docs/architecture.md`, `docs/dataflow.md` |
| Understand synthetic MBIDs | `docs/uuid-scheme.md` |
| Add or change a field mapping | `docs/design/musicbrainz-deezer-mapping.md` |
| Add a streaming provider | `docs/providers.md` (§4 checklist) |
| Find a plugin symbol | `docs/reference/module-map.md` |
| Deezer endpoint and response shapes | `docs/reference/deezer-api.md`, `docs/reference/deezer/` |
| Picard tag behavior | `docs/reference/picard/basic-tags.md`, `docs/reference/picard/advanced-tags.md`, tag-mapping HTML |
| Current and planned work | `docs/roadmap.md`, design records in `docs/design/` |

Vendored third-party reference material (MusicBrainz HTML pages, Mp3tag mappings, Deezer docs) also lives under `docs/reference/` — it documents external systems, not this plugin.

## Running tests and Python — always via the UV virtual environment

All `python`, `pytest`, and lint execution must run inside the project virtual environment managed by UV (`ruff` and `pytest` ship in the `dev` dependency group installed by `uv sync`):

```bash
uv sync                                    # create/update .venv at the repo root
source .venv/bin/activate                  # activate before running anything
pytest test/meta_streaming/ -n auto        # plugin tests
pytest test/ -n auto                       # full suite before committing
ruff format picard/plugins/meta-streaming test/meta_streaming
ruff check picard/plugins/meta-streaming test/meta_streaming
```

Equivalent one-shot form without activating: `uv run pytest test/meta_streaming/ -n auto`. Run `ty check` on modified files when `ty` is available (pre-existing errors in the codebase can be ignored). Plugin tests live in `test/meta_streaming/` and follow the `PicardTestCase` style; never create a local `QApplication` (root AGENTS.md / `test/README.md` explain why).

## Plugin-specific gotchas

### The package is dash-named and cannot be imported normally

`meta-streaming` (dash) is loaded by Picard as a namespace package stub. Tests reproduce that via `_load_plugin_submodule()` in `test/meta_streaming/test_explicit_tag.py`. Copy that harness (`PicardTestCase`, `set_plugin_uuid(...)` with the MANIFEST uuid, `SimpleNamespace` api stubs such as `SimpleNamespace(plugin_config={...}, web_service=None)`) for new test files rather than inventing an import path for the dash-named directory.

### Synthetic node contract

- Track recordings carry `relations: []` — a required sentinel that prevents real MusicBrainz recording lookups on synthetic IDs. Never remove it; only the *release* node may gain relations.
- Synthetic UUIDs are deterministic two-tier `uuid5` derivations (`providers.py`). Never hardcode them or compute them by hand; use `MetadataProvider`.

### Tag purity

Provider-specific keys must not leak into files as unknown tags. Data reaches metadata only through `track_metadata_processor` (`deezerjson.py`) or internal `~`-prefixed keys (display-only). Release-node relations must stay a no-op in `release_to_metadata()`'s `release_ars`-gated relations branch — verify with a parse test when adding relations.

### Provider layering

Keep responsibilities in their layer (`docs/providers.md` §1): JSON-to-node translation in `deezerjson.py`, transport and URL building in `api_helpers.py`, ID derivation in`providers.py`, UI in `albumsearch.py`. A new provider adds a sibling module wired through `_API_HELPER_REGISTRY`, not edits to Deezer code.

## Working process

- Significant changes follow the roadmap process: a design/decision record under `docs/design/` first, roadmap bullets ticked during implementation, docs updated in the same change.
- Bug fixes are test-first: reproduce with a failing test, then fix, keeping the test as a permanent regression test.
- User-visible strings are translatable keys in `locale/en.toml` (`t_()` for manifest / action strings, `_()` at runtime) — add the key when adding a string.
- Do not commit agent tool directories or unrelated files (root AGENTS.md rule; review `git diff --cached` before committing).
