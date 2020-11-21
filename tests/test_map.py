#
# Copyright 2018-2020 Clement
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

import os

import pytest
from flask import request
from PIL import Image

from flaskr.map import create_static_map
from flaskr.map import gpx_to_simplified_geojson


@pytest.mark.parametrize(
    "map_type",
    (
        "viewer",
        "player",
    ),
)
def test_viewers(files, client, app, auth, map_type):
    """
    Test the map viewer (2D) and map player (3D).
    """
    # unknown book ID:
    rv = client.get("/map/" + map_type + "/42/first_story/test_Gillespie_Circuit/nz")
    assert rv.status_code == 404

    # unknown book name:
    rv = client.get("/map/" + map_type + "/1/bad_story/test_Gillespie_Circuit/nz")
    assert rv.status_code == 404

    # restricted book (access level = 1):
    rv = client.get("/map/" + map_type + "/4/fourth_story/test_Gillespie_Circuit/fr")
    assert rv.status_code == 404

    # bad country code:
    rv = client.get("/map/" + map_type + "/1/first_story/test_Unknown/hell")
    assert rv.status_code == 404

    with client:
        # check granted access and raw GPX download link access:
        auth.login()
        rv = client.get(
            "/map/" + map_type + "/4/fourth_story/test_Gillespie_Circuit/fr"
        )
        assert rv.status_code == 200
        assert b'href="/stories/4/test_Gillespie_Circuit.gpx"' not in rv.data
        # actual GPX download tested in test_restricted_access.py
        auth.logout()
        auth.login("root@test.com", "admin")
        rv = client.get(
            "/map/" + map_type + "/4/fourth_story/test_Gillespie_Circuit/fr"
        )
        assert rv.status_code == 200
        assert b'href="/stories/4/test_Gillespie_Circuit.gpx"' in rv.data
        auth.logout()

        # check unrestricted track:
        rv = client.get("/map/" + map_type + "/1/first_story/test_Gillespie_Circuit/nz")
        assert rv.status_code == 200

        # test map.get_thumbnail_path():
        static_map_url = (
            request.url_root.encode() + b"map/static_map/1/test_Gillespie_Circuit.jpg"
        )
        assert (
            b'meta name="twitter:image" property="og:image" content="'
            + static_map_url
            + b'"'
            in rv.data
        )


def test_gpx_to_simplified_geojson(files):
    """
    Test the GPX to GeoJSON conversion.
    """
    with open("test_gpx_to_geojson.expected_output.geojson") as expected_output:
        assert expected_output.read() == gpx_to_simplified_geojson(
            "test_gpx_to_geojson.gpx"
        )


@pytest.mark.parametrize(
    "track_type",
    (
        "geojson",
        "webtrack",
    ),
)
def test_export(files, client, app, auth, track_type):
    """
    Test the WebTrack access.
    """
    # unknown book:
    rv = client.get("/map/" + track_type + "s/42/test_Gillespie_Circuit." + track_type)
    assert rv.status_code == 404

    # restricted book:
    rv = client.get("/map/" + track_type + "s/4/my_track." + track_type)
    assert rv.status_code == 404

    # unknown track:
    rv = client.get("/map/" + track_type + "s/1/test_Unknown." + track_type)
    assert rv.status_code == 404

    # empty GPX file:
    auth.login()
    with pytest.raises(EOFError, match="GPX file is empty"):
        rv = client.get("/map/" + track_type + "s/4/my_track." + track_type)
    auth.logout()

    # all good:
    track_filename = "test_Gillespie_Circuit." + track_type
    rv = client.get("/map/" + track_type + "s/1/" + track_filename)
    assert rv.status_code == 200
    with app.app_context():
        track_path = os.path.join(
            app.config["SHELF_FOLDER"], "first_story", track_filename
        )
        assert os.path.isfile(track_path)
        if track_type == "webtrack":
            webtrack_header = b"webtrack-bin"
            assert open(track_path, "rb").read(len(webtrack_header)) == webtrack_header
        elif track_type == "geojson":
            geojson_header = '{"type":"FeatureCollection","features":['
            assert open(track_path, "r").read(len(geojson_header)) == geojson_header


def test_static_map(files, client, auth):
    """
    Test the static map.
    """
    # unknown book:
    rv = client.get("/map/static_map/42/test_Gillespie_Circuit.jpg")
    assert rv.status_code == 404

    # restricted book:
    rv = client.get("/map/static_map/4/my_track.jpg")
    assert rv.status_code == 404

    # unknown track:
    rv = client.get("/map/static_map/1/test_Unknown.jpg")
    assert rv.status_code == 404

    # empty GPX file:
    auth.login()
    with pytest.raises(EOFError, match="GPX file is empty"):
        rv = client.get("/map/static_map/4/my_track.jpg")
    auth.logout()

    # all good:
    rv = client.get("/map/static_map/1/test_Gillespie_Circuit.jpg")
    assert rv.status_code == 200


def test_create_static_map(app):
    with app.app_context():
        static_image = "Gillespie_Circuit.jpeg"
        create_static_map(
            "Gillespie_Circuit.gpx", static_image, app.config["MAPBOX_STATIC_IMAGES"]
        )
        with Image.open(static_image) as im:
            assert im.format == "JPEG"
            assert im.size == (1600, 1000)
            assert im.mode == "RGB"
        os.remove(static_image)


@pytest.mark.parametrize(
    "path",
    (
        # LDS aerial:
        "/map/middleware/lds/set=2/a/0/0/0",
        # LDS topo:
        "/map/middleware/lds/layer=767/a/0/0/0",
        # IGN aerial:
        "/map/middleware/ign?layer=GEOGRAPHICALGRIDSYSTEMS.MAPS&style=normal&tilematrixset=PM&Service=WMTS&Request"
        "=GetTile&Version=1.0.0&Format=image/jpeg&TileMatrix=11&TileCol=1023&TileRow=753",
        # IGN topo:
        "/map/middleware/ign?layer=ORTHOIMAGERY.ORTHOPHOTOS&style=normal&tilematrixset=PM&Service=WMTS&Request"
        "=GetTile&Version=1.0.0&Format=image%2Fjpeg&TileMatrix=11&TileCol=1026&TileRow=753",
    ),
)
def test_map_proxy_link_ok(client, path):
    """ Check the links availability. """
    rv = client.get(path)
    assert rv.status_code == 200
