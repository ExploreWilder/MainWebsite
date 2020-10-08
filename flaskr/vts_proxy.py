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
from .tilenames import tileLatLonEdges # bbox
from pyquadkey2 import tilesystem # Bing Maps QuadKey

vts_proxy_app = Blueprint("vts_proxy_app", __name__)

#: OpenTopoMap cache directory.
OTM_CACHE = absolute_path("../otm_cache")

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

@vts_proxy_app.route("/world/topo/otm/<int:z>/<int:x>/<int:y>.png", methods=("GET",))
@same_site
def vts_proxy_world_topo_otm(z: int, x: int, y: int) -> FlaskResponse:
    """
    Tunneling map requests to the OpenTopoMap servers.
    To use only with VTS Browser JS. Use proxy_ign() for OpenLayers.
    Notice: an offset of 1 on the Z index has been applied.
    Caching request is not forbidden by OpenTopoMap, so tiles are cached
    for better performance.

    Raises:
        404: in case of OpenTopoMap error or if the request comes from another website and not in testing mode.
    """
    cache_filename = "{}.{}.{}.png".format(z, x, y)
    cache_path = os.path.join(OTM_CACHE, cache_filename)
    if not os.path.isfile(cache_path):
        url = "https://opentopomap.org/{}/{}/{}.png".format(z, x, y)
        try:
            r = requests.get(url)
        except:
            abort(404)
        with open(cache_path, "wb") as tile:
            tile.write(r.content)
        return Response(r.content, mimetype="image/png")
    return send_from_directory(OTM_CACHE, cache_filename, mimetype="image/png")

@vts_proxy_app.route("/world/topo/thunderforest/<string:layer>/<int:z>/<int:x>/<int:y>.png", methods=("GET",))
@same_site
def vts_proxy_world_topo_thunderforest(layer: str, z: int, x: int, y: int) -> FlaskResponse:
    """
    Tunneling map requests to the Thunderforest servers in order to hide the API key.
    Other tile layer URLs:
    https://manage.thunderforest.com/dashboard

    Raises:
        404: in case of Thunderforest error (such as ConnectionError).

    Args:
        layer (str): Tile layer.
        z (int): Z parameter of the XYZ request.
        x (int): X parameter of the XYZ request.
        y (int): Y parameter of the XYZ request.
    """
    layer = escape(layer)
    if not layer in (
        'cycle',
        'transport',
        'landscape',
        'outdoors',
        'transport-dark',
        'spinal-map',
        'pioneer',
        'mobile-atlas',
        'neighbourhood'):
        abort(404)
    url = "https://tile.thunderforest.com/{}/{}/{}/{}.png?apikey={}".format(
        layer,
        z,
        x,
        y,
        current_app.config["THUNDERFOREST_API_KEY"])
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
        z,
        x,
        y)
    
    try:
        r = requests.get(url)
    except:
        abort(404)
    return Response(r.content, mimetype="image/jpeg")

def get_subdomain(x: int, y:int, subdomains: Union[str, Tuple[str]] = "abc") -> str:
    """
    Returns a subdomain based on the position.
    Subdomains help supporting more simultaneous tile requests.
    https://github.com/Leaflet/Leaflet/blob/37d2fd15ad6518c254fae3e033177e96c48b5012/src/layer/tile/TileLayer.js#L222

    Args:
        x (int): X coord in the XYZ system.
        y (int): Y coord in the XYZ system.
        subdomains: List of letters made available by the tiles supplier.
                    Example:
                    
                    * a string: "abcd" for subdomains a, b, c, and d
                    * or a tuple/list: ("10", "100", "101", "102", "103", "104", "20")
    
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
        z,
        x,
        y)
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

    s,w,n,e = tileLatLonEdges(x,y,z)
    url = "https://maps.geogratis.gc.ca/wms/canvec_en?{}&BBOX={},{},{},{}".format(
        params_urlencode(CANVEC_PARAMS), s, w, n, e)
    try:
        r = requests.get(url)
    except:
        abort(404)
    return Response(r.content, mimetype="image/png")

def download_bing_metadata(bing_key: str, imagery_set: str = "Aerial", timeout: int = 10) -> Tuple[str, List[str]]:
    """
    Download the metadata URL from Bing Maps.

    More information:

    * Get Imagery Metadata (Microsoft):
      https://docs.microsoft.com/en-us/bingmaps/rest-services/imagery/get-imagery-metadata
    
    * The request configuration (timeout and Keep-Alive) is based on the VTS Mapproxy / TMS Bing:
      https://github.com/melowntech/vts-mapproxy/blob/master/mapproxy/src/mapproxy/generator/tms-bing.cpp#L105
    
    Args:
        bing_key (str): The Bing Maps private app key.
        imagery_set (str): The type of imagery for which you are requesting metadata.
        timeout (int): The HTTP request timeout in seconds.
    
    Returns:
        The image URL and a list of subdomains. The URL is forced to be HTTPS.
    """
    metadata_url = "https://dev.virtualearth.net/REST/v1/Imagery/Metadata/" + imagery_set + "?key=" + bing_key

    with requests.Session() as s:
        s.keep_alive = False # no reuse
        try:
            r = s.get(metadata_url, timeout=timeout)
            r.raise_for_status()
        except requests.exceptions.HTTPError as err:
            raise Exception("Failed to download the imagery metadata from Bing Maps (" + r.status_code + " status code)")
    
    try:
        metadata = json.loads(r.content)
        if metadata["authenticationResultCode"] != "ValidCredentials":
            raise Exception("Invalid Bing Maps credentials")
        if metadata["statusCode"] >= 400: # 400, 401, 404, 429, 500, 503
            raise Exception("Bing Maps error status code " + metadata["statusCode"])
    except:
        raise Exception("Bad metadata")
    try:
        resource = metadata["resourceSets"][0]["resources"][0]
        image_url = resource["imageUrl"]
        subdomains = resource["imageUrlSubdomains"]
    except:
        raise Exception("Missing resources from the metadata")
    
    return (image_url.replace("http://", "https://"), subdomains)

@vts_proxy_app.route("/world/satellite/bing/<int:z>/<int:x>/<int:y>.jpeg", methods=("GET",))
@same_site
def vts_proxy_bing_aerial(z: int, x: int, y: int) -> FlaskResponse:
    """
    Handle the Bing Maps protocol of tiles request:

    1) get metadata for imagery that is hosted by Bing Maps,
    2) get the image URLs from the metadata,
    3) find out the QuadKey from the xyz coords,
    4) download and return the tile.

    The first step is done only once to find out the regularly changing
    Bing tile URL and subdomains, then the result is saved into the session.
    
    The private key is sent to Bing only.
    The image URLs are not sensitive data and actually exposed to the user
    via the session, which is signed by design to avoid requesting a bad URL.

    More information:
    
    * Displaying Bing Map layers (Melowntech):
      https://vts-geospatial.org/tutorials/bing-maps.html?highlight=bing
    
    * Directly accessing the Bing Maps tiles (Microsoft):
      https://docs.microsoft.com/en-us/bingmaps/rest-services/directly-accessing-the-bing-maps-tiles
    
    * Bing Maps Tile System (Microsoft):
      https://docs.microsoft.com/en-us/bingmaps/articles/bing-maps-tile-system
    
    """
    if not "BingImageryMetadata" in session:
        try:
            metadata = download_bing_metadata(current_app.config["BING_API_KEY"])
            session["BingImageryMetadata"] = metadata
        except Exception as e:
            return str(e), 500
    else:
        metadata = session["BingImageryMetadata"]
    image_url, subdomains = metadata
    r = requests.get(image_url.format(
        subdomain=get_subdomain(x, y, subdomains),
        quadkey=tilesystem.tile_to_quadkey((x, y), z)))
    return Response(r.content, mimetype="image/jpeg")
