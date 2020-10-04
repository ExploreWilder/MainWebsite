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
from .tilenames import tileLatLonEdges

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

#: Canvec parameters for the WMS service.
CANVEC_PARAMS = {
    "SERVICE": "WMS",
    "VERSION": "1.3.0",
    "REQUEST": "GetMap",
    "FORMAT": "image/png",
    "TRANSPARENT": "false",
    "LAYERS": "canvec",
    "WIDTH": "256",
    "HEIGHT": "256",
    "CRS": "EPSG:4326",
    "STYLES": ""
}

@vts_proxy_app.route("/world/satellite/<int:z>/<int:x>/<int:y>.jpg", methods=("GET",))
@same_site
def vts_proxy_world_sat(z: int, x: int, y: int) -> FlaskResponse:
    """
    Tunneling map requests to the Mapbox servers.
    To use only with VTS Browser JS. Use proxy_ign() for OpenLayers.
    Notice: an offset of 1 on the Z index has been applied.

    Raises:
        404: in case of Mapbox error or if the request comes from another website and not in testing mode.
    """
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
@same_site
def vts_proxy_world_topo(z: int, x: int, y: int) -> FlaskResponse:
    """
    Tunneling map requests to the OpenTopoMap servers.
    To use only with VTS Browser JS. Use proxy_ign() for OpenLayers.
    Notice: an offset of 1 on the Z index has been applied.

    Raises:
        404: in case of OpenTopoMap error or if the request comes from another website and not in testing mode.
    """
    url = "https://opentopomap.org/{}/{}/{}.png".format(
        z - 1,
        x,
        y)
    try:
        r = requests.get(url)
    except:
        abort(404)
    return Response(r.content, mimetype="image/png")

@vts_proxy_app.route("/fr/<string:layer>/<int:z>/<int:x>/<int:y>.jpg", methods=("GET",))
@same_site
def vts_proxy_ign(layer: str, z: int, x: int, y: int) -> FlaskResponse:
    """
    Tunneling map requests to the IGN servers in order to hide the API key.
    To use only with VTS Browser JS. Use proxy_ign() for OpenLayers.
    Notice: an offset of 1 on the Z index has been applied.

    Raises:
        404: in case of IGN error or if the request comes from another website and not in testing mode.
    """
    layer = escape(layer)
    if layer == "satellite":
        layer = "ORTHOIMAGERY.ORTHOPHOTOS"
    elif layer == "topo":
        layer = "GEOGRAPHICALGRIDSYSTEMS.MAPS"
    else:
        abort(404)
    
    url = "https://{}:{}@wxs.ign.fr/{}/geoportail/wmts?layer={}&{}&TileMatrix={}&TileCol={}&TileRow={}".format(
        current_app.config["IGN"]["username"],
        current_app.config["IGN"]["password"],
        current_app.config["IGN"]["app"],
        layer,
        params_urlencode(IGN_COMMON_PARAMS),
        z - 1,
        x,
        y)
    
    try:
        r = requests.get(url)
    except:
        abort(404)
    return Response(r.content, mimetype="image/jpeg")

def get_subdomain(x: int, y:int, subdomains: str = "abc") -> str:
    """
    Returns a subdomain based on the position.
    Subdomains help supporting more simultaneous tile requests.
    https://github.com/Leaflet/Leaflet/blob/37d2fd15ad6518c254fae3e033177e96c48b5012/src/layer/tile/TileLayer.js#L222

    Args:
        x (int): X coord in the XYZ system.
        y (int): Y coord in the XYZ system.
        subdomains (str): List of letters made available by the tiles supplier.
    
    Returns:
        str: One of the subdomain letter.
    """
    return subdomains[abs(x + y) % len(subdomains)]

@vts_proxy_app.route("/nz/<string:layer>/<int:z>/<int:x>/<int:y>.png", methods=("GET",))
@same_site
def vts_proxy_lds(layer: str, z: int, x: int, y: int) -> FlaskResponse:
    """
    Tunneling map requests to the LDS servers in order to hide the API key.
    Help using LDS with OpenLayers:
    https://www.linz.govt.nz/data/linz-data-service/guides-and-documentation/using-lds-xyz-services-in-openlayers

    Raises:
        404: in case of LDS error (such as ConnectionError).

    Args:
        layer (str): satellite or topo. The layer type is replaced to the actual tile name.
        z (int): Z parameter of the XYZ request.
        x (int): X parameter of the XYZ request.
        y (int): Y parameter of the XYZ request.
    """
    layer = escape(layer)
    if layer == "satellite":
        layer = "set=2"
    elif layer == "topo":
        layer = "layer=767"
    else:
        abort(404)
    
    # https://www.linz.govt.nz/data/linz-data-service/guides-and-documentation/using-lds-xyz-services-in-leaflet
    subdomains = "abcd"

    url = "https://tiles-{}.data-cdn.linz.govt.nz/services;key={}/tiles/v4/{}/EPSG:3857/{}/{}/{}.png".format(
        get_subdomain(x, y, subdomains),
        current_app.config["LDS_API_KEY"],
        layer,
        z - 1,
        x,
        y)
    try:
        r = requests.get(url)
    except:
        abort(404)
    return Response(r.content, mimetype="image/png")

@vts_proxy_app.route("/no/topo/<int:z>/<int:x>/<int:y>.png", methods=("GET",))
@same_site
def vts_proxy_topografisk(z: int, x: int, y: int) -> FlaskResponse:
    """
    Tunneling map requests to the Kartverket servers (Norway).
    Howto available here: https://kartverket.no/en/data/lage-kart-pa-nett/

    Raises:
        404: in case of server error or if the request comes from another website and not in testing mode.

    Args:
        z (int): Z parameter of the XYZ request.
        x (int): X parameter of the XYZ request.
        y (int): Y parameter of the XYZ request.
    """
    url = "https://opencache.statkart.no/gatekeeper/gk/gk.open_gmaps?layers=topo4&zoom={}&x={}&y={}".format(
        z - 1, x, y)
    try:
        r = requests.get(url)
    except:
        abort(404)
    return Response(r.content, mimetype="image/png")

@vts_proxy_app.route("/ca/topo/<int:z>/<int:x>/<int:y>.png", methods=("GET",))
@same_site
def vts_proxy_canvec(z: int, x: int, y: int) -> FlaskResponse:
    """
    Tunneling map requests to the Geogratis servers (Canada).
    Only the WMS service is available so the XYZ position used
    for a WMTS service is converted to a BBOX used for the
    WMS service.

    Raises:
        404: in case of server error or if the request comes from another website and not in testing mode.
    """

    s,w,n,e = tileLatLonEdges(x,y,z - 1)
    url = "http://maps.geogratis.gc.ca/wms/canvec_en?{}&BBOX={},{},{},{}".format(
        params_urlencode(CANVEC_PARAMS), s, w, n, e)
    try:
        r = requests.get(url)
    except:
        abort(404)
    return Response(r.content, mimetype="image/png")
