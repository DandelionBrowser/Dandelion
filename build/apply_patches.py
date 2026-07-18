#!/usr/bin/env python3
# Copyright 2026 Christian Relf. All rights reserved.
# Use of this source code is governed by the license found in the LICENSE file.

"""Applies Dandelion's patches to the Chromium checkout.

Patches already present are skipped, so this is safe to re-run. Conflicts are
reported per-file rather than aborting on the first failure, because after a
Chromium roll it is far more useful to see the whole list at once.

Usage:
  python build/apply_patches.py
  python build/apply_patches.py --reset   # discard upstream edits first
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lib import config
from lib import patching
from lib import proc


def main():
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument(
      '--reset', action='store_true',
      help='restore each patched file to pristine upstream state first, '
           'discarding any local edits to it')
  args = parser.parse_args()

  src = config.chromium_src()
  if not os.path.isdir(os.path.join(src, '.git')):
    raise proc.CommandError(
        'no Chromium checkout at %s; run build/sync.py first' % src)

  patches = patching.list_patches()
  if not patches:
    proc.info('no patches to apply')
    return 0

  failures = []
  counts = {'applied': 0, 'skipped': 0}
  for patch_file in patches:
    name = os.path.basename(patch_file)
    try:
      if args.reset:
        patching.reset_target(src, patching.target_of(patch_file))
      state = patching.apply_patch(src, patch_file)
      counts[state] += 1
      proc.info('%s %s' % (state, name))
    except (proc.CommandError, ValueError) as e:
      failures.append((name, str(e)))
      proc.error(str(e))

  if failures:
    proc.error('%d of %d patches failed' % (len(failures), len(patches)))
    proc.warn('after a Chromium roll, rebase each failing patch by hand, then '
              'run build/update_patches.py to regenerate it')
    return 1

  proc.info('%d applied, %d already present' % (counts['applied'],
                                                counts['skipped']))
  return 0


if __name__ == '__main__':
  try:
    sys.exit(main())
  except (proc.CommandError, ValueError) as e:
    proc.error(str(e))
    sys.exit(1)
