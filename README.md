# Dandelion

A fast, private web browser built on Chromium.

Dandelion is a Chromium browser, not an embedder or a shell. Its interface is
built with Chromium's native Views framework and its features are implemented
against Chromium's own subsystems.

## Repository layout

This is an **overlay** repository. It contains Dandelion's code and a small set
of patches; Chromium itself is a pinned dependency that is fetched into a
separate directory and never committed here. See
[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for why.

| Path | Contents |
| --- | --- |
| `CHROMIUM_VERSION` | The pinned Chromium release |
| `app/` | Product identity: branding, icons |
| `patches/` | Generated diffs against upstream Chromium |
| `build/` | Sync, patch and build tooling; GN argument files |
| `docs/` | Architecture, build and patch documentation |

## Getting started

```sh
python build/sync.py     # fetch Chromium and apply patches
python build/build.py    # configure and build
```

Prerequisites, toolchain setup and platform notes are in
[docs/BUILDING.md](docs/BUILDING.md). The first build takes hours.

## Documentation

- [Architecture](docs/ARCHITECTURE.md) — the overlay model and where code belongs
- [Building](docs/BUILDING.md) — toolchain, checkout and build configurations
- [Patches](docs/PATCHES.md) — how upstream changes are managed

## Licence

Dandelion's own source — everything in this repository — is licensed under the
[Mozilla Public License 2.0](LICENSE).

Chromium is not part of this repository. It is fetched separately and remains
under its own BSD-3-Clause licence, alongside the many third-party licences in
its tree.

MPL-2.0 is file-level copyleft: modifications to Dandelion's files stay open,
while the browser can still be distributed with the proprietary components a
production browser depends on — most importantly the Widevine CDM, without
which Netflix, Spotify and other DRM-protected services will not play. This is
the same choice Brave made, and for the same reason.
