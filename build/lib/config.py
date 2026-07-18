# Copyright 2026 Christian Relf. All rights reserved.
# Use of this source code is governed by the license found in the LICENSE file.

"""Filesystem layout and version pinning for the Dandelion overlay.

Dandelion does not fork chromium/src. This repository is checked out *into* a
Chromium tree as src/dandelion, so every script needs to agree on where that
tree lives and which Chromium revision it is pinned to. Both answers come from
here and nowhere else.
"""

import os

# .../dandelion/build/lib/config.py -> .../dandelion
DANDELION_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PATCHES_DIR = os.path.join(DANDELION_ROOT, 'patches')
ARGS_DIR = os.path.join(DANDELION_ROOT, 'build', 'args')
BRANDING_FILE = os.path.join(DANDELION_ROOT, 'app', 'BRANDING')
CHROMIUM_VERSION_FILE = os.path.join(DANDELION_ROOT, 'CHROMIUM_VERSION')

# The name of the junction created inside the Chromium tree that points back at
# this repository. Upstream never writes here, which is what keeps rolls cheap.
OVERLAY_DIR_NAME = 'dandelion'

CHROMIUM_GIT_URL = 'https://chromium.googlesource.com/chromium/src.git'

# Windows has a 260-character path limit that several tools in the Chromium
# build still hit even when LongPathsEnabled is set, so the checkout defaults to
# a short root rather than living next to this repository.
_DEFAULT_CHROMIUM_ROOT_WIN = 'C:\\src\\chromium'


def chromium_root():
  """Returns the directory that contains the .gclient file and src/."""
  override = os.environ.get('DANDELION_CHROMIUM_ROOT')
  if override:
    return os.path.abspath(override)
  if os.name == 'nt':
    return _DEFAULT_CHROMIUM_ROOT_WIN
  return os.path.expanduser('~/chromium')


def chromium_src():
  """Returns the Chromium source directory (the `src` checkout itself)."""
  return os.path.join(chromium_root(), 'src')


def overlay_path():
  """Returns where this repository is mounted inside the Chromium tree."""
  return os.path.join(chromium_src(), OVERLAY_DIR_NAME)


def chromium_version():
  """Returns the pinned Chromium version, e.g. '150.0.7871.129'.

  Chromium tags releases with the bare version string, so this doubles as the
  git ref to check out.
  """
  with open(CHROMIUM_VERSION_FILE, encoding='utf-8') as f:
    version = f.read().strip()
  if not version:
    raise ValueError('%s is empty' % CHROMIUM_VERSION_FILE)
  return version


def out_dir(config):
  """Returns the ninja build directory for a named configuration."""
  return os.path.join(chromium_src(), 'out', config)


def read_branding():
  """Parses app/BRANDING into a dict, ignoring comments and blank lines."""
  values = {}
  with open(BRANDING_FILE, encoding='utf-8') as f:
    for line in f:
      line = line.strip()
      if not line or line.startswith('#'):
        continue
      key, separator, value = line.partition('=')
      if not separator:
        raise ValueError('Malformed line in %s: %r' % (BRANDING_FILE, line))
      values[key.strip()] = value.strip()
  return values
