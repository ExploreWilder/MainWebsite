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

import os
from filecmp import cmp

from flaskr.map import good_webtrack_version
from flaskr.map import gpx_to_webtrack_with_elevation


def test_gpx_to_webtrack(app):
    """ Provide a GPX file and compare the generated WebTrack with the expected data. """
    with app.app_context():
        gpx_file = "Gillespie_Circuit_2.gpx"
        generated_webtrack_file = "tmp_Gillespie_Circuit.webtrack"
        expected_webtrack_file = "Gillespie_Circuit.webtrack"
        try:
            gpx_to_webtrack_with_elevation(
                gpx_file, generated_webtrack_file, app.config["NASA_EARTHDATA"]
            )
        except Exception as err:
            raise Exception("Failed to create WebTrack") from err
        assert not cmp(generated_webtrack_file, expected_webtrack_file)
        gpx_file = "Gillespie_Circuit.gpx"
        try:
            gpx_to_webtrack_with_elevation(
                gpx_file, generated_webtrack_file, app.config["NASA_EARTHDATA"]
            )
        except Exception as err:
            raise Exception("Failed to create WebTrack") from err
        assert cmp(generated_webtrack_file, expected_webtrack_file)
        os.remove(generated_webtrack_file)


def test_good_webtrack_version():
    """ Check the read capability. """
    expected_webtrack_file = "Gillespie_Circuit.webtrack"
    assert good_webtrack_version(expected_webtrack_file)
