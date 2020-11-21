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

"""
Map-related functions and routes.
For the complete mapproxy, refer to vts_proxy.py
"""

# pylint: disable=invalid-name; allow one letter variables (f.i. x, y, z)

import gpxpy
import gpxpy.gpx
import srtm

from .db import get_db
from .gpx_to_img import gpx_to_src
from .utils import *
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


def get_thumbnail_path(book_id: int, gpx_name: str) -> str:
    """
    Returns the path to the thumbnail file.

    Example:
        'map/static_map/42/super_track.jpg'
    """
    return "map/static_map/" + "/".join([str(book_id), gpx_name]) + ".jpg"


@map_app.route(
    "/viewer/<int:book_id>/<string:book_url>/<string:gpx_name>/<string:country>"
)
@map_app.route(
    "/player/<int:book_id>/<string:book_url>/<string:gpx_name>/<string:country>"
)
def map_viewer(book_id: int, book_url: str, gpx_name: str, country: str) -> Any:
    """
    - *viewer:* 2D map viewer.
                With some basic tools, track and topo information.
    - *player:* 3D map viewer.
                With a real 3D map more focused on a fun user experience
                than a hiker-centric track viewer.

    A track is always linked to a story and the navbar would display breadcrumbs
    and a link to the alternative version (2D/3D). The path to the map configuration
    is in the Jinja template.

    Args:
        book_id (int): Book ID based on the 'shelf' database table.
        book_url (str): Book URL based on the 'shelf' database table.
        gpx_name (str): Name of the GPX file in the /tracks directory WITHOUT file extension. NOT USED.
        country (str): Country code (f.i. "nz".)

    Raises:
        404: in case of denied access.
    """
    if "/player/" in request.path:
        map_type, alt_map_type = "player", "viewer"
    else:
        map_type, alt_map_type = "viewer", "player"
    try:
        gpx_exporter = GpxExporter(book_id, gpx_name, book_name=book_url)
    except (LookupError, PermissionError, FileNotFoundError):
        abort(404)
    book_url = escape(book_url)
    gpx_name = escape(gpx_name)
    country_code = escape(country)
    country_code_up = country_code.upper()
    if country_code_up not in current_app.config["MAP_LAYERS"]:
        abort(404)
    if actual_access_level() >= current_app.config["ACCESS_LEVEL_DOWNLOAD_GPX"]:
        gpx_download_path = gpx_exporter.get_gpx_download_path()
    else:
        gpx_download_path = ""
    return render_template(
        "map_" + map_type + ".html",
        country=country_code_up,
        header_breadcrumbs=track_path_to_header(
            book_id, book_url, gpx_exporter.get_book_title(), gpx_name
        ),
        url_alt_map="/".join(
            ["/map", alt_map_type, str(book_id), book_url, gpx_name, country_code]
        ),
        gpx_download_path=gpx_download_path,
        thumbnail_networks=request.url_root + get_thumbnail_path(book_id, gpx_name),
        total_subscribers=total_subscribers(mysql.cursor()),
        is_prod=not current_app.config["DEBUG"],
    )


def create_static_map(
    gpx_path: str, static_map_path: str, static_image_settings: Dict
) -> None:
    """
    Create a URL based on the `gpx_path` GPX file and the `static_image_settings` configuration.
    The URL is then fetched to the Mapbox server to retrieve a JPG image.

    .. note::
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
    r.raise_for_status()
    with open(static_map_path, "wb") as static_image:
        static_image.write(r.content)


class GpxExporter:
    """ Handle a GPX file and the export. """

    def __init__(self, book_id: int, gpx_name: str, **kwargs: str):
        """
        Check if the `book_id` and the `gpx_name` exist and accessible based on
        the user access level.

        .. note::
            Some raised exceptions might be intentionally unhandled in order
            to alert the unexpected error (with Sentry).

        Args:
            book_id (int): Book ID based on the 'shelf' database table.
            gpx_name (str): Name of the GPX file WITHOUT file extension.

        Keyword Args:
            export_ext (str): Replace the gpx extension to this extension WITHOUT ``.``.
            book_name (str): Book name based on the 'shelf' database table.

        Raises:
            LookupError: `book_id` not in the database
            PermissionError: Access denied
            FileNotFoundError: GPX file not in the shelf
            EOFError: GPX file is empty
        """
        self.gpx_filename: str = secure_filename(escape(gpx_name) + ".gpx")
        self.export_file: Optional[str] = (
            replace_extension(self.gpx_filename, kwargs["export_ext"])
            if "export_ext" in kwargs
            else None
        )

        cursor = mysql.cursor()
        query = f"""SELECT access_level, url, title
                FROM shelf
                WHERE book_id={book_id}"""
        if "book_name" in kwargs:
            query += f""" AND url='{kwargs["book_name"]}'"""
        cursor.execute(query)
        data = cursor.fetchone()
        if cursor.rowcount == 0:
            raise LookupError("Book not found in the database")
        if actual_access_level() < data[0]:
            raise PermissionError("Access denied")

        self.gpx_dir = os.path.join(
            current_app.config["SHELF_FOLDER"], secure_filename(data[1])
        )
        self.gpx_path = os.path.join(self.gpx_dir, self.gpx_filename)

        if not os.path.isfile(self.gpx_path):
            raise FileNotFoundError("GPX file not in the shelf")
        if os.stat(self.gpx_path).st_size == 0:
            raise EOFError("GPX file is empty")

        self.export_path = (
            os.path.join(self.gpx_dir, self.export_file)
            if self.export_file is not None
            else None
        )
        self.book_id = book_id
        self.book_title = data[2]

    def get_book_title(self) -> str:
        """ Returns the book title. """
        return self.book_title

    def get_gpx_path(self) -> str:
        """ Returns the GPX path and filename. """
        return self.gpx_path

    def get_export_path(self) -> str:
        """
        Returns the export path and filename or none if not set.

        Raises:
            ValueError: if the export path is not set.
        """
        if self.export_path is None:
            raise ValueError("Undefined export path")  # pragma: no cover; misuse
        return self.export_path

    def should_update_export(self) -> bool:
        """
        Returns true if the export file should be (re-)generated.

        Raises:
            ValueError: if the export path is not set.
        """
        if self.export_path is None:
            raise ValueError("Undefined export path")  # pragma: no cover; misuse
        return (
            not os.path.isfile(self.export_path)
            or os.stat(self.export_path).st_size == 0
            or os.stat(self.export_path).st_mtime < os.stat(self.gpx_path).st_mtime
        )

    def get_gpx_download_path(self) -> str:
        """
        Returns the real path to the GPX file.

        Returns:
            str: For example '/stories/42/super_track.gpx'
        """
        return "/".join(["/stories", str(self.book_id), self.gpx_filename])

    def export(self, export_mimetype: str) -> FlaskResponse:
        """
        Returns the export file with the right MIME type.

        Args:
            export_mimetype (str): MIME type of the export file.

        Raises:
            ValueError: if the export file is not set.
        """
        if self.export_file is None:
            raise ValueError("Undefined export file")  # pragma: no cover; misuse
        return send_from_directory(
            self.gpx_dir,
            self.export_file,
            mimetype=export_mimetype,
        )


@map_app.route("/static_map/<int:book_id>/<string:gpx_name>.jpg")
def static_map(book_id: int, gpx_name: str) -> FlaskResponse:
    """
    Print a static map and create it if not already existing or not up to date.
    Keep this route open to external requests since it's used as thumbnail for the social platforms.

    Args:
        book_id (int): Book ID based on the 'shelf' database table.
        gpx_name (str): Name of the GPX file WITHOUT file extension.

    Returns:
        JPG image or a 404/500 HTTP error.

    Raises:
        404: Permission error or GPX file not found.
    """
    try:
        gpx_exporter = GpxExporter(book_id, gpx_name, export_ext="gpx_static_map.jpg")
    except (LookupError, PermissionError, FileNotFoundError):
        abort(404)
    if gpx_exporter.should_update_export():
        create_static_map(
            gpx_exporter.get_gpx_path(),
            gpx_exporter.get_export_path(),
            current_app.config["MAPBOX_STATIC_IMAGES"],
        )
    return gpx_exporter.export("image/jpeg")


@map_app.route("/geojsons/<int:book_id>/<string:gpx_name>.geojson")
@same_site
def simplified_geojson(book_id: int, gpx_name: str) -> FlaskResponse:
    """
    Simplify a GPX file, convert to GeoJSON and send it.
    The generated GeoJSON is cached.

    Args:
        book_id (int): Book ID based on the 'shelf' database table.
        gpx_name (str): Name of the GPX file WITHOUT file extension.

    Returns:
        JSON file containing the profile and statistics or a 404/500 HTTP error.

    Raises:
        404: Permission error or GPX file not found.
    """
    try:
        gpx_exporter = GpxExporter(book_id, gpx_name, export_ext="geojson")
    except (LookupError, PermissionError, FileNotFoundError):
        abort(404)
    if gpx_exporter.should_update_export():
        with open(gpx_exporter.get_export_path(), "w") as geojson_file:
            geojson_file.write(gpx_to_simplified_geojson(gpx_exporter.get_gpx_path()))
    return gpx_exporter.export("application/geo+json")


@map_app.route("/webtracks/<int:book_id>/<string:gpx_name>.webtrack")
@same_site
def webtrack_file(book_id: int, gpx_name: str) -> FlaskResponse:
    """
    Send a WebTrack file and create it if not already existing or not up to date.

    Args:
        book_id (int): Book ID based on the 'shelf' database table.
        gpx_name (str): Name of the GPX file in the /tracks directory WITHOUT file extension.

    Returns:
        The WebTrack file or a 404/500 HTTP error.

    Raises:
        404: Permission error or GPX file not found.
    """
    try:
        gpx_exporter = GpxExporter(book_id, gpx_name, export_ext="webtrack")
    except (LookupError, PermissionError, FileNotFoundError):
        abort(404)
    if gpx_exporter.should_update_export() or not good_webtrack_version(
        gpx_exporter.get_export_path()
    ):
        gpx_to_webtrack_with_elevation(
            gpx_exporter.get_gpx_path(),
            gpx_exporter.get_export_path(),
            current_app.config["NASA_EARTHDATA"],
        )
    return gpx_exporter.export("application/prs.webtrack")


def good_webtrack_version(file_path: str) -> bool:
    """
    Check that the WebTrack format version of `file_path` can
    be handled by the WebTrack module. Only the file header is
    checked in order to speed up the verification process.
    A partially corrupted file may pass the test.

    Args:
        file_path (str): Path the the WebTrack file.

    Returns:
        False if the WebTrack module cannot handle the file.
        True otherwise.
    """
    webtrack = WebTrack()
    current_format = webtrack.get_format_information()
    file_format = webtrack.get_format_information(file_path)
    return current_format == file_format


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
            os.makedirs(result)  # pragma: no cover

        return result


def gpx_to_webtrack_with_elevation(
    gpx_path: str, webtrack_path: str, credentials: Dict[str, str]
) -> None:
    """
    Find out the elevation profile of ``gpx_path`` thanks to SRTM data
    version 3.0 with 1-arc-second for the whole world and save the result
    into ``webtrack_path`` which is overwritten if already existing.

    SRTM data are stored in the folder specified in CustomFileHandler().get_srtm_dir()

    * Data source: https://e4ftl01.cr.usgs.gov/MEASURES/SRTMGL1.003/
    * Also: https://lpdaac.usgs.gov/products/srtmgl1v003/

    .. note::
        In case of USGS.gov server error, you should see a notification banner in:
        https://lpdaac.usgs.gov/products/srtmgl1v003/
        such as `LP DAAC websites and HTTP downloads will be unavailable...`

    .. note::
        SRTMGL1.003 data requires user authentication through the NASA Earthdata Login.

    .. note::
        GPX tracks and segments are merged and only one WebTrack segment is created
        because the GPX track is a *one go* tramping trip.

    How to use gpxpy: https://github.com/tkrajina/gpxpy

    How to use SRTM.py: https://github.com/nawagers/srtm.py/tree/EarthDataLogin

    Args:
        gpx_path (str): Secured path to the input file.
        webtrack_path (str): Secured path to the overwritten output file.
        credentials (Dict[str, str]): NASA credentials.

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
                    if gps_curr_point.elevation is None:
                        raise ValueError("Expected elevation to be known.")
                    if elevation_min > gps_curr_point.elevation:  # type: ignore[operator]
                        elevation_min = gps_curr_point.elevation  # type: ignore[assignment]
                    if elevation_max < gps_curr_point.elevation:  # type: ignore[operator]
                        elevation_max = gps_curr_point.elevation  # type: ignore[assignment]
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

        webtrack = WebTrack()
        webtrack.to_file(webtrack_path, full_profile)


def gpx_to_simplified_geojson(gpx_path: str) -> str:
    """
    Create a GeoJSON string based on the GPX file ``gpx_path``.
    A GPX trk with multiple trkseg is converted into a GeoJSON
    MultiLineString, otherwise the trk is a GeoJSON LineString.
    The GeoJSON is a FeatureCollection combining MultiLineStrings
    and LineStrings.

    .. note::
        Tracks are gathered in a GeoJSON FeatureCollection instead of a
        GeometryCollection for a safer future (a probably richer
        GeoJSON string without changing the container type).

    .. note::
        * Waypoints are excluded.
        * Elevation data are excluded.
        * Track names and and similar meta-data are excluded.
        * Timestamps are excluded.
        * Floating points are reduced to 4 digits (handheld GPS accuracy, 11m at equator).
        * Tracks are simplified with the Ramer-Douglas-Peucker algorithm.

    Args:
        gpx_path (str): Secured path to the input file.

    Returns:
        str: A GeoJSON string ready to be saved into a file and/or sent.
    """
    with open(gpx_path, "r") as input_gpx_file:
        gpx = gpxpy.parse(input_gpx_file)
    gpx.simplify()
    str_geo = '{"type":"FeatureCollection","features":['
    for track in gpx.tracks:
        is_multiline = len(track.segments) > 1
        str_geo += '{"type":"Feature","properties":{},"geometry":{"type":'
        str_geo += '"MultiLineString"' if is_multiline else '"LineString"'
        str_geo += ',"coordinates":'
        if is_multiline:
            str_geo += "["
        for segment in track.segments:
            str_geo += "["
            for gps_point in segment.points:
                lon = str(round(gps_point.longitude, 4))
                lat = str(round(gps_point.latitude, 4))
                str_geo += "[" + lon + "," + lat + "],"
            str_geo = str_geo[:-1] + "],"  # remove the last ,
        if is_multiline:
            str_geo = str_geo[:-1] + "],"
        str_geo = str_geo[:-1] + "}},"
    return str_geo[:-1] + "]}"


@map_app.route(
    "/middleware/lds/<string:layer>/<string:a_d>/<int:z>/<int:x>/<int:y>",
    methods=("GET",),
)
@same_site
def proxy_lds(layer: str, a_d: str, z: int, x: int, y: int) -> FlaskResponse:
    """
    Tunneling map requests to the LDS servers in order to hide the API key. `Help using LDS with OpenLayers
    <https://www.linz.govt.nz/data/linz-data-service/guides-and-documentation/using-lds-xyz-services-in-openlayers>`_.

    Raises:
        404: in case of LDS error (such as ConnectionError).

    Args:
        layer (str): Tile layer.
        a_d (str): LDS' a, b, c, d subdomains to support more simultaneous tile requests.
        z (int): Z parameter of the XYZ request.
        x (int): X parameter of the XYZ request.
        y (int): Y parameter of the XYZ request.
    """
    mimetype = "image/png"
    url = "https://tiles-{}.data-cdn.linz.govt.nz/services;key={}/tiles/v4/{}/EPSG:3857/{}/{}/{}.png".format(
        escape(a_d), current_app.config["LDS_API_KEY"], escape(layer), z, x, y
    )
    try:
        r = requests.get(url)
        r.raise_for_status()  # raise for not found tiles
    except requests.exceptions.HTTPError:  # pragma: no cover
        return tile_not_found(mimetype)
    return Response(r.content, mimetype=mimetype)


@map_app.route("/middleware/ign", methods=("GET",))
@same_site
def proxy_ign() -> FlaskResponse:
    """
    Tunneling map requests to the IGN servers in order to hide the API key.
    Notice: use this routine for OpenLayers and vts_proxy_ign_*() for VTS Browser JS.

    Raises:
        404: in case of IGN error or if the request comes from another website and not in testing mode.
    """
    mimetype = "image/jpeg"
    url = "https://{}:{}@wxs.ign.fr/{}/geoportail/wmts?{}".format(
        current_app.config["IGN"]["username"],
        current_app.config["IGN"]["password"],
        current_app.config["IGN"]["app"],
        secure_decode_query_string(request.query_string),
    )
    try:
        r = requests.get(url)
        r.raise_for_status()  # raise for not found tiles
    except requests.exceptions.HTTPError:  # pragma: no cover
        return tile_not_found(mimetype)
    return Response(r.content, mimetype=mimetype)
