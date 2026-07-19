#!/usr/bin/env python3
# Copyright (c) 2026 Christian Relf. All rights reserved.
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Tests for //dandelion/build/lib/patching.py.

These run against a synthetic git repository standing in for the Firefox
checkout, so they need no real tree.

  python build/tests/patching_test.py
"""

import os
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib import config
from lib import patching
from lib import proc

BRAND = 'browser/branding/unofficial/locales/en-US/brand.properties'
UPSTREAM = 'brandShortName=Nightly\nbrandFullName=Nightly\n'
BRANDED = 'brandShortName=Dandelion\nbrandFullName=Dandelion\n'


def _git(args, cwd):
  subprocess.run(['git', '-c', 'user.email=test@dandelion', '-c',
                  'user.name=test'] + args,
                 cwd=cwd, check=True, stdout=subprocess.DEVNULL,
                 stderr=subprocess.DEVNULL)


class PatchingTest(unittest.TestCase):

  def setUp(self):
    temp = tempfile.TemporaryDirectory()
    self.addCleanup(temp.cleanup)

    self.src = os.path.join(temp.name, 'src')
    os.makedirs(os.path.join(self.src, os.path.dirname(BRAND)))
    self._write(BRAND, UPSTREAM)
    _git(['init', '-q'], self.src)
    _git(['add', '-A'], self.src)
    _git(['commit', '-qm', 'upstream'], self.src)

    # Patches must never land in the real repository during a test run.
    original = config.PATCHES_DIR
    config.PATCHES_DIR = os.path.join(temp.name, 'patches')
    os.makedirs(config.PATCHES_DIR)
    self.addCleanup(lambda: setattr(config, 'PATCHES_DIR', original))

  def _write(self, relative_path, contents):
    with open(os.path.join(self.src, relative_path), 'w', encoding='utf-8',
              newline='\n') as f:
      f.write(contents)

  def _read(self, relative_path):
    with open(os.path.join(self.src, relative_path), encoding='utf-8') as f:
      return f.read()

  def _capture(self):
    self._write(BRAND, BRANDED)
    return patching.write_patch(self.src, BRAND)

  def test_patch_filename_flattens_path(self):
    self.assertEqual(
        patching.patch_filename(BRAND),
        'browser-branding-unofficial-locales-en-US-brand.properties.patch')

  def test_target_is_read_from_diff_header_not_filename(self):
    self.assertEqual(patching.target_of(self._capture()), BRAND)

  def test_capture_revert_apply_round_trip(self):
    patch_file = self._capture()
    _git(['checkout', 'HEAD', '--', BRAND], self.src)
    self.assertEqual(self._read(BRAND), UPSTREAM)

    self.assertEqual(patching.apply_patch(self.src, patch_file), 'applied')
    self.assertEqual(self._read(BRAND), BRANDED)

  def test_apply_is_idempotent(self):
    patch_file = self._capture()
    _git(['checkout', 'HEAD', '--', BRAND], self.src)
    patching.apply_patch(self.src, patch_file)
    self.assertEqual(patching.apply_patch(self.src, patch_file), 'skipped')

  def test_modified_files_sees_changes_staged_by_three_way_apply(self):
    # Regression: `git apply --3way` stages what it applies, so comparing the
    # worktree against the index reports a freshly patched tree as clean. That
    # made update_patches capture nothing and marked every patch stale, which
    # --prune would then delete.
    patch_file = self._capture()
    _git(['checkout', 'HEAD', '--', BRAND], self.src)
    patching.apply_patch(self.src, patch_file)

    self.assertEqual(patching.modified_files(self.src), [BRAND])

  def test_write_patch_captures_changes_staged_by_three_way_apply(self):
    patch_file = self._capture()
    _git(['checkout', 'HEAD', '--', BRAND], self.src)
    patching.apply_patch(self.src, patch_file)

    # Must not raise "has no changes to capture".
    patching.write_patch(self.src, BRAND)
    with open(patch_file, encoding='utf-8') as f:
      self.assertIn('brandFullName=Dandelion', f.read())

  def test_reset_target_restores_after_three_way_apply(self):
    # Regression: `git checkout -- <path>` restores from the index, which the
    # three-way apply has already populated, so it would reset nothing.
    patch_file = self._capture()
    _git(['checkout', 'HEAD', '--', BRAND], self.src)
    patching.apply_patch(self.src, patch_file)

    patching.reset_target(self.src, BRAND)
    self.assertEqual(self._read(BRAND), UPSTREAM)

  def test_mounted_branding_is_never_captured(self):
    # branding/ is mounted into the Firefox tree but tracked by this
    # repository, so it must never be captured as a patch against Firefox.
    mounted = os.path.join(config.BRANDING_MOUNT, 'configure.sh')
    os.makedirs(os.path.dirname(os.path.join(self.src, mounted)))
    self._write(mounted, 'MOZ_APP_DISPLAYNAME=Dandelion\n')
    _git(['add', '-A'], self.src)
    _git(['commit', '-qm', 'branding'], self.src)
    self._write(mounted, 'MOZ_APP_DISPLAYNAME=Dandelion Nightly\n')

    self.assertNotIn(mounted.replace('\\', '/'),
                     patching.modified_files(self.src))

  def test_conflicting_roll_raises(self):
    patch_file = self._capture()
    # Upstream rewrites the same lines, then Dandelion tries to reapply.
    _git(['checkout', 'HEAD', '--', BRAND], self.src)
    self._write(BRAND, 'brandShortName=Rewritten\nbrandFullName=Rewritten\n')
    _git(['commit', '-qam', 'firefox roll'], self.src)

    with self.assertRaises(proc.CommandError):
      patching.apply_patch(self.src, patch_file)

  def test_validate_target_rejects_untracked_paths(self):
    with self.assertRaises(ValueError):
      patching.validate_target(self.src, 'browser/does/not/exist.js')

  def test_validate_target_rejects_traversal(self):
    with self.assertRaises(ValueError):
      patching.validate_target(self.src, '../outside.js')


if __name__ == '__main__':
  unittest.main(verbosity=2)
