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

Some of those slots are different entry points into the browser rather than
different sizes of the same one -- a new tab, a new window, a private window --
and Windows shows them side by side in the jump list. They are therefore
generated through a *variant*: a recolour of the mark, optionally carrying a
small badge, declared once in VARIANTS and named by each output. Adding a mark
for a new surface means adding a variant, not new artwork.

Re-run after changing branding/icon.png:

  python build/generate_branding_assets.py
"""

import collections
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lib import config
from lib import proc

try:
  from PIL import Image, ImageDraw
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

# The two colours branding/icon.png is drawn in. The mark is strictly two-tone:
# every pixel is a blend of these, which is what makes recolouring it exact.
# The accent is --dandelion-accent from ui/content/tokens.css, restated because
# this script cannot read CSS; keep the two in step.
SOURCE_SURFACE = (20, 20, 20)
SOURCE_ACCENT = (245, 196, 81)

# A variant of the mark: the palette to recolour it onto, and an optional badge
# stamped in the lower-right corner. Both may be omitted to get the mark as
# drawn.
Variant = collections.namedtuple('Variant', ['surface', 'accent', 'badge'])

VARIANTS = {
    'default': Variant(SOURCE_SURFACE, SOURCE_ACCENT, None),
    # Private browsing is signalled by the surface alone. The seedhead keeps
    # the accent, so the mark still reads as Dandelion rather than as a
    # separate product.
    'private': Variant(PRIVATE_SURFACE, SOURCE_ACCENT, None),
    # New tab and new window sit next to each other in the Windows jump list,
    # where a recolour alone is too weak to tell them apart. They are badged
    # instead, and keep the default palette so the jump list stays coherent.
    'newtab': Variant(SOURCE_SURFACE, SOURCE_ACCENT, 'plus'),
    'newwindow': Variant(SOURCE_SURFACE, SOURCE_ACCENT, 'window'),
}

# Standalone PNG icons, used by the Linux desktop entry and about: pages.
PNG_SIZES = [16, 22, 24, 32, 48, 64, 128, 256]

# Windows .ico files, as (sizes, variant). Multi-resolution so Explorer picks
# the right one. The last three are jump list tasks rather than the app itself,
# so each takes its own variant.
ICO_FILES = {
    'firefox.ico': ([16, 32, 48, 64, 128, 256], 'default'),
    'firefox64.ico': ([64], 'default'),
    'document.ico': ([16, 32, 48, 64], 'default'),
    'document_pdf.ico': ([16, 32, 48], 'default'),
    'newtab.ico': ([16, 32, 48], 'newtab'),
    'newwindow.ico': ([16, 32, 48], 'newwindow'),
    'pbmode.ico': ([16, 32, 48], 'private'),
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


def _recoloured(source, variant):
  """Maps the two-tone source mark onto a variant's palette.

  Every pixel of branding/icon.png lies on the segment between SOURCE_SURFACE
  and SOURCE_ACCENT, so the blend factor can be recovered from the red channel
  alone -- it has by far the widest range of the three, which keeps the
  antialiased edges accurate. Each output channel is then a 256-entry lookup
  that Pillow applies in C, rather than a Python loop over a megapixel.

  Fully transparent pixels carry no colour, so they map to the surface end.
  That is deliberate rather than incidental: Pillow downscales
  non-premultiplied RGBA, so it blends the colour of transparent pixels into
  the edges around them, and leaving them black would ring a recoloured mark
  with a dark fringe.
  """
  if (variant.surface, variant.accent) == (SOURCE_SURFACE, SOURCE_ACCENT):
    return source

  low = SOURCE_SURFACE[0]
  span = SOURCE_ACCENT[0] - low
  red = source.getchannel('R')
  channels = []
  for i in range(3):
    start, end = variant.surface[i], variant.accent[i]
    channels.append(red.point(
        [round(start + (end - start) * min(max((v - low) / span, 0.0), 1.0))
         for v in range(256)]))
  channels.append(source.getchannel('A'))
  return Image.merge('RGBA', channels)


# Badge geometry, as a fraction of the icon edge. The badge has to survive being
# scaled to 16px, so it is large and sits clear of the seedhead. Its outer edge
# stays inside the mark's rounded corner, so the silhouette is unchanged.
BADGE_CENTRE = 0.70
BADGE_RADIUS = 0.20
# Ring of surface colour separating the badge from the artwork behind it.
BADGE_RING = 0.045


def _badged(image, variant):
  """Stamps a variant's badge into the lower-right corner of the mark.

  Icons that share the seedhead are otherwise indistinguishable in the jump
  list, where they appear together. Badges are drawn at full resolution and
  scaled down with everything else, so they antialias rather than alias.
  """
  size = image.width
  centre = BADGE_CENTRE * size
  radius = BADGE_RADIUS * size
  accent = variant.accent + (255,)
  surface = variant.surface + (255,)

  badged = image.copy()
  draw = ImageDraw.Draw(badged)

  def disc(r, fill):
    draw.ellipse([centre - r, centre - r, centre + r, centre + r], fill=fill)

  disc(radius + BADGE_RING * size, surface)
  disc(radius, accent)

  if variant.badge == 'plus':
    arm = radius * 0.58
    bar = radius * 0.20
    draw.rectangle([centre - arm, centre - bar, centre + arm, centre + bar],
                   fill=surface)
    draw.rectangle([centre - bar, centre - arm, centre + bar, centre + arm],
                   fill=surface)
  elif variant.badge == 'window':
    # Two offset frames, the conventional "new window" glyph. The front frame
    # is filled with the badge colour before being outlined, so it occludes the
    # back one and the pair reads as stacked rather than as a grid.
    half = radius * 0.42
    offset = radius * 0.17
    stroke = max(1, round(radius * 0.14))
    for dx, dy, fill in ((offset, -offset, None), (-offset, offset, accent)):
      x, y = centre + dx, centre + dy
      draw.rectangle([x - half, y - half, x + half, y + half],
                     fill=fill, outline=surface, width=stroke)
  else:
    raise ValueError('unknown badge %r' % variant.badge)

  return badged


def _master(source, name, cache):
  """Returns the full-resolution mark for a named variant, built once."""
  if name not in cache:
    try:
      variant = VARIANTS[name]
    except KeyError:
      raise ValueError('unknown variant %r' % name)
    image = _recoloured(source, variant)
    if variant.badge:
      image = _badged(image, variant)
    cache[name] = image
  return cache[name]


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
  masters = {}

  for size in PNG_SIZES:
    written.append(_write(_scaled(source, size),
                          os.path.join(config.BRANDING_DIR,
                                       'default%d.png' % size)))

  for name, (sizes, variant) in ICO_FILES.items():
    path = os.path.join(config.BRANDING_DIR, name)
    # Pillow builds the multi-resolution ICO from the largest requested size.
    _scaled(_master(source, variant, masters), max(sizes)).save(
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
