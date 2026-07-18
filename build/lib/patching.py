# Copyright 2026 Christian Relf. All rights reserved.
# Use of this source code is governed by the license found in the LICENSE file.

"""Generation and application of Dandelion's patches against upstream Chromium.

Every patch here is merge debt: it must be re-validated on each Chromium roll.
The overlay exists so that the patch set stays small — new code belongs under
//dandelion, and upstream files should be touched only enough to call into it.

Patches are stored one-per-upstream-file, named after the file's path with
separators flattened to '-', so `chrome/browser/ui/views/frame/browser_view.cc`
becomes `chrome-browser-ui-views-frame-browser_view.cc.patch`. That flattening
is lossy, so the target path is always recovered by parsing the diff header
rather than by trying to reverse the file name.
"""

import os
import posixpath
import re

from . import config
from . import proc

PATCH_SUFFIX = '.patch'

# Matches the "+++ b/path/to/file" line of a unified diff. Git quotes and
# escapes paths containing unusual characters, which this deliberately does not
# accept: such a path in the Chromium tree indicates a malformed patch.
_DIFF_TARGET_RE = re.compile(r'^\+\+\+ b/(.+)$', re.MULTILINE)


def patch_filename(relative_path):
  """Returns the patch file name for an upstream path relative to src/."""
  return relative_path.replace('/', '-').replace('\\', '-') + PATCH_SUFFIX


def patch_path(relative_path):
  """Returns the absolute path of the patch file for an upstream path."""
  return os.path.join(config.PATCHES_DIR, patch_filename(relative_path))


def list_patches():
  """Returns absolute paths of all patch files, in a stable order."""
  if not os.path.isdir(config.PATCHES_DIR):
    return []
  names = [n for n in os.listdir(config.PATCHES_DIR)
           if n.endswith(PATCH_SUFFIX)]
  return [os.path.join(config.PATCHES_DIR, n) for n in sorted(names)]


def target_of(patch_file):
  """Returns the upstream path (relative to src/) that a patch applies to."""
  with open(patch_file, encoding='utf-8') as f:
    contents = f.read()
  match = _DIFF_TARGET_RE.search(contents)
  if not match:
    raise ValueError('%s has no "+++ b/<path>" header; it is not a valid '
                     'unified diff' % patch_file)
  return match.group(1).strip()


def modified_files(src):
  """Returns tracked upstream files modified in the Chromium checkout.

  The comparison is against HEAD rather than the index because `git apply
  --3way` stages what it applies. A plain `git diff` would therefore report a
  freshly patched tree as unmodified, causing this to capture nothing and
  stale-detection to condemn every valid patch.

  The overlay directory is excluded: it is this repository, tracked by its own
  git, and must never be captured as a patch against Chromium.
  """
  output = proc.git_output(['diff', 'HEAD', '--name-only', '--diff-filter=M'],
                           cwd=src)
  paths = [line.strip() for line in output.splitlines() if line.strip()]
  prefix = config.OVERLAY_DIR_NAME + '/'
  return sorted(p for p in paths if not p.startswith(prefix))


def write_patch(src, relative_path):
  """Writes the diff of a single upstream file to patches/, returning its path.

  The diff is taken against HEAD so that changes already staged by a previous
  `git apply --3way` are included; see modified_files().

  The `index` line is preserved so that `git apply --3way` can fall back to a
  three-way merge when a Chromium roll shifts the surrounding context.
  """
  diff = proc.git_output(
      ['diff', 'HEAD', '--no-color', '--no-ext-diff', '--src-prefix=a/',
       '--dst-prefix=b/', '--', relative_path], cwd=src)
  if not diff:
    raise ValueError('%s has no changes to capture' % relative_path)

  os.makedirs(config.PATCHES_DIR, exist_ok=True)
  destination = patch_path(relative_path)
  # Newline is pinned to '\n' so that patches are byte-identical regardless of
  # the platform that generated them.
  with open(destination, 'w', encoding='utf-8', newline='\n') as f:
    f.write(diff)
    f.write('\n')
  return destination


def is_applied(src, patch_file):
  """Returns True if the patch is already present in the checkout."""
  applied = proc.run(
      ['git', 'apply', '--reverse', '--check', patch_file],
      cwd=src, check=False, capture=True)
  return applied.returncode == 0


def apply_patch(src, patch_file):
  """Applies one patch to the Chromium checkout.

  Returns 'applied', 'skipped' if it was already present, or raises
  CommandError with git's own diagnostics when it genuinely conflicts.
  """
  if is_applied(src, patch_file):
    return 'skipped'

  result = proc.run(['git', 'apply', '--3way', patch_file],
                    cwd=src, check=False, capture=True)
  if result.returncode != 0:
    detail = (result.stderr or result.stdout or '').strip()
    raise proc.CommandError(
        'failed to apply %s\n%s\nthe three-way merge left conflict markers in '
        '%s; resolve them before building'
        % (os.path.basename(patch_file), detail, target_of(patch_file)))
  return 'applied'


def reset_target(src, relative_path):
  """Restores one upstream file to its pristine state.

  Restores from HEAD rather than the index: `git apply --3way` stages what it
  applies, so a plain `git checkout -- <path>` would restore the patched
  content back over itself and reset nothing.

  This discards local edits to that file, so callers must confirm intent.
  """
  proc.git(['checkout', 'HEAD', '--', relative_path], cwd=src)


def validate_target(src, relative_path):
  """Raises if an upstream path is not a tracked file in the Chromium tree."""
  if posixpath.isabs(relative_path) or '..' in relative_path.split('/'):
    raise ValueError('%r must be a path relative to src/' % relative_path)
  listed = proc.run(['git', 'ls-files', '--error-unmatch', '--', relative_path],
                    cwd=src, check=False, capture=True)
  if listed.returncode != 0:
    raise ValueError('%r is not a tracked file in the Chromium checkout. New '
                     'code belongs under //dandelion, not upstream.'
                     % relative_path)
