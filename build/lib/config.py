# Copyright (c) 2026 Christian Relf. All rights reserved.
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Filesystem layout and version pinning for the Dandelion overlay.

Dandelion does not fork mozilla-firefox/firefox. The Firefox source is checked
out separately and pinned to the release in //FIREFOX_VERSION; this repository
supplies branding, which is mounted into the tree, plus a small set of patches
against upstream files. Every script agrees on those locations here.
"""

import os

# .../dandelion/build/lib/config.py -> .../dandelion
DANDELION_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PATCHES_DIR = os.path.join(DANDELION_ROOT, 'patches')
BRANDING_DIR = os.path.join(DANDELION_ROOT, 'branding')
MOZCONFIG_DIR = os.path.join(DANDELION_ROOT, 'build', 'mozconfig')
FIREFOX_VERSION_FILE = os.path.join(DANDELION_ROOT, 'FIREFOX_VERSION')

# Where branding/ is mounted inside the Firefox tree. Referenced by the
# mozconfigs as --with-branding, so the two must agree.
BRANDING_MOUNT = 'browser/branding/dandelion'

FIREFOX_GIT_URL = 'https://github.com/mozilla-firefox/firefox.git'

# Firefox refuses to build from a path containing spaces, so the checkout
# defaults to a short, plain root rather than living beside this repository.
_DEFAULT_FIREFOX_SRC_WIN = 'C:\\src\\firefox'


def firefox_src():
  """Returns the Firefox source directory."""
  override = os.environ.get('DANDELION_FIREFOX_SRC')
  if override:
    return os.path.abspath(override)
  if os.name == 'nt':
    return _DEFAULT_FIREFOX_SRC_WIN
  return os.path.expanduser('~/firefox')


def firefox_version():
  """Returns the pinned Firefox version, e.g. '152.0.6'."""
  with open(FIREFOX_VERSION_FILE, encoding='utf-8') as f:
    version = f.read().strip()
  if not version:
    raise ValueError('%s is empty' % FIREFOX_VERSION_FILE)
  return version


def firefox_tag(version=None):
  """Returns the git tag for a Firefox version.

  Mozilla tags releases as FIREFOX_<version with dots as underscores>_RELEASE,
  so 152.0.6 becomes FIREFOX_152_0_6_RELEASE.
  """
  return 'FIREFOX_%s_RELEASE' % (version or firefox_version()).replace('.', '_')


def branding_mount_path():
  """Returns where branding/ is mounted inside the Firefox tree."""
  return os.path.join(firefox_src(), *BRANDING_MOUNT.split('/'))


def object_dir(config):
  """Returns the mach object directory for a named configuration.

  Kept outside the source tree so that switching configurations never forces a
  rebuild of the other, and so a wiped objdir cannot take sources with it.
  """
  return os.path.join(firefox_src(), 'obj-dandelion-%s' % config)


def read_branding():
  """Parses branding/configure.sh into a dict of its shell assignments.

  The file is consumed by Firefox's configure as shell, but it is a flat list
  of NAME=value assignments, so it doubles as the single source of product
  identity for this tooling.
  """
  values = {}
  path = os.path.join(BRANDING_DIR, 'configure.sh')
  with open(path, encoding='utf-8') as f:
    for line in f:
      line = line.strip()
      if not line or line.startswith('#'):
        continue
      key, separator, value = line.partition('=')
      if not separator:
        raise ValueError('Malformed line in %s: %r' % (path, line))
      values[key.strip()] = value.strip().strip('"')
  return values
