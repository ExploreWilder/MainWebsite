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

from .utils import *

vts_proxy_app = Blueprint("vts_proxy_app", __name__)

#: IGN parameters used for all IGN layers.
IGN_COMMON_PARAMS = {
    "style": "normal",
    "tilematrixset": "PM",
    "Service": "WMTS",
    "Request": "GetTile",
    "Version": "1.0.0",
    "Format": "image/jpeg"
}

@vts_proxy_app.route("/world/satellite/<int:z>/<int:x>/<int:y>.jpg", methods=("GET",))
def vts_proxy_world_sat(z: int, x: int, y: int) -> FlaskResponse:
    """
    Tunneling map requests to the Mapbox servers.
    To use only with VTS Browser JS. Use proxy_ign() for OpenLayers.
    Notice: an offset of 1 on the Z index has been applied.

    Raises:
        404: in case of Mapbox error or if the request comes from another website and not in testing mode.
    """
    if not is_same_site() and not (current_app.config["TESTING"] or current_app.config["DEBUG"]):
        abort(404)
    url = "https://api.mapbox.com/v4/mapbox.satellite/{}/{}/{}@2x.jpg90?access_token={}".format(
        z - 1, # hack
        x,
        y,
        current_app.config["MAPBOX_PUB_KEY"])
    try:
        r = requests.get(url)
    except:
        abort(404)
    return Response(r.content, mimetype="image/jpeg")

@vts_proxy_app.route("/world/topo/<int:z>/<int:x>/<int:y>.png", methods=("GET",))
def vts_proxy_world_topo(z: int, x: int, y: int) -> FlaskResponse:
    """
    Tunneling map requests to the OpenTopoMap servers.
    To use only with VTS Browser JS. Use proxy_ign() for OpenLayers.
    Notice: an offset of 1 on the Z index has been applied.

    Raises:
        404: in case of OpenTopoMap error or if the request comes from another website and not in testing mode.
    """
    if not is_same_site() and not (current_app.config["TESTING"] or current_app.config["DEBUG"]):
        abort(404)
    url = "https://opentopomap.org/{}/{}/{}.png".format(
        z - 1,
        x,
        y)
    try:
        r = requests.get(url)
    except:
        abort(404)
    return Response(r.content, mimetype="image/png")

@vts_proxy_app.route("/fr/satellite/<int:z>/<int:x>/<int:y>.jpg", methods=("GET",))
def vts_proxy_ign_sat(z: int, x: int, y: int) -> FlaskResponse:
    """
    Tunneling map requests to the IGN servers in order to hide the API key.
    To use only with VTS Browser JS. Use proxy_ign() for OpenLayers.
    Notice: an offset of 1 on the Z index has been applied.

    Raises:
        404: in case of IGN error or if the request comes from another website and not in testing mode.
    """
    if not is_same_site() and not (current_app.config["TESTING"] or current_app.config["DEBUG"]):
        abort(404)
    url = "https://{}:{}@wxs.ign.fr/{}/geoportail/wmts?layer={}&{}&TileMatrix={}&TileCol={}&TileRow={}".format(
        current_app.config["IGN"]["username"],
        current_app.config["IGN"]["password"],
        current_app.config["IGN"]["app"],
        "ORTHOIMAGERY.ORTHOPHOTOS", # layer
        params_urlencode(IGN_COMMON_PARAMS),
        z - 1,
        x,
        y)
    try:
        r = requests.get(url)
    except:
        abort(404)
    return Response(r.content, mimetype="image/jpeg")

@vts_proxy_app.route("/fr/topo/<int:z>/<int:x>/<int:y>.jpg", methods=("GET",))
def vts_proxy_ign_topo(z: int, x: int, y: int) -> FlaskResponse:
    """
    Tunneling map requests to the IGN servers in order to hide the API key.

    Raises:
        404: in case of IGN error or if the request comes from another website and not in testing mode.
    """
    if not is_same_site() and not (current_app.config["TESTING"] or current_app.config["DEBUG"]):
        abort(404)
    url = "https://{}:{}@wxs.ign.fr/{}/geoportail/wmts?layer={}&{}&TileMatrix={}&TileCol={}&TileRow={}".format(
        current_app.config["IGN"]["username"],
        current_app.config["IGN"]["password"],
        current_app.config["IGN"]["app"],
        "GEOGRAPHICALGRIDSYSTEMS.MAPS",
        params_urlencode(IGN_COMMON_PARAMS),
        z - 1,
        x,
        y)
    try:
        r = requests.get(url)
    except:
        abort(404)
    return Response(r.content, mimetype="image/jpeg")
