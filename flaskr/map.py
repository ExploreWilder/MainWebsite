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

import srtm, gpxpy, gpxpy.gpx

from .utils import *
from .db import get_db
from .gpx_to_img import gpx_to_src
from .webtrack import WebTrack

map_app = Blueprint("map_app", __name__)
mysql = LocalProxy(get_db)


def track_path_to_header(
    book_id: int, book_url: str, book_title: str, gpx_name: str
) -> List[Dict]:
    """
    Format the header breadcrumbs - refer to templates/layout.html.

    Args:
        book_id (int): Book ID based on the 'shelf' database table.
        book_url (str): Book URL based on the 'shelf' database table.
        book_title (str): Book title based on the 'shelf' database table.
        gpx_name (str): Name of the GPX file in the /tracks directory WITHOUT file extension.

    Returns:
        List of dicts.
    """
    return [
        {"title": "Stories", "url": "/stories"},
        {
            "title": book_title,
            "url": "/stories/" + str(book_id) + "/" + book_url,
        },
        {
            "title": gpx_name.replace("_", " ")
            # no URL because it is the current one
        },
    ]


def get_gpx_download_path(book_id: int, book_url: str, gpx_name: str) -> str:
    """
    Returns the path to the GPX file.

    Returns:
        str: For example '/books/42/my_story/super_track.gpx'
    """
    return "/".join(["/books", str(book_id), book_url, gpx_name]) + ".gpx"


def get_thumbnail_path(book_id: int, book_url: str, gpx_name: str) -> str:
    """
    Returns the path to the thumbnail file.

    Returns:
        str: For example: 'map/static_map/42/my_story/super_track.gpx.jpg'
    """
    return "map/static_map/" + "/".join([str(book_id), book_url, gpx_name]) + ".jpg"


@map_app.route(
    "/player/<int:book_id>/<string:book_url>/<string:gpx_name>/<string:country>"
)
def map_player(book_id: int, book_url: str, gpx_name: str, country: str) -> Any:
    """
    Map viewer with a real 3D map more focused on a fun user experience than a hiker-centric track viewer.
    A track is always linked to a story and the navbar would display breadcrumbs and a link to the 2D version.
    The path to the map configuration is in the Jinja template.

    Args:
        book_id (int): Book ID based on the 'shelf' database table.
        book_url (str): Book URL based on the 'shelf' database table.
        gpx_name (str): Name of the GPX file in the /tracks directory WITHOUT file extension. NOT USED.

    Raises:
        404: in case of denied access.
    """
    cursor = mysql.cursor()
    book_url = escape(book_url)
    gpx_name = escape(gpx_name)
    country_code = escape(country)
    country_code_up = country_code.upper()
    cursor.execute(
        """SELECT access_level, title
        FROM shelf
        WHERE book_id={book_id} AND url='{book_url}'""".format(
            book_id=book_id, book_url=book_url
        )
    )
    data = cursor.fetchone()
    if cursor.rowcount == 0 or actual_access_level() < data[0]:
        abort(404)
    if actual_access_level() >= current_app.config["ACCESS_LEVEL_DOWNLOAD_GPX"]:
        gpx_download_path = get_gpx_download_path(book_id, book_url, gpx_name)
    else:
        gpx_download_path = ""
    return render_template(
        "map_player.html",
        header_breadcrumbs=track_path_to_header(book_id, book_url, data[1], gpx_name),
        url_topo_map="/map/viewer/"
        + "/".join([str(book_id), book_url, gpx_name, country_code]),
        country=country_code_up,
        gpx_download_path=gpx_download_path,
        thumbnail_networks=request.url_root
        + get_thumbnail_path(book_id, book_url, gpx_name),
        total_subscribers=total_subscribers(cursor),
        is_prod=not current_app.config["DEBUG"],
    )


@map_app.route(
    "/viewer/<int:book_id>/<string:book_url>/<string:gpx_name>/<string:country>"
)
def map_viewer(book_id: int, book_url: str, gpx_name: str, country: str) -> Any:
    """
    2D map viewer with some basic tools, track and topo information.
    A track is always linked to a story and the navbar would display breadcrumbs and a link to the 3D version.

    Args:
        book_id (int): Book ID based on the 'shelf' database table.
        book_url (str): Book URL based on the 'shelf' database table.
        gpx_name (str): Name of the GPX file in the /tracks directory WITHOUT file extension. NOT USED.
        country (str): Country code (f.i. "nz".)

    Raises:
        404: in case of denied access.
    """
    cursor = mysql.cursor()
    book_url = escape(book_url)
    gpx_name = escape(gpx_name)
    cursor.execute(
        """SELECT access_level, title
        FROM shelf
        WHERE book_id={book_id} AND url='{book_url}'""".format(
            book_id=book_id, book_url=book_url
        )
    )
    data = cursor.fetchone()
    country_code = escape(country)
    country_code_up = country_code.upper()
    if (
        cursor.rowcount == 0
        or actual_access_level() < data[0]
        or not country_code_up in current_app.config["MAP_LAYERS"]
    ):
        abort(404)
    if actual_access_level() >= current_app.config["ACCESS_LEVEL_DOWNLOAD_GPX"]:
        gpx_download_path = get_gpx_download_path(book_id, book_url, gpx_name)
    else:
        gpx_download_path = ""
    return render_template(
        "map_viewer.html",
        country=country_code_up,
        header_breadcrumbs=track_path_to_header(book_id, book_url, data[1], gpx_name),
        url_player_map="/map/player/"
        + "/".join([str(book_id), book_url, gpx_name, country_code]),
        gpx_download_path=gpx_download_path,
        thumbnail_networks=request.url_root
        + get_thumbnail_path(book_id, book_url, gpx_name),
        total_subscribers=total_subscribers(cursor),
        is_prod=not current_app.config["DEBUG"],
    )


def create_static_map(
    gpx_path: str, static_map_path: str, static_image_settings: Dict
) -> None:
    """
    Create a URL based on the ``gpx_path`` GPX file and the ``static_image_settings`` configuration.
    The URL is then fetched to the Mapbox server to retrieve a JPG image.
    Mapbox pricing: https://www.mapbox.com/pricing/#glstatic (free up to 50,000 per month)
    A Mapbox access token is required for the map generation.

    Args:
        gpx_path (str): Secured path to the input file.
        static_map_path (str): Secured path to the overwritten output file.
        static_image_settings (Dict): Mapbox Static Images configuration (kind of).

    Returns:
        Nothing, the image is saved into the disk.
    """
    with open(gpx_path, "r") as gpx_file:
        gpx = gpxpy.parse(gpx_file)
    url = gpx_to_src(gpx, static_image_settings)
    r = requests.get(url)
    with open(static_map_path, "wb") as static_image:
        static_image.write(r.content)


@map_app.route("/static_map/<int:book_id>/<string:book_url>/<string:gpx_name>.jpg")
def static_map(book_id: int, book_url: str, gpx_name: str) -> FlaskResponse:
    """
    Print a static map and create it if not already existing or not up to date.
    Keep this route open to external requests since it's used as thumbnail for the social platforms.

    Args:
        book_id (int): Book ID based on the 'shelf' database table.
        book_url (str): Book URL based on the 'shelf' database table.
        gpx_name (str): Name of the GPX file in the /tracks directory WITHOUT file extension.

    Returns:
        JPG image.

    Raises:
        500: failed to create the image.
    """
    book_url = escape(book_url)
    cursor = mysql.cursor()
    cursor.execute(
        """SELECT access_level
        FROM shelf
        WHERE book_id={book_id} AND url='{book_url}'""".format(
            book_id=book_id, book_url=book_url
        )
    )
    data = cursor.fetchone()
    if cursor.rowcount == 0 or actual_access_level() < data[0]:
        abort(404)
    gpx_filename = secure_filename(escape(gpx_name) + ".gpx")
    gpx_dir = os.path.join(
        current_app.config["SHELF_FOLDER"], secure_filename(book_url)
    )
    gpx_path = os.path.join(gpx_dir, gpx_filename)
    append_ext = "_static_map.jpg"
    static_map_path = gpx_path + append_ext
    if (
        not os.path.isfile(static_map_path)
        or os.stat(static_map_path).st_size == 0
        or os.stat(static_map_path).st_mtime < os.stat(gpx_path).st_mtime
    ):  # update profile
        try:
            create_static_map(
                gpx_path, static_map_path, current_app.config["MAPBOX_STATIC_IMAGES"]
            )
        except Exception as e:
            return "{}".format(type(e).__name__), 500
    return send_from_directory(gpx_dir, gpx_filename + append_ext)


@map_app.route("/webtracks/<int:book_id>/<string:book_url>/<string:gpx_name>.webtrack")
@same_site
def webtrack_file(book_id: int, book_url: str, gpx_name: str) -> FlaskResponse:
    """
    Print a profile file and create it if not already existing or not up to date.

    Args:
        book_id (int): Book ID based on the 'shelf' database table.
        book_url (str): Book URL based on the 'shelf' database table.
        gpx_name (str): Name of the GPX file in the /tracks directory WITHOUT file extension.
        country (str): Country code (f.i. "nz".) NOT USED.

    Returns:
        JSON file containing the profile and statistics.

    Raises:
        404: if the request comes from another website and not in testing mode.
        500: failed to create the elevation profile.
    """
    book_url = escape(book_url)
    cursor = mysql.cursor()
    cursor.execute(
        """SELECT access_level
        FROM shelf
        WHERE book_id={book_id} AND url='{book_url}'""".format(
            book_id=book_id, book_url=book_url
        )
    )
    data = cursor.fetchone()
    if cursor.rowcount == 0 or actual_access_level() < data[0]:
        abort(404)
    gpx_filename = secure_filename(escape(gpx_name) + ".gpx")
    gpx_dir = os.path.join(
        current_app.config["SHELF_FOLDER"], secure_filename(book_url)
    )
    gpx_path = os.path.join(gpx_dir, gpx_filename)
    if not os.path.isfile(gpx_path) or os.stat(gpx_path).st_size == 0:
        return "GPX file missing or empty", 500
    webtrack_path = replace_extension(gpx_path, "webtrack")
    if (
        not os.path.isfile(webtrack_path)
        or os.stat(webtrack_path).st_size == 0
        or os.stat(webtrack_path).st_mtime < os.stat(gpx_path).st_mtime
    ):  # update webtrack
        try:  # TODO: re-create the WebTrack file if bad header information
            gpx_to_webtrack_with_elevation(
                gpx_path, webtrack_path, current_app.config["NASA_EARTHDATA"]
            )
        except Exception as e:
            return "{}".format(type(e).__name__), 500
    return send_from_directory(
        gpx_dir,
        replace_extension(gpx_filename, "webtrack"),
        mimetype="application/prs.webtrack",
    )


class CustomFileHandler(srtm.data.FileHandler):
    """
    The custom file handler to choose the cache directory.
    https://github.com/ExploreWilder/srtm.py/blob/EarthDataLogin/srtm/data.py
    """

    def get_srtm_dir(self) -> str:
        """ The default path to store files. """
        # Local cache path:
        result = absolute_path("../srtm_cache")

        if not os.path.exists(result):
            os.makedirs(result)

        return result


def gpx_to_webtrack_with_elevation(
    gpx_path: str, webtrack_path: str, credentials: Dict[str, str]
) -> None:
    """
    Find out the elevation profile of ``gpx_path`` thanks to SRTM data
    version 3.0 with 1-arc-second for the whole world and save the result
    into ``webtrack_path`` which is overwritten if already existing.
    Data source: https://e4ftl01.cr.usgs.gov/MEASURES/SRTMGL1.003/
    Also: https://lpdaac.usgs.gov/products/srtmgl1v003/
    Note: In case of USGS.gov server error, you should see a notification banner in:
    https://lpdaac.usgs.gov/products/srtmgl1v003/
    such as "LP DAAC websites and HTTP downloads will be unavailable..."
    SRTMGL1.003 data requires user authentication through the NASA Earthdata Login.
    Use gpxpy: https://github.com/tkrajina/gpxpy
    Use SRTM.py: https://github.com/nawagers/srtm.py/tree/EarthDataLogin
    SRTM data are stored in the folder specified in CustomFileHandler().get_srtm_dir()

    Args:
        gpx_path (str): Secured path to the input file.
        webtrack_path (str): Secured path to the overwritten output file.

    Returns:
        The result is saved into a file, nothing is returned.
    """
    elevation_data = srtm.data.GeoElevationData(
        version="v3.1a",
        EDuser=credentials["username"],
        EDpass=credentials["password"],
        file_handler=CustomFileHandler(),
    )
    with open(gpx_path, "r") as input_gpx_file:
        gpx = gpxpy.parse(input_gpx_file)
        elevation_data.add_elevations(gpx, smooth=True)
        elevation_profile = []
        elevation_min = 10000
        elevation_max = -elevation_min
        elevation_total_gain = 0
        elevation_total_loss = 0
        current_length = 0
        delta_h = None
        for track in gpx.tracks:
            for segment in track.segments:
                for gps_curr_point in segment.points:
                    # add point to segment:
                    if delta_h is not None:
                        current_length += gpxpy.geo.haversine_distance(
                            gps_curr_point.latitude,
                            gps_curr_point.longitude,
                            gps_prev_point.latitude,
                            gps_prev_point.longitude,
                        )
                    elevation_profile.append(
                        [
                            gps_curr_point.longitude,
                            gps_curr_point.latitude,
                            current_length,
                            gps_curr_point.elevation,
                        ]
                    )

                    # statistics:
                    if elevation_min > gps_curr_point.elevation:
                        elevation_min = gps_curr_point.elevation
                    if elevation_max < gps_curr_point.elevation:
                        elevation_max = gps_curr_point.elevation
                    if delta_h is None:
                        delta_h = gps_curr_point.elevation
                    else:
                        delta_h = gps_curr_point.elevation - gps_prev_point.elevation
                        if delta_h > 0:
                            elevation_total_gain += delta_h
                        else:
                            elevation_total_loss -= (
                                delta_h  # keep loss positive/unsigned
                            )

                    gps_prev_point = gpxpy.geo.Location(
                        gps_curr_point.latitude,
                        gps_curr_point.longitude,
                        gps_curr_point.elevation,
                    )

        waypoints = []
        for waypoint in gpx.waypoints:
            point_ele = elevation_data.get_elevation(
                waypoint.latitude, waypoint.longitude, approximate=False
            )
            waypoints.append(
                [
                    waypoint.longitude,
                    waypoint.latitude,
                    True,  # with elevation
                    point_ele,
                    waypoint.symbol,
                    waypoint.name,
                ]
            )

        full_profile = {
            "segments": [{"withEle": True, "points": elevation_profile}],
            "waypoints": waypoints,
            "trackInformation": {
                "length": current_length,
                "minimumAltitude": elevation_min,
                "maximumAltitude": elevation_max,
                "elevationGain": elevation_total_gain,
                "elevationLoss": elevation_total_loss,
            },
        }

        webTrack = WebTrack(webtrack_path, full_profile)


@map_app.route(
    "/middleware/lds/<string:layer>/<string:a_d>/<int:z>/<int:x>/<int:y>",
    methods=("GET",),
)
@same_site
def proxy_lds(layer: str, a_d: str, z: int, x: int, y: int) -> FlaskResponse:
    """
    Tunneling map requests to the LDS servers in order to hide the API key.
    Help using LDS with OpenLayers:
    https://www.linz.govt.nz/data/linz-data-service/guides-and-documentation/using-lds-xyz-services-in-openlayers

    Raises:
        404: in case of LDS error (such as ConnectionError).

    Args:
        layer (str): Tile layer.
        a_d (str): LDS' a, b, c, d subdomains to support more simultaneous tile requests.
        z (int): Z parameter of the XYZ request.
        x (int): X parameter of the XYZ request.
        y (int): Y parameter of the XYZ request.
    """
    url = "https://tiles-{}.data-cdn.linz.govt.nz/services;key={}/tiles/v4/{}/EPSG:3857/{}/{}/{}.png".format(
        escape(a_d), current_app.config["LDS_API_KEY"], escape(layer), z, x, y
    )
    try:
        r = requests.get(url)
    except:
        abort(404)
    return Response(r.content, mimetype="image/png")


@map_app.route("/middleware/ign", methods=("GET",))
@same_site
def proxy_ign() -> FlaskResponse:
    """
    Tunneling map requests to the IGN servers in order to hide the API key.
    Notice: use this routine for OpenLayers and vts_proxy_ign_*() for VTS Browser JS.

    Raises:
        404: in case of IGN error or if the request comes from another website and not in testing mode.
    """
    url = "https://{}:{}@wxs.ign.fr/{}/geoportail/wmts?{}".format(
        current_app.config["IGN"]["username"],
        current_app.config["IGN"]["password"],
        current_app.config["IGN"]["app"],
        secure_decode_query_string(request.query_string),
    )
    try:
        r = requests.get(url)
    except:
        abort(404)
    return Response(r.content, mimetype="image/jpeg")
