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
Mapproxy used by both the 2D and the 3D map viewers.
This API gets xyz requests and sends tiles back.
"""

# pylint: disable=invalid-name; allow one letter variables (f.i. x, y, z)
# pylint: disable=line-too-long; allow long URLs

from pyquadkey2 import tilesystem  # Bing Maps QuadKey

from .tilenames import tileLatLonEdges  # bbox
from .utils import *

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
    "Format": "image/jpeg",
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
    "STYLES": "",
}

#: GEBCO parameters for the WMS service.
GEBCO_SHADED_PARAMS = {
    "request": "getmap",
    "service": "wms",
    "crs": "EPSG:4326",
    "format": "image/jpeg",
    "width": "256",
    "height": "256",
    "version": "1.3.0",
}

#: EUMETSAT parameters for the WMS service (specific to some layers).
EUMETSAT_PARAMS = {
    "TRANSPARENT": "TRUE",
    "FORMAT": "image/png8",
    "VERSION": "1.3.0",
    "TILED": "true",
    "EXCEPTIONS": "INIMAGE",
    "SERVICE": "WMS",
    "REQUEST": "GetMap",
    "CRS": "EPSG:4326",
    "WIDTH": "256",
    "HEIGHT": "256",
}


@vts_proxy_app.route("/world/topo/otm/<int:z>/<int:x>/<int:y>.png", methods=("GET",))
@same_site
def vts_proxy_world_topo_otm(z: int, x: int, y: int) -> FlaskResponse:
    """
    Tunneling map requests to the OpenTopoMap servers.
    Caching request is not forbidden by OpenTopoMap, so tiles are cached
    for better performance. Tiles are re-downloaded and overwritten if older than
    a week for complying the HTTP Expires value.
    """
    mimetype = "image/png"
    if z < 1:
        return tile_not_found(mimetype)
    cache_filename = tilesystem.tile_to_quadkey((x, y), z) + ".png"
    cache_path = os.path.join(OTM_CACHE, cache_filename)
    goto_cache = False
    if not os.path.isfile(cache_path):
        goto_cache = True
    else:
        time_cached_tile = datetime.datetime.fromtimestamp(os.path.getmtime(cache_path))
        time_now = datetime.datetime.now()
        if (time_cached_tile + datetime.timedelta(days=7)) < time_now:
            goto_cache = True
    if goto_cache:
        url = "https://opentopomap.org/{}/{}/{}.png".format(z, x, y)
        try:
            r = requests.get(url)
            # do not raise 404 error because the map coverage is global and the tile may be cached
        except requests.exceptions.HTTPError:  # pragma: no cover
            return tile_not_found(mimetype)
        if r.status_code == 200:
            with open(cache_path, "wb") as tile:
                tile.write(r.content)
        return Response(r.content, mimetype=mimetype)
    return send_from_directory(OTM_CACHE, cache_filename, mimetype=mimetype)


@vts_proxy_app.route(
    "/world/topo/thunderforest/<string:layer>/<int:z>/<int:x>/<int:y>.png",
    methods=("GET",),
)
@same_site
def vts_proxy_world_topo_thunderforest(
    layer: str, z: int, x: int, y: int
) -> FlaskResponse:
    """
    Tunneling map requests to the Thunderforest servers in order to hide the API key.
    Other tile layer URLs:
    https://manage.thunderforest.com/dashboard

    Args:
        layer (str): Tile layer.
        z (int): Z parameter of the XYZ request.
        x (int): X parameter of the XYZ request.
        y (int): Y parameter of the XYZ request.
    """
    mimetype = "image/png"
    layer = escape(layer)
    if layer not in (
        "cycle",
        "transport",
        "landscape",
        "outdoors",
        "transport-dark",
        "spinal-map",
        "pioneer",
        "mobile-atlas",
        "neighbourhood",
    ):
        return tile_not_found(mimetype)
    url = "https://tile.thunderforest.com/{}/{}/{}/{}.png?apikey={}".format(
        layer, z, x, y, current_app.config["THUNDERFOREST_API_KEY"]
    )
    try:
        r = requests.get(url)
        r.raise_for_status()  # raise for not found tiles
    except requests.exceptions.HTTPError:  # pragma: no cover
        return tile_not_found(mimetype)
    return Response(r.content, mimetype=mimetype)


@vts_proxy_app.route("/fr/<string:layer>/<int:z>/<int:x>/<int:y>.jpg", methods=("GET",))
@same_site
def vts_proxy_ign(layer: str, z: int, x: int, y: int) -> FlaskResponse:
    """
    Tunneling map requests to the IGN servers in order to hide the API key.
    """
    layer = escape(layer)
    mimetype = "image/jpeg"
    if layer == "satellite":
        layer = "ORTHOIMAGERY.ORTHOPHOTOS"
    elif layer == "topo":
        layer = "GEOGRAPHICALGRIDSYSTEMS.MAPS"
    else:
        return tile_not_found(mimetype)

    url = "https://{}:{}@wxs.ign.fr/{}/geoportail/wmts?layer={}&{}&TileMatrix={}&TileCol={}&TileRow={}".format(
        current_app.config["IGN"]["username"],
        current_app.config["IGN"]["password"],
        current_app.config["IGN"]["app"],
        layer,
        params_urlencode(IGN_COMMON_PARAMS),
        z,
        x,
        y,
    )

    try:
        # timeout to avoid freezing the map, 12 seconds is sometimes not enough!
        r = requests.get(url, timeout=12)
        # raise for not found tiles
        r.raise_for_status()
    except requests.exceptions.HTTPError:  # pragma: no cover
        return tile_not_found(mimetype)
    return Response(r.content, mimetype=mimetype)


def get_subdomain(
    x: int, y: int, subdomains: Union[str, Tuple[str], List[str]] = "abc"
) -> str:
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


@vts_proxy_app.route(
    "/nz/<string:layer>/<int:z>/<int:x>/<int:y>.<string:file_format>", methods=("GET",)
)
@same_site
def vts_proxy_lds(
    layer: str, z: int, x: int, y: int, file_format: str
) -> FlaskResponse:
    """
    Tunneling map requests to the LINZ servers in order to hide the API key.
    Help using LINZ with OpenLayers:
    https://www.linz.govt.nz/data/linz-data-service/guides-and-documentation/using-lds-xyz-services-in-openlayers

    Args:
        layer (str): satellite or topo. The layer type is replaced to the actual tile name.
        z (int): Z parameter of the XYZ request.
        x (int): X parameter of the XYZ request.
        y (int): Y parameter of the XYZ request.
        file_format (str): The file format to receive (supported: WebP and PNG).
    """
    mimetype = "image/" + escape(file_format)
    if layer == "satellite" and file_format == "webp":
        url = "https://basemaps.linz.govt.nz/v1/tiles/aerial/EPSG:3857/{}/{}/{}.webp?api={}".format(
            z, x, y, current_app.config["LINZ_API_KEYS"]["basemaps"]
        )
    elif layer == "topo" and file_format == "png":
        # https://www.linz.govt.nz/data/linz-data-service/guides-and-documentation/using-lds-xyz-services-in-leaflet
        subdomains = "abcd"

        url = "https://tiles-{}.data-cdn.linz.govt.nz/services;key={}/tiles/v4/{}/EPSG:3857/{}/{}/{}.png".format(
            get_subdomain(x, y, subdomains),
            current_app.config["LINZ_API_KEYS"]["lds"],
            "layer=767",
            z,
            x,
            y,
        )
    else:
        return tile_not_found(mimetype)

    try:
        r = requests.get(url)
        r.raise_for_status()  # raise for not found tiles
    except requests.exceptions.HTTPError:  # pragma: no cover
        return tile_not_found(mimetype)
    return Response(r.content, mimetype=mimetype)


@vts_proxy_app.route("/ca/topo/<int:z>/<int:x>/<int:y>.png", methods=("GET",))
@same_site
def vts_proxy_canvec(z: int, x: int, y: int) -> FlaskResponse:
    """
    Tunneling map requests to the Geogratis servers (Canada).
    Only the WMS service is available so the XYZ position used
    for a WMTS service is converted to a BBOX used for the
    WMS service.
    """
    mimetype = "image/png"
    s, w, n, e = tileLatLonEdges(x, y, z)
    url = "https://maps.geogratis.gc.ca/wms/canvec_en?{}&BBOX={},{},{},{}".format(
        params_urlencode(CANVEC_PARAMS), s, w, n, e
    )
    try:
        r = requests.get(url)
        r.raise_for_status()  # raise for not found tiles
    except requests.exceptions.HTTPError:  # pragma: no cover
        return tile_not_found(mimetype)
    return Response(r.content, mimetype=mimetype)


@vts_proxy_app.route(
    "/world/gebco/<string:layer>/<int:z>/<int:x>/<int:y>.jpeg", methods=("GET",)
)
@same_site
def vts_proxy_gebco(layer: str, z: int, x: int, y: int) -> FlaskResponse:
    """
    Tunneling map requests to the GEBCO servers.
    Only the WMS service is available so the XYZ position used
    for a WMTS service is converted to a BBOX used for the
    WMS service.
    """
    mimetype = "image/jpeg"
    layer = escape(layer)
    if layer == "shaded":
        layer = "gebco_2019_grid"
    elif layer == "flat":
        layer = "gebco_2019_grid_2"
    else:
        return tile_not_found(mimetype)
    s, w, n, e = tileLatLonEdges(x, y, z)
    url = "https://www.gebco.net/data_and_products/gebco_web_services/2019/mapserv?{}&layers={}&BBOX={},{},{},{}".format(
        params_urlencode(GEBCO_SHADED_PARAMS), layer, s, w, n, e
    )
    try:
        r = requests.get(url)
        r.raise_for_status()  # raise for not found tiles
    except requests.exceptions.HTTPError:  # pragma: no cover
        return tile_not_found(mimetype)
    return Response(r.content, mimetype=mimetype)


@vts_proxy_app.route(
    "/eumetsat/<string:layer>/<int:z>/<int:x>/<int:y>.png", methods=("GET",)
)
@same_site
def vts_proxy_eumetsat(layer: str, z: int, x: int, y: int) -> FlaskResponse:
    """
    Tunneling map requests to the EUMETSAT servers.
    Only the WMS service is available so the XYZ position used
    for a WMTS service is converted to a BBOX used for the
    WMS service.
    """
    mimetype = "image/png"
    layer = escape(layer)
    if layer == "meteosat_iodc_mpe":
        layer = "msgiodc:msgiodc_mpe"
        style = "style_msg_mpe"
    elif layer == "meteosat_0deg_h0b3":
        layer = "meteosat:msg_h03B"
        style = "style_h03B"
    else:
        return tile_not_found(mimetype)

    last_weather_update = datetime.datetime.utcnow() - datetime.timedelta(hours=1)
    to_quarter = last_weather_update.minute % 15
    if to_quarter:
        last_weather_update += datetime.timedelta(minutes=15 - to_quarter)
    str_time = last_weather_update.strftime("%Y-%m-%dT%H:%M:00.000Z")

    s, w, n, e = tileLatLonEdges(x, y, z)
    url = "https://eumetview.eumetsat.int/geoserv/wms?{}&LAYERS={}&STYLES={}&TIME={}&BBOX={},{},{},{}".format(
        params_urlencode(EUMETSAT_PARAMS), layer, style, str_time, s, w, n, e
    )
    try:
        r = requests.get(url)
        r.raise_for_status()  # raise for not found tiles
    except requests.exceptions.HTTPError:  # pragma: no cover
        return tile_not_found(mimetype)
    return Response(r.content, mimetype=mimetype)


def download_bing_metadata(
    bing_key: str, imagery_set: str = "Aerial", timeout: int = 10
) -> Tuple[str, List[str]]:
    """
    Download the imagery URLs (and metadata) from Bing Maps through the Microsoft API:

    * API Type: REST Services
    * API Category: RESTImagery-Metadata
    * Billable: Yes
    * Cost: free up to 125,000 calls per calendar year

    More information:

    * Get Imagery Metadata (Microsoft):
      https://docs.microsoft.com/en-us/bingmaps/rest-services/imagery/get-imagery-metadata

    * The request timeout is based on the official VTS Mapproxy:
      https://github.com/melowntech/vts-mapproxy/blob/master/mapproxy/src/mapproxy/generator/tms-bing.cpp#L105

    * Licensing Options (Microsoft):
      https://www.microsoft.com/en-us/maps/licensing/licensing-options

    Args:
        bing_key (str): The Bing Maps private app key.
        imagery_set (str): The type of imagery for which you are requesting metadata.
        timeout (int): The HTTP request timeout in seconds.

    Returns:
        The image URL and a list of subdomains. The URL is forced to be HTTPS.
    """
    metadata_url = (
        "https://dev.virtualearth.net/REST/v1/Imagery/Metadata/"
        + imagery_set
        + "?key="
        + bing_key
    )

    with requests.Session() as s:
        try:
            r = s.get(metadata_url, timeout=timeout)
            r.raise_for_status()
        except requests.exceptions.HTTPError as err:  # pragma: no cover
            raise Exception(
                "Failed to download the imagery metadata from Bing Maps ("
                + str(r.status_code)
                + " status code)"
            ) from err

    try:
        metadata = json.loads(r.content)
    except json.JSONDecodeError as err:
        raise Exception("Failed to parse JSON metadata") from err
    if not all(x in metadata for x in ["authenticationResultCode", "statusCode"]):
        raise Exception("Missing result or status code")
    if metadata["authenticationResultCode"] != "ValidCredentials":
        raise Exception("Invalid Bing Maps credentials")
    if metadata["statusCode"] >= 400:  # 400, 401, 404, 429, 500, 503
        raise Exception("Bing Maps error status code " + metadata["statusCode"])
    try:
        resource = metadata["resourceSets"][0]["resources"][0]
        image_url = resource["imageUrl"]
        subdomains = resource["imageUrlSubdomains"]
    except Exception as err:
        raise Exception("Missing resources from the metadata") from err

    return image_url.replace("http://", "https://"), subdomains


@vts_proxy_app.route(
    "/world/satellite/bing/<int:z>/<int:x>/<int:y>.jpeg", methods=("GET",)
)
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
    mimetype = "image/jpeg"
    if (
        z < 1
    ):  # the lowest level of detail is 1, i.e. the tile 0/0/0.jpeg does not exist
        return tile_not_found(mimetype)
    if "BingImageryMetadata" not in session:
        try:
            metadata = download_bing_metadata(current_app.config["BING_API_KEY"])
            session["BingImageryMetadata"] = metadata
        except Exception as e:  # pylint: disable=broad-except
            return str(e), 500
    else:
        metadata = session["BingImageryMetadata"]
    image_url, subdomains = metadata
    try:
        r = requests.get(
            image_url.format(
                subdomain=get_subdomain(x, y, subdomains),
                quadkey=tilesystem.tile_to_quadkey((x, y), z),
            )
        )
        r.raise_for_status()
    except requests.exceptions.HTTPError:  # pragma: no cover
        return tile_not_found(mimetype)
    return Response(r.content, mimetype=mimetype)
