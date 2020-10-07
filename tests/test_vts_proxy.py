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

import pytest

@pytest.mark.parametrize("path", (
    ("/map/vts_proxy/world/topo/otm/0/0/0.png"),
    ("/map/vts_proxy/world/topo/thunderforest/outdoors/0/0/0.png"),
    ("/map/vts_proxy/world/topo/thunderforest/landscape/0/0/0.png"),
    ("/map/vts_proxy/world/topo/thunderforest/cycle/0/0/0.png"),
    ("/map/vts_proxy/world/topo/thunderforest/transport/0/0/0.png"),
    ("/map/vts_proxy/world/topo/thunderforest/transport-dark/0/0/0.png"),
    ("/map/vts_proxy/world/topo/thunderforest/spinal-map/0/0/0.png"),
    ("/map/vts_proxy/world/topo/thunderforest/pioneer/0/0/0.png"),
    ("/map/vts_proxy/world/topo/thunderforest/mobile-atlas/0/0/0.png"),
    ("/map/vts_proxy/world/topo/thunderforest/neighbourhood/0/0/0.png"),
    ("/map/vts_proxy/nz/satellite/0/0/0.png"),
    ("/map/vts_proxy/nz/topo/0/0/0.png"),
    ("/map/vts_proxy/ca/topo/0/0/0.png"),
    ("/map/vts_proxy/fr/satellite/0/0/0.jpg"),
    ("/map/vts_proxy/fr/topo/0/0/0.jpg")
))
def test_vts_proxy_link_ok(client, path):
    """ Ckeck the links availability. """
    rv = client.get(path)
    assert rv.status_code == 200

@pytest.mark.parametrize("path", (
    ("/map/vts_proxy/fr/underground/0/0/0.jpg"),
))
def test_vts_proxy_bad_link(client, path):
    """ Ckeck the links inavailability. """
    rv = client.get(path)
    assert rv.status_code == 404
