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

import pytest, os
from urllib.parse import urlparse
import gpxpy

from flaskr.gpx_to_img import gpx_to_src


def test_gpx_to_src(app):
    """ Test of the GPX to the Mapbox API URL conversion. """
    gpx_path = "Gillespie_Circuit.gpx"
    with open(gpx_path, "r") as gpx_file:
        gpx = gpxpy.parse(gpx_file)
    with app.app_context():
        url = gpx_to_src(gpx, app.config["MAPBOX_STATIC_IMAGES"])
        parsed_url = urlparse(url)
        assert len(url) < 8192  # avoid too long URL
        assert parsed_url.scheme == "https"
        assert parsed_url.netloc == "api.mapbox.com"
        args = parsed_url.query.split("&")
        has_access_token = False
        has_logo_set = False
        for arg in args:
            key, value = arg.split("=")
            if key == "access_token":
                has_access_token = True
                assert value == app.config["MAPBOX_STATIC_IMAGES"]["access_token"]
            elif key == "logo":
                has_logo_set = True
                assert (
                    value == "true"
                    if app.config["MAPBOX_STATIC_IMAGES"]["logo"]
                    else "false"
                )
        assert has_access_token
        assert has_logo_set
