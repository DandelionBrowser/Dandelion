#!/usr/bin/env python3
# Copyright (c) 2026 Christian Relf. All rights reserved.
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Tests for //dandelion/build/sync.py.

These cover the two steps that would otherwise only fail after a multi-hour
checkout: generating a .gclient that gclient can actually parse, and mounting
the overlay into the Chromium tree.

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


class WriteGclientTest(unittest.TestCase):

  def setUp(self):
    temp = tempfile.TemporaryDirectory()
    self.addCleanup(temp.cleanup)
    self.root = temp.name

  def _generate(self, version='150.0.7871.129'):
    sync._write_gclient(self.root, version)
    with open(os.path.join(self.root, '.gclient'), encoding='utf-8') as f:
      return f.read()

  def test_gclient_file_is_valid_python(self):
    # gclient evaluates .gclient as Python; a syntax error here would only
    # surface after the checkout had already started.
    namespace = {}
    exec(self._generate(), namespace)  # pylint: disable=exec-used

    self.assertIn('solutions', namespace)
    self.assertIn('target_os', namespace)
    self.assertEqual(len(namespace['solutions']), 1)

  def test_solution_pins_the_requested_version(self):
    namespace = {}
    exec(self._generate('123.0.1.2'), namespace)  # pylint: disable=exec-used

    solution = namespace['solutions'][0]
    self.assertEqual(solution['name'], 'src')
    self.assertTrue(solution['url'].endswith('@123.0.1.2'), solution['url'])
    self.assertFalse(solution['managed'],
                     'the tag is checked out by sync.py, not by gclient')

  def test_pgo_profiles_are_requested(self):
    # build/args/release.gn sets is_official_build, which cannot build without
    # profile data in the checkout.
    namespace = {}
    exec(self._generate(), namespace)  # pylint: disable=exec-used

    self.assertTrue(
        namespace['solutions'][0]['custom_vars']['checkout_pgo_profiles'])

  def test_target_os_matches_the_host(self):
    expected = {'win32': ['win'], 'darwin': ['mac']}.get(sys.platform,
                                                         ['linux'])
    self.assertEqual(sync._target_os(), expected)


class MountOverlayTest(unittest.TestCase):

  def setUp(self):
    temp = tempfile.TemporaryDirectory()
    self.addCleanup(temp.cleanup)

    self.src = os.path.join(temp.name, 'src')
    self.overlay = os.path.join(temp.name, 'dandelion')
    self.elsewhere = os.path.join(temp.name, 'elsewhere')
    for path in (self.src, self.overlay, self.elsewhere):
      os.makedirs(path)

    with open(os.path.join(self.overlay, 'marker'), 'w',
              encoding='utf-8') as f:
      f.write('dandelion')

    original = config.DANDELION_ROOT
    config.DANDELION_ROOT = self.overlay
    self.addCleanup(lambda: setattr(config, 'DANDELION_ROOT', original))

  def test_mount_creates_a_traversable_link(self):
    sync._mount_overlay(self.src)

    linked = os.path.join(self.src, config.OVERLAY_DIR_NAME)
    self.assertTrue(os.path.isdir(linked))
    # The link must be usable as a path, not merely present: the Chromium build
    # reaches Dandelion's sources through it.
    self.assertTrue(os.path.isfile(os.path.join(linked, 'marker')))

  def test_mount_is_idempotent(self):
    sync._mount_overlay(self.src)
    sync._mount_overlay(self.src)  # Must not raise.

    self.assertTrue(os.path.isfile(
        os.path.join(self.src, config.OVERLAY_DIR_NAME, 'marker')))

  def test_mount_refuses_to_clobber_a_foreign_directory(self):
    # A stale link from another checkout must be reported, never overwritten.
    link = os.path.join(self.src, config.OVERLAY_DIR_NAME)
    os.makedirs(link)

    with self.assertRaises(proc.CommandError):
      sync._mount_overlay(self.src)


if __name__ == '__main__':
  unittest.main(verbosity=2)
