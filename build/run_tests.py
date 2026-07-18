#!/usr/bin/env python3
# Copyright (c) 2026 Christian Relf. All rights reserved.
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Runs every Dandelion build-tooling test.

The test files are standalone scripts rather than a package, because they add
//dandelion/build to sys.path themselves so that they can be run individually.
That makes them invisible to `unittest discover`, so they are loaded by path
here instead.

  python build/run_tests.py
"""

import importlib.util
import os
import sys
import unittest

TESTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tests')


def _load(path):
  name = 'dandelion_test_%s' % os.path.basename(path)[:-3]
  spec = importlib.util.spec_from_file_location(name, path)
  module = importlib.util.module_from_spec(spec)
  # Registering the module lets unittest resolve test names back to it.
  sys.modules[name] = module
  spec.loader.exec_module(module)
  return module


def main():
  loader = unittest.TestLoader()
  suite = unittest.TestSuite()
  names = sorted(n for n in os.listdir(TESTS_DIR) if n.endswith('_test.py'))
  if not names:
    print('no tests found in %s' % TESTS_DIR, file=sys.stderr)
    return 1

  for name in names:
    suite.addTests(loader.loadTestsFromModule(
        _load(os.path.join(TESTS_DIR, name))))

  result = unittest.TextTestRunner(verbosity=2).run(suite)
  return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
  sys.exit(main())
