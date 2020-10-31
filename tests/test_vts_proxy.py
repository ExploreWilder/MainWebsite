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

import pytest

from flaskr import utils
from flaskr import vts_proxy


def test_otm(client):
    """ Check the OpenTopoMap fetch and cache. """
    tile_lost = open("../flaskr/static/images/tile404.png", "rb").read()

    # force to fetch:
    try:
        os.remove(os.path.join(vts_proxy.OTM_CACHE, "0.png"))
    except FileNotFoundError:
        pass
    rv = client.get("/map/vts_proxy/world/topo/otm/1/0/0.png")
    assert rv.status_code == 200
    assert rv.data != tile_lost

    # test cache:
    rv = client.get("/map/vts_proxy/world/topo/otm/1/0/0.png")
    assert rv.status_code == 200
    assert rv.data != tile_lost


@pytest.mark.parametrize(
    "path",
    (
        ("/map/vts_proxy/world/topo/thunderforest/outdoors/1/0/0.png"),
        ("/map/vts_proxy/world/topo/thunderforest/landscape/1/0/0.png"),
        ("/map/vts_proxy/world/topo/thunderforest/cycle/1/0/0.png"),
        ("/map/vts_proxy/world/topo/thunderforest/transport/1/0/0.png"),
        ("/map/vts_proxy/world/topo/thunderforest/transport-dark/1/0/0.png"),
        ("/map/vts_proxy/world/topo/thunderforest/spinal-map/1/0/0.png"),
        ("/map/vts_proxy/world/topo/thunderforest/pioneer/1/0/0.png"),
        ("/map/vts_proxy/world/topo/thunderforest/mobile-atlas/1/0/0.png"),
        ("/map/vts_proxy/world/topo/thunderforest/neighbourhood/1/0/0.png"),
        ("/map/vts_proxy/nz/satellite/1/0/0.png"),
        ("/map/vts_proxy/nz/topo/1/0/0.png"),
        ("/map/vts_proxy/ca/topo/1/0/0.png"),
        ("/map/vts_proxy/fr/satellite/1/0/0.jpg"),
        ("/map/vts_proxy/fr/topo/1/0/0.jpg"),
        ("/map/vts_proxy/world/gebco/shaded/1/0/0.jpeg"),
        ("/map/vts_proxy/world/gebco/flat/1/0/0.jpeg"),
        ("/map/vts_proxy/eumetsat/meteosat_iodc_mpe/1/0/0.png"),
        ("/map/vts_proxy/eumetsat/meteosat_0deg_h0b3/1/0/0.png"),
        ("/map/vts_proxy/world/satellite/bing/3/3/5.jpeg"),
    ),
)
def test_vts_proxy_link_ok(client, path):
    """ Ckeck internal links availability. """
    rv = client.get(path)
    assert rv.status_code == 200


@pytest.mark.parametrize(
    "path",
    (
        ("/map/vts_proxy/world/topo/otm/0/0/0.png"),
        ("/map/vts_proxy/world/topo/thunderforest/pluton/1/0/0.png"),
        ("/map/vts_proxy/nz/pluton/1/0/0.png"),
        ("/map/vts_proxy/fr/pluton/1/0/0.jpg"),
        ("/map/vts_proxy/world/gebco/pluton/1/0/0.jpeg"),
        ("/map/vts_proxy/eumetsat/pluton/1/0/0.png"),
        ("/map/vts_proxy/world/satellite/bing/0/3/5.jpeg"),
    ),
)
def test_vts_proxy_bad_requests(client, path):
    """ Test with bad layers or bad z. """
    tile_ext = utils.file_extension(path)
    tile_lost = open("../flaskr/static/images/tile404." + tile_ext, "rb").read()
    rv = client.get(path)
    assert rv.status_code == 200
    assert rv.data == tile_lost


@pytest.mark.parametrize("path", (("/map/vts_proxy/fr/underground/1/0/0"),))
def test_vts_proxy_bad_link(client, path):
    """ Ckeck the links inavailability. """
    rv = client.get(path)
    assert rv.status_code == 404
