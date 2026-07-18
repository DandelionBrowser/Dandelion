#!/usr/bin/env python3
# Copyright 2026 Christian Relf. All rights reserved.
# Use of this source code is governed by the license found in the LICENSE file.

"""Tests for //dandelion/build/lib/patching.py.

These run against a synthetic git repository standing in for the Chromium
checkout, so they need neither depot_tools nor a real tree.

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

BRANDING = 'chrome/app/theme/chromium/BRANDING'
UPSTREAM = 'COMPANY_FULLNAME=The Chromium Authors\nPRODUCT_FULLNAME=Chromium\n'
BRANDED = 'COMPANY_FULLNAME=Christian Relf\nPRODUCT_FULLNAME=Dandelion\n'


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
    os.makedirs(os.path.join(self.src, os.path.dirname(BRANDING)))
    self._write(BRANDING, UPSTREAM)
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
    self._write(BRANDING, BRANDED)
    return patching.write_patch(self.src, BRANDING)

  def test_patch_filename_flattens_path(self):
    self.assertEqual(patching.patch_filename(BRANDING),
                     'chrome-app-theme-chromium-BRANDING.patch')

  def test_target_is_read_from_diff_header_not_filename(self):
    self.assertEqual(patching.target_of(self._capture()), BRANDING)

  def test_capture_revert_apply_round_trip(self):
    patch_file = self._capture()
    _git(['checkout', 'HEAD', '--', BRANDING], self.src)
    self.assertEqual(self._read(BRANDING), UPSTREAM)

    self.assertEqual(patching.apply_patch(self.src, patch_file), 'applied')
    self.assertEqual(self._read(BRANDING), BRANDED)

  def test_apply_is_idempotent(self):
    patch_file = self._capture()
    _git(['checkout', 'HEAD', '--', BRANDING], self.src)
    patching.apply_patch(self.src, patch_file)
    self.assertEqual(patching.apply_patch(self.src, patch_file), 'skipped')

  def test_modified_files_sees_changes_staged_by_three_way_apply(self):
    # Regression: `git apply --3way` stages what it applies, so comparing the
    # worktree against the index reports a freshly patched tree as clean. That
    # made update_patches capture nothing and marked every patch stale, which
    # --prune would then delete.
    patch_file = self._capture()
    _git(['checkout', 'HEAD', '--', BRANDING], self.src)
    patching.apply_patch(self.src, patch_file)

    self.assertEqual(patching.modified_files(self.src), [BRANDING])

  def test_write_patch_captures_changes_staged_by_three_way_apply(self):
    patch_file = self._capture()
    _git(['checkout', 'HEAD', '--', BRANDING], self.src)
    patching.apply_patch(self.src, patch_file)

    # Must not raise "has no changes to capture".
    patching.write_patch(self.src, BRANDING)
    with open(patch_file, encoding='utf-8') as f:
      self.assertIn('PRODUCT_FULLNAME=Dandelion', f.read())

  def test_reset_target_restores_after_three_way_apply(self):
    # Regression: `git checkout -- <path>` restores from the index, which the
    # three-way apply has already populated, so it would reset nothing.
    patch_file = self._capture()
    _git(['checkout', 'HEAD', '--', BRANDING], self.src)
    patching.apply_patch(self.src, patch_file)

    patching.reset_target(self.src, BRANDING)
    self.assertEqual(self._read(BRANDING), UPSTREAM)

  def test_overlay_directory_is_never_captured(self):
    overlay_file = os.path.join(config.OVERLAY_DIR_NAME, 'browser', 'a.cc')
    os.makedirs(os.path.dirname(os.path.join(self.src, overlay_file)))
    self._write(overlay_file, 'int a = 0;\n')
    _git(['add', '-A'], self.src)
    _git(['commit', '-qm', 'overlay'], self.src)
    self._write(overlay_file, 'int a = 1;\n')

    self.assertNotIn(overlay_file.replace('\\', '/'),
                     patching.modified_files(self.src))

  def test_conflicting_roll_raises(self):
    patch_file = self._capture()
    # Upstream rewrites the same lines, then Dandelion tries to reapply.
    _git(['checkout', 'HEAD', '--', BRANDING], self.src)
    self._write(BRANDING, 'COMPANY_FULLNAME=Rewritten\nPRODUCT_NAME=Other\n')
    _git(['commit', '-qam', 'chromium roll'], self.src)

    with self.assertRaises(proc.CommandError):
      patching.apply_patch(self.src, patch_file)

  def test_validate_target_rejects_untracked_paths(self):
    with self.assertRaises(ValueError):
      patching.validate_target(self.src, 'chrome/does/not/exist.cc')

  def test_validate_target_rejects_traversal(self):
    with self.assertRaises(ValueError):
      patching.validate_target(self.src, '../outside.cc')


if __name__ == '__main__':
  unittest.main(verbosity=2)
