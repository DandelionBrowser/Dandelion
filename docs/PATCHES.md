# Patches

Every patch in `patches/` is a permanent maintenance cost, paid again at every
Firefox roll. This document exists to keep that cost low.

## Workflow

Patch files are **generated, never hand-written**.

```sh
# 1. Edit the upstream file directly in the Firefox checkout.
#    C:\src\firefox\browser\base\content\browser.js

# 2. Capture the edit as a patch.
python build\update_patches.py

# 3. Commit the generated patch to this repository.
```

To capture only specific files, name them:

```sh
python build\update_patches.py browser/base/content/browser.js
```

To reapply the full set to a clean checkout:

```sh
python build\apply_patches.py
```

`apply_patches.py` skips patches that are already present, so it is safe to
re-run. `--reset` restores each target to pristine upstream state first,
discarding local edits to those files.

## Naming

A patch is named after the upstream path it modifies, with separators
flattened:

```text
browser/base/content/browser.js
  -> browser-base-content-browser.js.patch
```

That flattening is ambiguous in principle, so the tooling recovers the real
target by parsing the `+++ b/<path>` header inside the diff, never by
un-mangling the file name.

## Policy

Before adding a patch, exhaust the alternatives in this order:

1. **Use a pref, or an existing extension point.** Firefox is heavily
   pref-driven, and a pref costs nothing at roll time.
2. **Add Dandelion's logic in its own file** and patch upstream with a single
   line that loads it. A one-line hook almost always survives a roll untouched.
3. **Change upstream substantively.** Last resort. Justify it in the commit
   message.

Branding needs no patch at all: `branding/` is mounted into the tree at
`browser/branding/dandelion`, so a roll never touches it. Prefer that shape —
code that lives in this repository and is mounted or loaded, rather than
pasted into Firefox's own files.

## Rolling

When a patch fails to apply after a roll, `git apply --3way` has already tried
a three-way merge and lost, and has left conflict markers in the target file.
Resolve them in the checkout, then re-run `update_patches.py` to regenerate the
patch.

Patches whose target file is no longer modified are stale — the change was
reverted, or upstream absorbed it. `update_patches.py --prune` removes them.
Deleting a patch you no longer need is the cheapest possible improvement to
this repository.
