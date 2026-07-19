#!/usr/bin/env python3
# Copyright (c) 2026 Christian Relf. All rights reserved.
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Tests for //dandelion/build/generate_branding_assets.py.

These run against a synthetic two-tone mark rather than branding/icon.png, so
they test the variant system rather than the artwork of the day.

The invariant worth protecting is that the jump list icons stay *different*.
They are generated from one source, so a mistake there fails silently: the
assets regenerate, the build succeeds, and Windows shows three identical
entries.

  python build/tests/branding_test.py
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
  from PIL import Image
except ImportError:
  Image = None

# generate_branding_assets exits at import time when Pillow is missing, so it
# can only be imported once that has been ruled out.
if Image is not None:
  import generate_branding_assets as branding

SIZE = 256
TRANSPARENT = (0, 0, 0, 0)


def _synthetic_source():
  """A square two-tone mark with transparent corners, like branding/icon.png.

  Row 0 is surface, row 1 accent, row 2 an even blend of the two; the corners
  are transparent so that silhouette changes are detectable.
  """
  image = Image.new('RGBA', (SIZE, SIZE), branding.SOURCE_SURFACE + (255,))
  pixels = image.load()
  blend = tuple(round((a + b) / 2)
                for a, b in zip(branding.SOURCE_SURFACE,
                                branding.SOURCE_ACCENT))
  for x in range(SIZE):
    pixels[x, 0] = branding.SOURCE_SURFACE + (255,)
    pixels[x, 1] = branding.SOURCE_ACCENT + (255,)
    pixels[x, 2] = blend + (255,)
  for x, y in ((0, 0), (SIZE - 1, 0), (0, SIZE - 1), (SIZE - 1, SIZE - 1)):
    pixels[x, y] = TRANSPARENT
  return image


@unittest.skipIf(Image is None, 'Pillow is not installed')
class VariantTest(unittest.TestCase):

  def setUp(self):
    self.source = _synthetic_source()

  def _master(self, name):
    return branding._master(self.source, name, {})

  def test_every_ico_names_a_declared_variant(self):
    for name, (_, variant) in branding.ICO_FILES.items():
      self.assertIn(variant, branding.VARIANTS,
                    '%s names an undeclared variant %r' % (name, variant))

  def test_unknown_variant_is_rejected(self):
    with self.assertRaises(ValueError):
      branding._master(self.source, 'no-such-variant', {})

  def test_default_variant_leaves_the_mark_untouched(self):
    self.assertEqual(self._master('default').tobytes(), self.source.tobytes())

  def test_recolour_maps_both_ends_of_the_blend(self):
    variant = branding.VARIANTS['private']
    pixels = branding._recoloured(self.source, variant).load()
    # Column 1, because column 0 holds a transparent corner.
    self.assertEqual(pixels[1, 0], variant.surface + (255,))
    self.assertEqual(pixels[1, 1], variant.accent + (255,))
    midpoint = tuple(round((a + b) / 2)
                     for a, b in zip(variant.surface, variant.accent))
    # Antialiased edges are blends, so they have to land between the two ends
    # rather than snapping to either. One count of rounding slack.
    for channel, want in enumerate(midpoint):
      self.assertAlmostEqual(pixels[1, 2][channel], want, delta=1)

  def test_recolour_preserves_alpha_and_tints_behind_it(self):
    variant = branding.VARIANTS['private']
    pixels = branding._recoloured(self.source, variant).load()
    self.assertEqual(pixels[1, 0][3], 255)
    corner = pixels[SIZE - 1, SIZE - 1]
    self.assertEqual(corner[3], 0)
    # Transparent pixels take the surface colour rather than staying black.
    # Pillow downscales non-premultiplied RGBA, so it blends the colour of
    # fully transparent pixels into the edges around them; matching the
    # surface is what keeps a recoloured mark from picking up a dark fringe.
    self.assertEqual(corner[:3], variant.surface)

  def test_badge_stays_inside_the_silhouette(self):
    # A badge drawn past the mark's rounded corner would square off its
    # outline, which is only visible once the icon ships.
    for name in ('newtab', 'newwindow'):
      pixels = self._master(name).load()
      for x, y in ((0, 0), (SIZE - 1, 0), (0, SIZE - 1), (SIZE - 1, SIZE - 1)):
        self.assertEqual(pixels[x, y], TRANSPARENT,
                         '%s badge broke the silhouette at %d,%d'
                         % (name, x, y))

  def test_badge_changes_the_mark(self):
    for name in ('newtab', 'newwindow'):
      self.assertNotEqual(self._master(name).tobytes(),
                          self.source.tobytes(),
                          '%s is indistinguishable from the plain mark' % name)

  def test_jump_list_marks_are_all_different(self):
    variants = [variant for name, (_, variant) in branding.ICO_FILES.items()
                if name in ('newtab.ico', 'newwindow.ico', 'pbmode.ico')]
    self.assertEqual(len(variants), 3)
    rendered = {}
    for variant in variants:
      data = self._master(variant).tobytes()
      self.assertNotIn(data, rendered,
                       '%s renders identically to %s'
                       % (variant, rendered.get(data)))
      rendered[data] = variant


if __name__ == '__main__':
  unittest.main()
