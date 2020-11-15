#
# Copyright 2020 Clement
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its contributors
#    may be used to endorse or promote products derived from this software
#    without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#

"""
Test conversions with an independent/3rd-party library:
mercantile by Mapbox: https://github.com/mapbox/mercantile
"""

import random

import mercantile

from flaskr import tilenames


def test_numTiles():
    """ Check the number of tiles for each zoom level (the entire world is in a single tile at z=0). """
    for z in range(0, 15):
        assert tilenames.numTiles(z) == 2 ** z


def test_xy2latlon():
    """ Test conversion with up to 100 random positions for each zoom level (only one tile (0,0) at z=0). """
    for z in range(0, 15):
        num_tiles = 2 ** z

        def create_samples(n_tiles):
            return random.sample(range(n_tiles), k=min(10, n_tiles))

        samples_x = create_samples(num_tiles)
        samples_y = create_samples(num_tiles)
        for x in samples_x:
            for y in samples_y:
                should_be = mercantile.ul(x, y, z)
                assert tilenames.xy2latlon(x, y, z) == (should_be.lat, should_be.lng)


def test_tileXY():
    """ Test conversion with 100 random positions for each zoom level. """
    for z in range(0, 15):
        samples_lng = random.sample(range(-180, 180), k=10)
        samples_lat = random.sample(range(-85, 85), k=10)
        for lng in samples_lng:
            for lat in samples_lat:
                should_be = mercantile.tile(lng, lat, z, truncate=False)
                assert tilenames.tileXY(lat, lng, z) == (should_be.x, should_be.y)


def test_tileSizePixels():
    """ Check the tile size. """
    assert tilenames.tileSizePixels() == 256
