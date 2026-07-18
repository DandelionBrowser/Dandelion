#!/usr/bin/env python3
# Copyright (c) 2026 Christian Relf. All rights reserved.
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Builds and runs Dandelion.

Configuration comes from //build/mozconfig/<config>.mozconfig, selected by
exporting MOZCONFIG for the mach invocation. Each mozconfig names its own
object directory, so configurations never invalidate one another.

Usage:
  python build/build.py                    # dev config
  python build/build.py --config artifact  # frontend-only, minutes not hours
  python build/build.py --run              # build, then launch
  python build/build.py --mach package     # any other mach command
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lib import config
from lib import proc


def _mozconfig_path(name):
  path = os.path.join(config.MOZCONFIG_DIR, '%s.mozconfig' % name)
  if not os.path.exists(path):
    available = sorted(f[:-len('.mozconfig')]
                       for f in os.listdir(config.MOZCONFIG_DIR)
                       if f.endswith('.mozconfig'))
    raise ValueError('unknown config %r; available: %s'
                     % (name, ', '.join(available)))
  return path


def _mach_environment(mozconfig):
  environment = os.environ.copy()
  environment['MOZCONFIG'] = mozconfig
  return environment


def main():
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument('--config', default='dev',
                      help='configuration in build/mozconfig (default: dev)')
  parser.add_argument('--run', action='store_true',
                      help='launch the browser after building')
  parser.add_argument('--mach', nargs=argparse.REMAINDER,
                      help='run an arbitrary mach command instead of build')
  args = parser.parse_args()

  src = config.firefox_src()
  if not os.path.isdir(os.path.join(src, '.git')):
    raise proc.CommandError(
        'no Firefox checkout at %s; run build/sync.py first' % src)

  branding = os.path.join(src, *config.BRANDING_MOUNT.split('/'))
  if not os.path.isdir(branding):
    raise proc.CommandError(
        'branding is not mounted at %s; run build/sync.py' % branding)

  mozconfig = _mozconfig_path(args.config)
  proc.info('using %s' % mozconfig)

  mach = os.path.join(src, 'mach')
  environment = _mach_environment(mozconfig)

  command = args.mach if args.mach else ['build']
  proc.run([sys.executable, mach] + command, cwd=src, env=environment)

  if args.run and not args.mach:
    proc.run([sys.executable, mach, 'run'], cwd=src, env=environment)

  return 0


if __name__ == '__main__':
  try:
    sys.exit(main())
  except (proc.CommandError, ValueError) as e:
    proc.error(str(e))
    sys.exit(1)
