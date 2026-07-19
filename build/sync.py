#!/usr/bin/env python3
# Copyright (c) 2026 Christian Relf. All rights reserved.
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Creates or updates the Firefox checkout that Dandelion builds against.

The checkout is pinned to the release in //FIREFOX_VERSION and lives outside
this repository. Dandelion's branding is then mounted into it as
browser/branding/dandelion, so the Firefox build sees it as an ordinary
in-tree brand while it remains version controlled here.

Usage:
  python build/sync.py                # clone or update, mount, patch
  python build/sync.py --no-patch     # leave upstream pristine
  python build/sync.py --bootstrap    # also run mach bootstrap
"""

import argparse
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lib import config
from lib import patching
from lib import proc


def _clone(src, depth):
  """Performs the initial clone when no checkout exists yet."""
  proc.info('no Firefox checkout found; cloning into %s' % src)
  parent = os.path.dirname(src)
  if parent:
    os.makedirs(parent, exist_ok=True)

  # git only draws progress when stderr is a terminal, so a clone whose output
  # is piped to a log looks stalled for the entire run. --progress forces it.
  command = ['git', 'clone', '--progress']
  if depth:
    # A shallow clone is enough to build and to diff patches against HEAD, but
    # rolling to another release later needs a matching --depth fetch.
    command += ['--depth', str(depth), '--branch', config.firefox_tag()]
    proc.warn('shallow clone: rolling to another release will need '
              '`git fetch --unshallow`')
  command += [config.FIREFOX_GIT_URL, src]
  proc.run(command)


def _checkout_version(src, version):
  """Pins the Firefox tree to the tagged release."""
  tag = config.firefox_tag(version)
  proc.info('pinning Firefox to %s (%s)' % (version, tag))

  known = proc.run(['git', 'rev-parse', '--verify', '--quiet', tag + '^{}'],
                   cwd=src, check=False, capture=True)
  if known.returncode != 0:
    proc.git(['fetch', '--tags', 'origin'], cwd=src, capture=False)

  # A named branch at the tag keeps `git status` readable and gives patches a
  # stable base to diff against, unlike a detached HEAD.
  branch = 'dandelion-%s' % version
  existing = proc.run(['git', 'rev-parse', '--verify', '--quiet', branch],
                      cwd=src, check=False, capture=True)
  if existing.returncode == 0:
    proc.git(['checkout', branch], cwd=src, capture=False)
  else:
    proc.git(['checkout', '-b', branch, 'refs/tags/%s' % tag],
             cwd=src, capture=False)


def _mount(src, source_dir, mount_rel):
  """Links one of this repository's directories into the Firefox tree.

  A junction is used on Windows because, unlike a symlink, it needs neither
  administrator rights nor Developer Mode. Mounting rather than copying means
  edits here are immediately live in the tree, with no sync step to forget.
  """
  link = os.path.join(src, *mount_rel.split('/'))
  if os.path.exists(link):
    resolved = os.path.realpath(link)
    if resolved == os.path.realpath(source_dir):
      proc.info('already mounted at %s' % link)
      return
    raise proc.CommandError(
        '%s already exists and points at %s, not this repository. Remove it '
        'and re-run.' % (link, resolved))

  parent = os.path.dirname(link)
  if not os.path.isdir(parent):
    raise proc.CommandError(
        '%s does not exist; the Firefox checkout looks incomplete' % parent)

  if sys.platform == 'win32':
    proc.run(['cmd', '/c', 'mklink', '/J', link, source_dir])
  else:
    os.symlink(source_dir, link, target_is_directory=True)
  proc.info('mounted %s at %s' % (os.path.basename(source_dir), link))


def _protect_mounts(src):
  """Hides Dandelion's mounts from the Firefox repository's git.

  The junction is an untracked directory as far as Firefox's checkout is
  concerned, so it otherwise clutters `git status` and `git clean -fd` deletes
  it. This does not protect against `git clean -fdx`, which removes ignored
  files by definition — but that only unmounts branding, it does not reach the
  files behind the junction: Windows removes the reparse point without
  following it. Re-running build/sync.py remounts, and build.py refuses to
  build when the mount is missing rather than silently producing Firefox
  branding.
  """
  exclude_file = os.path.join(src, '.git', 'info', 'exclude')
  existing = ''
  if os.path.exists(exclude_file):
    with open(exclude_file, encoding='utf-8') as f:
      existing = f.read()
  lines = existing.splitlines()

  missing = ['/%s/' % mount for _, mount in config.mounts()
             if '/%s/' % mount not in lines]
  if not missing:
    return

  os.makedirs(os.path.dirname(exclude_file), exist_ok=True)
  with open(exclude_file, 'a', encoding='utf-8', newline='\n') as f:
    if existing and not existing.endswith('\n'):
      f.write('\n')
    f.write('\n# Dandelion directories are mounted here by build/sync.py.\n'
            '# Excluding them stops `git clean -fdx` from deleting through\n'
            '# the junctions into the Dandelion repository.\n')
    for entry in missing:
      f.write(entry + '\n')
  proc.info('excluded %s from the Firefox checkout' % ', '.join(missing))


def _bootstrap(src):
  """Runs mach bootstrap, which installs Rust and the clang toolchain."""
  proc.info('running mach bootstrap (interactive)')
  proc.run([sys.executable, os.path.join(src, 'mach'), 'bootstrap',
            '--application-choice', 'browser'], cwd=src)


def main():
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument('--no-patch', action='store_true',
                      help='do not apply Dandelion patches after syncing')
  parser.add_argument('--bootstrap', action='store_true',
                      help='also run mach bootstrap to install the toolchain')
  parser.add_argument('--depth', type=int, default=None,
                      help='make a shallow clone of this depth (initial '
                           'clone only)')
  args = parser.parse_args()

  if shutil.which('git') is None:
    raise proc.CommandError('git was not found on PATH')

  src = config.firefox_src()
  version = config.firefox_version()

  if ' ' in src:
    raise proc.CommandError(
        'Firefox cannot build from a path containing spaces: %s' % src)

  if not os.path.isdir(os.path.join(src, '.git')):
    _clone(src, args.depth)

  _checkout_version(src, version)
  for source_dir, mount_rel in config.mounts():
    _mount(src, source_dir, mount_rel)
  _protect_mounts(src)

  if not args.no_patch:
    proc.info('applying Dandelion patches')
    for patch_file in patching.list_patches():
      state = patching.apply_patch(src, patch_file)
      proc.info('  %s %s' % (state, os.path.basename(patch_file)))

  if args.bootstrap:
    _bootstrap(src)

  proc.info('checkout ready at %s' % src)
  return 0


if __name__ == '__main__':
  try:
    sys.exit(main())
  except (proc.CommandError, ValueError) as e:
    proc.error(str(e))
    sys.exit(1)
