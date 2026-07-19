# Dandelion

A fast, private web browser built on Firefox.

Dandelion is a Firefox-based browser, not an embedder or a shell. Its
interface is built with Gecko's own chrome layer and its features are
implemented against Firefox's subsystems.

## Repository layout

This is an **overlay** repository. It contains Dandelion's code and a small set
of patches; Firefox itself is a pinned dependency that is cloned into a
separate directory and never committed here. See
[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for why.

| Path | Contents |
| --- | --- |
| `FIREFOX_VERSION` | The pinned Firefox release |
| `branding/` | Product identity, mounted into the Firefox tree |
| `patches/` | Generated diffs against upstream Firefox |
| `build/` | Sync, patch and build tooling; mozconfigs |
| `docs/` | Architecture, build and patch documentation |

## Getting started

```sh
python build\sync.py --bootstrap   # clone Firefox, mount branding, patch
python build\build.py              # build
```

Prerequisites, toolchain setup and platform notes are in
[docs/BUILDING.md](docs/BUILDING.md). A full build takes 30-60 minutes; an
artifact build takes 1-2.

## Documentation

- [Architecture](docs/ARCHITECTURE.md) — the overlay model and where code belongs
- [Building](docs/BUILDING.md) — toolchain, checkout and build configurations
- [Patches](docs/PATCHES.md) — how upstream changes are managed

## Licence

Dandelion's own source — everything in this repository — is licensed under the
[Mozilla Public License 2.0](LICENSE).

Firefox is not part of this repository. It is cloned separately and remains
under the Mozilla Public License 2.0, alongside the other licences in its tree.

MPL-2.0 is file-level copyleft: modifications to Dandelion's files stay open,
while the browser can still be distributed with the proprietary components a
production browser depends on — most importantly the Widevine CDM, without
which Netflix, Spotify and other DRM-protected services will not play. It is
also Firefox's own licence, so Dandelion and Gecko share one.
