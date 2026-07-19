#!/usr/bin/env python3
# Copyright (c) 2026 Christian Relf. All rights reserved.
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Tests for //dandelion/build/sync.py.

These cover the steps that would otherwise only fail after a multi-gigabyte
clone: resolving the Firefox release tag, and mounting branding into the tree.

  python build/tests/sync_test.py
"""

import importlib.util
import os
import sys
import tempfile
import unittest

_BUILD_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _BUILD_DIR)

from lib import config
from lib import proc


def _load_sync():
  """Imports sync.py, which is a script rather than an importable module."""
  spec = importlib.util.spec_from_file_location(
      'dandelion_sync', os.path.join(_BUILD_DIR, 'sync.py'))
  module = importlib.util.module_from_spec(spec)
  spec.loader.exec_module(module)
  return module


sync = _load_sync()


class FirefoxTagTest(unittest.TestCase):

  def test_tag_matches_mozilla_release_convention(self):
    # Mozilla tags releases as FIREFOX_<version, dots to underscores>_RELEASE.
    # Getting this wrong fails only after the clone has finished.
    self.assertEqual(config.firefox_tag('152.0.6'), 'FIREFOX_152_0_6_RELEASE')

  def test_tag_handles_a_dotless_major_release(self):
    self.assertEqual(config.firefox_tag('153.0'), 'FIREFOX_153_0_RELEASE')

  def test_pinned_version_resolves_to_a_tag(self):
    self.assertTrue(config.firefox_tag().startswith('FIREFOX_'))
    self.assertTrue(config.firefox_tag().endswith('_RELEASE'))


class BrandingTest(unittest.TestCase):

  def test_mount_path_agrees_with_the_mozconfigs(self):
    # build/mozconfig/dev.mozconfig passes --with-branding, and the two must
    # name the same directory or the build silently uses Firefox branding.
    with open(os.path.join(config.MOZCONFIG_DIR, 'dev.mozconfig'),
              encoding='utf-8') as f:
      self.assertIn('--with-branding=%s' % config.BRANDING_MOUNT, f.read())

  def test_branding_declares_the_dandelion_product_name(self):
    branding = config.read_branding()
    self.assertEqual(branding['MOZ_APP_DISPLAYNAME'], 'Dandelion')


class MountTest(unittest.TestCase):

  def setUp(self):
    temp = tempfile.TemporaryDirectory()
    self.addCleanup(temp.cleanup)

    self.src = os.path.join(temp.name, 'src')
    self.branding = os.path.join(temp.name, 'branding')
    # The parent of the mount point exists in a real Firefox checkout.
    os.makedirs(os.path.join(self.src,
                             os.path.dirname(config.BRANDING_MOUNT)))
    os.makedirs(self.branding)
    with open(os.path.join(self.branding, 'configure.sh'), 'w',
              encoding='utf-8') as f:
      f.write('MOZ_APP_DISPLAYNAME=Dandelion\n')

    original = config.BRANDING_DIR
    config.BRANDING_DIR = self.branding
    self.addCleanup(lambda: setattr(config, 'BRANDING_DIR', original))

  def _mounted(self):
    return os.path.join(self.src, *config.BRANDING_MOUNT.split('/'))

  def test_mount_creates_a_traversable_link(self):
    sync._mount(self.src, self.branding, config.BRANDING_MOUNT)

    # The link must be usable as a path, not merely present: the Firefox build
    # reads branding through it.
    self.assertTrue(os.path.isfile(
        os.path.join(self._mounted(), 'configure.sh')))

  def test_mount_is_idempotent(self):
    sync._mount(self.src, self.branding, config.BRANDING_MOUNT)
    sync._mount(self.src, self.branding, config.BRANDING_MOUNT)  # Must not raise.

    self.assertTrue(os.path.isfile(
        os.path.join(self._mounted(), 'configure.sh')))

  def test_mount_refuses_to_clobber_a_foreign_directory(self):
    os.makedirs(self._mounted())

    with self.assertRaises(proc.CommandError):
      sync._mount(self.src, self.branding, config.BRANDING_MOUNT)

  def test_exclude_is_written_once(self):
    exclude = os.path.join(self.src, '.git', 'info', 'exclude')
    os.makedirs(os.path.dirname(exclude))
    with open(exclude, 'w', encoding='utf-8') as f:
      f.write('# pre-existing\n')

    sync._protect_mounts(self.src)
    sync._protect_mounts(self.src)  # Must not duplicate.

    with open(exclude, encoding='utf-8') as f:
      contents = f.read()
    entry = '/%s/' % config.BRANDING_MOUNT
    self.assertEqual(contents.count(entry), 1)
    self.assertIn('# pre-existing', contents)

  def test_exclude_is_created_when_absent(self):
    sync._protect_mounts(self.src)

    exclude = os.path.join(self.src, '.git', 'info', 'exclude')
    with open(exclude, encoding='utf-8') as f:
      self.assertIn('/%s/' % config.BRANDING_MOUNT, f.read())

  def test_mount_reports_an_incomplete_checkout(self):
    empty = os.path.join(os.path.dirname(self.src), 'empty-src')
    os.makedirs(empty)

    with self.assertRaises(proc.CommandError):
      sync._mount(empty, self.branding, config.BRANDING_MOUNT)


if __name__ == '__main__':
  unittest.main(verbosity=2)
