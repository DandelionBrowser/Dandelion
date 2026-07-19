# Dandelion architecture

Dandelion is a Firefox-based browser. It is not an embedder or a shell — it is
Gecko, with Dandelion's own product identity, interface and features compiled
into it.

## The overlay model

Dandelion does **not** fork `mozilla-firefox/firefox`.

A literal fork — copying Firefox's tree and editing it in place — makes every
upstream release a merge of tens of thousands of commits into files you have
modified. Firefox ships a new release roughly every four weeks.

Instead:

- Firefox is a **pinned dependency**, cloned separately and never committed
  here. The pin lives in [`FIREFOX_VERSION`](../FIREFOX_VERSION).
- Dandelion's branding is **mounted into** the tree at
  `browser/branding/dandelion`, where upstream never writes.
- Upstream files are modified only through a small set of **patches**, each one
  deliberate and reviewable.

The cost of a Firefox roll is therefore proportional to the size of the patch
set, not to the size of Firefox. Keeping that set small is the single most
important long-term constraint on this codebase.

```text
C:\src\firefox\                     <- Firefox checkout, not version controlled
├── browser\
│   └── branding\
│       └── dandelion\  ────────┐   <- junction into this repository
├── toolkit\                    │
└── obj-dandelion-dev\          │   <- build output
                                │
c:\Users\chris\Desktop\Dandelion\    <- THIS repository
├── FIREFOX_VERSION                 <- the pinned Firefox release
├── branding\                       <- product identity, mounted above
├── patches\                        <- diffs against upstream Firefox files
├── build\                          <- sync, patch and build tooling
└── docs\
```

## Branding

[`branding/`](../branding) is a complete Firefox brand directory, mounted into
the tree rather than copied, so edits here are immediately live with no sync
step to forget. `--with-branding` in the mozconfigs points at the mount, and
[`build/lib/config.py`](../build/lib/config.py) is the single place that path is
defined.

Raster assets are **generated, not hand-maintained**. `branding/icon.png` is the
only artwork under source control; the 27 icons, tiles and installer bitmaps
Firefox expects are produced from it:

```sh
python build/generate_branding_assets.py
```

## Where code belongs

Firefox's browser interface is privileged JavaScript, CSS and markup under
`browser/`, not compiled code. That is where Dandelion's UI work happens, and it
is why an artifact build — which downloads prebuilt C++ — turns a build into a
one-to-two minute operation.

Rules that follow:

- User-visible settings are **prefs**, registered through the standard pref
  system so they inherit sync and profile isolation.
- Per-window state belongs to the window's own actor, not a global.
- Cross-process communication uses **JSActors**. Nothing else.
- New chrome code should be added as its own file and referenced from a
  one-line upstream hook, rather than pasted into an existing Firefox file.

## Patching upstream

A patch is permanent maintenance cost. Before writing one, prefer in order:

1. A pref, or an existing Firefox extension point.
2. A new file of Dandelion code that upstream loads via a single-line hook.
3. Only then, a substantive change to upstream code.

See [PATCHES.md](PATCHES.md).

## Rolling Firefox

1. Update `FIREFOX_VERSION` to the new release.
2. `python build/sync.py --no-patch`
3. `python build/apply_patches.py` and rebase whatever conflicts.
4. `python build/update_patches.py --prune` to capture the rebased result and
   drop patches upstream has absorbed.
5. Rebuild and test.

Because branding is mounted rather than patched, a roll never touches it.
