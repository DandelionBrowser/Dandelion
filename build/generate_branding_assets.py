#!/usr/bin/env python3
# Copyright (c) 2026 Christian Relf. All rights reserved.
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Generates Dandelion's branding raster assets from a single source icon.

Firefox expects around two dozen icons, tiles and installer bitmaps in a brand
directory, at fixed names and sizes. Producing them by hand guarantees they
drift apart; producing them here means branding/icon.png is the only artwork
that has to be maintained, and everything else is reproducible.

Re-run after changing branding/icon.png:

  python build/generate_branding_assets.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lib import config
from lib import proc

try:
  from PIL import Image
except ImportError:
  proc.error('Pillow is required: python -m pip install Pillow')
  sys.exit(1)

SOURCE = os.path.join(config.BRANDING_DIR, 'icon.png')
CONTENT_DIR = os.path.join(config.BRANDING_DIR, 'content')
STUB_DIR = os.path.join(config.BRANDING_DIR, 'stubinstaller')

# Surface colour behind installer bitmaps, matching branding/icon.png.
SURFACE = (20, 20, 23)
# Private browsing surface, matching private_browsing.VisualElementsManifest.
PRIVATE_SURFACE = (37, 0, 62)

# Standalone PNG icons, used by the Linux desktop entry and about: pages.
PNG_SIZES = [16, 22, 24, 32, 48, 64, 128, 256]

# Windows .ico files. Multi-resolution so Explorer picks the right one.
ICO_FILES = {
    'firefox.ico': [16, 32, 48, 64, 128, 256],
    'firefox64.ico': [64],
    'document.ico': [16, 32, 48, 64],
    'document_pdf.ico': [16, 32, 48],
    'newtab.ico': [16, 32, 48],
    'newwindow.ico': [16, 32, 48],
    'pbmode.ico': [16, 32, 48],
}

# Windows Start menu tiles. Transparent: the manifest supplies the colour.
TILES = {
    'VisualElements_70.png': (70, None),
    'VisualElements_150.png': (150, None),
    'PrivateBrowsing_70.png': (70, PRIVATE_SURFACE),
    'PrivateBrowsing_150.png': (150, PRIVATE_SURFACE),
}

# NSIS installer bitmaps. Sizes are fixed by the installer layout, and the
# format must be 24-bit BMP because NSIS cannot read an alpha channel.
BITMAPS = {
    'wizHeader.bmp': (150, 57, 'right'),
    'wizHeaderRTL.bmp': (150, 57, 'left'),
    'wizWatermark.bmp': (164, 314, 'center'),
}

# Artwork for about: pages, referenced by content/jar.mn.
CONTENT_PNGS = {
    'about.png': (192, None),
    'about-logo.png': (192, None),
    'about-logo@2x.png': (384, None),
    'about-logo-private.png': (192, PRIVATE_SURFACE),
    'about-logo-private@2x.png': (384, PRIVATE_SURFACE),
}


# Backdrop for the Windows stub installer pages, required by
# browser/installer/windows/Makefile.in. The size matches Firefox's own asset;
# the installer scales it to the window, and its text is overlaid on top.
STUB_BACKGROUND = (1344, 822)


def _load_source():
  if not os.path.exists(SOURCE):
    raise ValueError('%s is missing; it is the source for every raster asset'
                     % SOURCE)
  image = Image.open(SOURCE).convert('RGBA')
  if image.width != image.height:
    raise ValueError('%s must be square, got %dx%d'
                     % (SOURCE, image.width, image.height))
  return image


def _scaled(source, size):
  return source.resize((size, size), Image.LANCZOS)


def _write(image, path):
  image.save(path)
  return os.path.relpath(path, config.DANDELION_ROOT)


def _tile(source, size, background):
  """Centres the logo on a square canvas, inset to leave the margin a tile
  needs so the artwork does not run to the edge."""
  canvas = Image.new('RGBA', (size, size),
                     background + (255,) if background else (0, 0, 0, 0))
  logo_size = max(1, int(size * 0.6))
  logo = _scaled(source, logo_size)
  offset = (size - logo_size) // 2
  canvas.alpha_composite(logo, (offset, offset))
  return canvas


def _bitmap(source, width, height, align):
  """Renders a 24-bit BMP for the NSIS installer."""
  canvas = Image.new('RGB', (width, height), SURFACE)
  logo_size = max(1, int(min(width, height) * 0.7))
  logo = _scaled(source, logo_size)

  y = (height - logo_size) // 2
  if align == 'left':
    x = int(min(width, height) * 0.15)
  elif align == 'right':
    x = width - logo_size - int(min(width, height) * 0.15)
  else:
    x = (width - logo_size) // 2

  canvas.paste(logo, (x, y), logo)
  return canvas


def _stub_background(source, width, height):
  """Renders the stub installer backdrop as a flat surface with the mark.

  JPEG carries no alpha, so the logo is composited onto the surface colour
  rather than left transparent.
  """
  canvas = Image.new('RGB', (width, height), SURFACE)
  logo_size = int(height * 0.42)
  logo = _scaled(source, logo_size)
  # Sitting low and right keeps the mark clear of the installer's heading and
  # progress bar, which are centred in the upper half.
  canvas.paste(logo, (int(width * 0.62), int(height * 0.46)), logo)
  return canvas


def main():
  source = _load_source()
  os.makedirs(CONTENT_DIR, exist_ok=True)
  os.makedirs(STUB_DIR, exist_ok=True)
  written = []

  for size in PNG_SIZES:
    written.append(_write(_scaled(source, size),
                          os.path.join(config.BRANDING_DIR,
                                       'default%d.png' % size)))

  for name, sizes in ICO_FILES.items():
    path = os.path.join(config.BRANDING_DIR, name)
    # Pillow builds the multi-resolution ICO from the largest requested size.
    _scaled(source, max(sizes)).save(
        path, format='ICO', sizes=[(s, s) for s in sizes])
    written.append(os.path.relpath(path, config.DANDELION_ROOT))

  for name, (size, background) in TILES.items():
    written.append(_write(_tile(source, size, background),
                          os.path.join(config.BRANDING_DIR, name)))

  for name, (width, height, align) in BITMAPS.items():
    written.append(_write(_bitmap(source, width, height, align),
                          os.path.join(config.BRANDING_DIR, name)))

  for name, (size, background) in CONTENT_PNGS.items():
    image = (_tile(source, size, background) if background
             else _scaled(source, size))
    written.append(_write(image, os.path.join(CONTENT_DIR, name)))

  stub = _stub_background(source, *STUB_BACKGROUND)
  stub_path = os.path.join(STUB_DIR, 'bgstub.jpg')
  stub.save(stub_path, format='JPEG', quality=88, optimize=True)
  written.append(os.path.relpath(stub_path, config.DANDELION_ROOT))

  for name in written:
    proc.info('wrote %s' % name)
  proc.info('generated %d assets from %s'
            % (len(written), os.path.relpath(SOURCE, config.DANDELION_ROOT)))
  return 0


if __name__ == '__main__':
  try:
    sys.exit(main())
  except (proc.CommandError, ValueError) as e:
    proc.error(str(e))
    sys.exit(1)
