#!/usr/bin/env python3
# Copyright (c) 2026 Christian Relf. All rights reserved.
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Regenerates patches/ from the current state of the Firefox checkout.

Edit upstream files directly in the Firefox tree, then run this to capture
those edits as patches. Patch files are never written by hand.

A patch whose target file is no longer modified is stale: the change was either
reverted or absorbed upstream. Those are reported, and removed with --prune.

Usage:
  python build/update_patches.py
  python build/update_patches.py --prune
  python build/update_patches.py chrome/browser/ui/views/frame/browser_view.cc
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lib import config
from lib import patching
from lib import proc


def _read(path):
  if not os.path.exists(path):
    return None
  with open(path, encoding='utf-8', newline='') as f:
    return f.read()


def main():
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument('paths', nargs='*',
                      help='specific upstream paths to capture; defaults to '
                           'every modified file in the checkout')
  parser.add_argument('--prune', action='store_true',
                      help='delete patches whose target is no longer modified')
  args = parser.parse_args()

  src = config.firefox_src()
  if not os.path.isdir(os.path.join(src, '.git')):
    raise proc.CommandError(
        'no Firefox checkout at %s; run build/sync.py first' % src)

  if args.paths:
    targets = []
    for path in args.paths:
      normalized = path.replace('\\', '/')
      patching.validate_target(src, normalized)
      targets.append(normalized)
  else:
    targets = patching.modified_files(src)

  if not targets:
    proc.info('no modified upstream files; nothing to capture')
  else:
    for relative_path in targets:
      destination = patching.patch_path(relative_path)
      before = _read(destination)
      patching.write_patch(src, relative_path)
      after = _read(destination)
      if before is None:
        state = 'added  '
      elif before == after:
        state = 'no change'
      else:
        state = 'updated'
      proc.info('%s %s' % (state, os.path.basename(destination)))

  # Stale detection only makes sense for a full sweep: a targeted run says
  # nothing about the patches it was not asked to look at.
  if not args.paths:
    modified = set(patching.modified_files(src))
    stale = [p for p in patching.list_patches()
             if patching.target_of(p) not in modified]
    for patch_file in stale:
      if args.prune:
        os.remove(patch_file)
        proc.info('pruned %s' % os.path.basename(patch_file))
      else:
        proc.warn('%s is stale: %s is no longer modified'
                  % (os.path.basename(patch_file), patching.target_of(patch_file)))
    if stale and not args.prune:
      proc.warn('re-run with --prune to delete the %d stale patch(es) above'
                % len(stale))

  return 0


if __name__ == '__main__':
  try:
    sys.exit(main())
  except (proc.CommandError, ValueError) as e:
    proc.error(str(e))
    sys.exit(1)
