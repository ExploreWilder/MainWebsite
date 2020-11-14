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
Tilename utils.

.. note::
    Based on: https://wiki.openstreetmap.org/wiki/Slippy_map_tilenames

    * Author: Oliver White, 2007
    * License: Public Domain

    I've added static types, documentation and unit tests.
"""

# pylint: disable=invalid-name; allow one letter variables (f.i. x, y, z)

import math as mod_math

from .typing import *


def numTiles(z: int) -> float:
    """ Returns the number of tiles at zoom level `z`. Only 1 at z=0. """
    return mod_math.pow(2, z)


def sec(x: float) -> float:
    """ Returns the secant of `x`. """
    return 1 / mod_math.cos(x)


def latlon2relativeXY(lat: float, lon: float) -> Tuple[float, float]:
    x = (lon + 180) / 360
    y = (
        1
        - mod_math.log(mod_math.tan(mod_math.radians(lat)) + sec(mod_math.radians(lat)))
        / mod_math.pi
    ) / 2
    return (x, y)


def latlon2xy(lat: float, lon: float, z: int) -> Tuple[float, float]:
    """
    Convert the (lat, lon, z) coordinates to the XY coords.

    Args:
        lat (float): Latitude [-85.05113, 85.05113].
        lon (float): Longitude [-180, 180].
        z (int): Zoom level (0 for the entire world)

    Returns:
        Tuple[int, int]: X, Y.
    """
    n = numTiles(z)
    x, y = latlon2relativeXY(lat, lon)
    return n * x, n * y


def tileXY(lat: float, lon: float, z: int) -> Tuple[int, int]:
    """ Same as latlon2xy() with a cast to int. """
    x, y = latlon2xy(lat, lon, z)
    return int(x), int(y)


def xy2latlon(x: int, y: int, z: int) -> Tuple[float, float]:
    """
    Convert the XYZ coordinates to the GPS coords.

    Args:
        x (int): X coordinate (between 0 and 2^z-1)
        y (int): Y coordinate (between 0 and 2^z-1)
        z (int): Zoom level (0 for the entire world)

    Returns:
        Tuple[float, float]: Latitude, longitude.
    """
    n = numTiles(z)
    relY = y / n
    lat = mercatorToLat(mod_math.pi * (1 - 2 * relY))
    lon = -180.0 + 360.0 * x / n
    return lat, lon


def latEdges(y: int, z: int) -> Tuple[float, float]:
    n = numTiles(z)
    unit = 1 / n
    relY1 = y * unit
    relY2 = relY1 + unit
    lat1 = mercatorToLat(mod_math.pi * (1 - 2 * relY1))
    lat2 = mercatorToLat(mod_math.pi * (1 - 2 * relY2))
    return lat1, lat2


def lonEdges(x: int, z: int) -> Tuple[float, float]:
    n = numTiles(z)
    unit = 360 / n
    lon1 = -180 + x * unit
    lon2 = lon1 + unit
    return lon1, lon2


def tileLatLonEdges(x: int, y: int, z: int) -> Tuple[float, float, float, float]:
    """
    Returns the bounding box (aka BBOX) according to the XYZ coords.

    Args:
        x (int): X coordinate (between 0 and 2^z-1)
        y (int): Y coordinate (between 0 and 2^z-1)
        z (int): Zoom level (0 for the entire world)

    Returns:
        Tuple[float,float,float,float]:
            * South latitude,
            * West longitude,
            * North latidude,
            * East longitude
    """
    lat1, lat2 = latEdges(y, z)
    lon1, lon2 = lonEdges(x, z)
    return lat2, lon1, lat1, lon2


def mercatorToLat(mercatorY: float) -> float:
    return mod_math.degrees(mod_math.atan(mod_math.sinh(mercatorY)))


def tileSizePixels() -> int:
    """ Tile height and width in pixels. """
    return 256
