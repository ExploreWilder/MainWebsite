"""
Tilename utils.
Extract from: https://wiki.openstreetmap.org/wiki/Slippy_map_tilenames
Author: Oliver White, 2007
License: Public Domain
"""

# pylint: disable=invalid-name; allow one letter variables (f.i. x, y, z)

import math as mod_math


def numTiles(z):
    return mod_math.pow(2, z)


def sec(x):
    return 1 / mod_math.cos(x)


def latlon2relativeXY(lat, lon):
    x = (lon + 180) / 360
    y = (
        1
        - mod_math.log(mod_math.tan(mod_math.radians(lat)) + sec(mod_math.radians(lat)))
        / mod_math.pi
    ) / 2
    return (x, y)


def latlon2xy(lat, lon, z):
    n = numTiles(z)
    x, y = latlon2relativeXY(lat, lon)
    return (n * x, n * y)


def tileXY(lat, lon, z):
    x, y = latlon2xy(lat, lon, z)
    return (int(x), int(y))


def xy2latlon(x, y, z):
    n = numTiles(z)
    relY = y / n
    lat = mercatorToLat(mod_math.pi * (1 - 2 * relY))
    lon = -180.0 + 360.0 * x / n
    return (lat, lon)


def latEdges(y, z):
    n = numTiles(z)
    unit = 1 / n
    relY1 = y * unit
    relY2 = relY1 + unit
    lat1 = mercatorToLat(mod_math.pi * (1 - 2 * relY1))
    lat2 = mercatorToLat(mod_math.pi * (1 - 2 * relY2))
    return (lat1, lat2)


def lonEdges(x, z):
    n = numTiles(z)
    unit = 360 / n
    lon1 = -180 + x * unit
    lon2 = lon1 + unit
    return (lon1, lon2)


def tileLatLonEdges(x, y, z):
    lat1, lat2 = latEdges(y, z)
    lon1, lon2 = lonEdges(x, z)
    return (lat2, lon1, lat1, lon2)  # S,W,N,E


def mercatorToLat(mercatorY):
    return mod_math.degrees(mod_math.atan(mod_math.sinh(mercatorY)))


def tileSizePixels():
    return 256
