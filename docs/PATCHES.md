# Patches

Every patch in `patches/` is a permanent maintenance cost, paid again at every
Chromium roll. This document exists to keep that cost low.

## Workflow

Patch files are **generated, never hand-written**.

```sh
# 1. Edit the upstream file directly in the Chromium checkout.
#    C:\src\chromium\src\chrome\app\theme\chromium\BRANDING

# 2. Capture the edit as a patch.
python build/update_patches.py

# 3. Commit the generated patch to this repository.
```

To capture only specific files, name them:

```sh
python build/update_patches.py chrome/app/theme/chromium/BRANDING
```

To reapply the full set to a clean checkout:

```sh
python build/apply_patches.py
```

`apply_patches.py` skips patches that are already present, so it is safe to
re-run. `--reset` restores each target to pristine upstream state first,
discarding local edits to those files.

## Naming

A patch is named after the upstream path it modifies, with separators flattened:

```text
chrome/browser/ui/views/frame/browser_view.cc
  -> chrome-browser-ui-views-frame-browser_view.cc.patch
```

That flattening is ambiguous in principle, so the tooling recovers the real
target by parsing the `+++ b/<path>` header inside the diff, never by
un-mangling the file name.

## Policy

Before adding a patch, exhaust the alternatives in this order:

1. **Use an existing extension point.** Chromium is full of delegates,
   observers, factories and `base::Feature` flags that exist precisely so
   downstream code does not have to patch. This costs nothing at roll time.
2. **Add the logic under `//dandelion`** and patch upstream with a single call
   into it. A one-line hook almost always survives a roll untouched.
3. **Change upstream substantively.** Last resort. Justify it in the commit
   message.

A patch that reimplements Chromium behaviour rather than delegating to
Dandelion code is a defect: it will conflict on the first roll that touches the
surrounding lines.

New files never belong upstream. Code added to `//dandelion` needs no patch at
all, which is the entire point of the overlay.

## Rolling

When a patch fails to apply after a roll, `git apply --3way` has already tried
a three-way merge and lost. Rebase it by hand in the checkout, then re-run
`update_patches.py` to regenerate it.

Patches whose target file is no longer modified are stale — the change was
reverted, or upstream absorbed it. `update_patches.py --prune` removes them.
Deleting a patch you no longer need is the cheapest possible improvement to
this repository.
