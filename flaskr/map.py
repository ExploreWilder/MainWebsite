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

from .utils import *
from .db import get_db
from .gpx_to_img import gpx_to_src
import srtm, gpxpy, gpxpy.gpx, pyproj, lzstring

map_app = Blueprint("map_app", __name__)
mysql = LocalProxy(get_db)

@map_app.route("/viewer/<int:book_id>/<string:book_url>/<string:gpx_name>/<string:country>")
def map_viewer(book_id, book_url, gpx_name, country):
    """
    Map viewer.

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
    cursor.execute("""SELECT access_level
        FROM shelf
        WHERE book_id={book_id} AND url='{book_url}'""".format(
            book_id=book_id,
            book_url=book_url))
    data = cursor.fetchone()
    country_code = escape(country).upper()
    if cursor.rowcount == 0 \
        or actual_access_level() < data[0] \
        or not country_code in current_app.config["MAP_LAYERS"]:
        abort(404)
    return render_template(
        "map_viewer.html",
        country=country_code,
        gpx_download_path="/books/" + str(book_id) + "/" + book_url + "/" + gpx_name + ".gpx" if actual_access_level() >= current_app.config["ACCESS_LEVEL_DOWNLOAD_GPX"] else "",
        is_prod=not current_app.config["DEBUG"])

def create_static_map(gpx_path, static_map_path, static_image_settings):
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
def static_map(book_id, book_url, gpx_name):
    """
    Print a static map and create it if not already existing or not up to date.

    Args:
        book_id (int): Book ID based on the 'shelf' database table.
        book_url (str): Book URL based on the 'shelf' database table.
        gpx_name (str): Name of the GPX file in the /tracks directory WITHOUT file extension.

    Returns:
        JPG image.

    Raises:
        404: if the request comes from another website and not in testing mode.
        500: failed to create the image.
    """
    if not is_same_site() and not (current_app.config["TESTING"] or current_app.config["DEBUG"]):
        abort(404)
    book_url = escape(book_url)
    cursor = mysql.cursor()
    cursor.execute("""SELECT access_level
        FROM shelf
        WHERE book_id={book_id} AND url='{book_url}'""".format(
            book_id=book_id,
            book_url=book_url))
    data = cursor.fetchone()
    if cursor.rowcount == 0 or actual_access_level() < data[0]:
        abort(404)
    gpx_filename = secure_filename(escape(gpx_name) + ".gpx")
    gpx_dir = os.path.join(current_app.config["SHELF_FOLDER"], secure_filename(book_url))
    gpx_path = os.path.join(gpx_dir, gpx_filename)
    append_ext = "_static_map.jpg"
    static_map_path = gpx_path + append_ext
    if not os.path.isfile(static_map_path) \
        or os.stat(static_map_path).st_size == 0 \
        or os.stat(static_map_path).st_mtime < os.stat(gpx_path).st_mtime: # update profile
        try:
            create_static_map(gpx_path, static_map_path, current_app.config["MAPBOX_STATIC_IMAGES"])
        except Exception as e:
            return "{}".format(type(e).__name__), 500
    return send_from_directory(gpx_dir, gpx_filename + append_ext)

@map_app.route("/profile/<int:book_id>/<string:book_url>/<string:gpx_name>/<string:country>")
def profile_file(book_id, book_url, gpx_name, country):
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
    if not is_same_site() and not (current_app.config["TESTING"] or current_app.config["DEBUG"]):
        abort(404)
    book_url = escape(book_url)
    cursor = mysql.cursor()
    cursor.execute("""SELECT access_level
        FROM shelf
        WHERE book_id={book_id} AND url='{book_url}'""".format(
            book_id=book_id,
            book_url=book_url))
    data = cursor.fetchone()
    if cursor.rowcount == 0 or actual_access_level() < data[0]:
        abort(404)
    gpx_filename = secure_filename(escape(gpx_name) + ".gpx")
    gpx_dir = os.path.join(current_app.config["SHELF_FOLDER"], secure_filename(book_url))
    gpx_path = os.path.join(gpx_dir, gpx_filename)
    profile_path = gpx_path + "_profile.bin"
    if not os.path.isfile(profile_path) \
        or os.stat(profile_path).st_size == 0 \
        or os.stat(profile_path).st_mtime < os.stat(gpx_path).st_mtime: # update profile
        try:
            elevation_profile(gpx_path, profile_path, current_app.config["NASA_EARTHDATA"])
        except Exception as e:
            return "{}".format(type(e).__name__), 500
    return send_from_directory(gpx_dir, gpx_filename + "_profile.bin")

class CustomFileHandler(srtm.data.FileHandler):
    """
    The custom file handler to choose the cache directory.
    https://github.com/ExploreWilder/srtm.py/blob/EarthDataLogin/srtm/data.py
    """

    def get_srtm_dir(self):
        """ The default path to store files. """
        # Local cache path:
        result = absolute_path("../srtm_cache")

        if not os.path.exists(result):
            os.makedirs(result)

        return result

def elevation_profile(gpx_path, profile_path, credentials):
    """
    Find out the elevation profile of ``gpx_path`` thanks to SRTM data
    version 3.0 with 1-arc-second for the whole world and save the result
    into ``profile_path`` which is overwritten if already existing.
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
        profile_path (str): Secured path to the overwritten output file.
    
    Returns:
        dict:
        Elements of the elevation profile are:

        * Height (aka elevation) in m,
        * Distance from the beginning in km rounded with 2 digits,
        * X coordinate in the Web Mercator projection (EPSG:3857),
        * Y coordinate in the Web Mercator projection (EPSG:3857).

        Also, do some statistics:

        * Total length in km,
        * Minimum altitude in m,
        * Maximum altitude in m,
        * Total elevation gain in m,
        * Total elevation loss in m (negative).
    """
    elevation_data = srtm.data.GeoElevationData(
        version='v3.1a',
        EDuser=credentials["username"],
        EDpass=credentials["password"],
        file_handler=CustomFileHandler())
    print(elevation_data.file_handler)
    with open(gpx_path, "r") as input_gpx_file:
        gpx = gpxpy.parse(input_gpx_file)
        elevation_data.add_elevations(gpx, smooth=True)
        elevation_profile = []
        elevation_min = 10000
        elevation_max = -elevation_min
        elevation_total_gain = 0
        elevation_total_loss = 0
        delta_h = None
        current_length = 0
        proj_transformer = pyproj.Transformer.from_crs('epsg:4326', 'epsg:3857')
        i = 0
        for track in gpx.tracks:
            for segment in track.segments:
                for point in segment.points:
                    if delta_h is not None:
                        current_length += gpxpy.geo.haversine_distance(
                            point.latitude,
                            point.longitude,
                            location.latitude,
                            location.longitude)
                    web_point = proj_transformer.transform(point.latitude, point.longitude)
                    elevation_profile.append([
                        int(point.elevation),
                        round(float(current_length) / 1000., 2),
                        int(web_point[0]) + 485 - i * 30, # slight obfuscation
                        int(web_point[1]) + 1567])
                    if elevation_min > point.elevation:
                        elevation_min = point.elevation
                    if elevation_max < point.elevation:
                        elevation_max = point.elevation
                    if delta_h is None:
                        delta_h = point.elevation
                    else:
                        delta_h = point.elevation - location.elevation
                        if delta_h > 0:
                            elevation_total_gain += delta_h
                        else:
                            elevation_total_loss += delta_h
                    location = gpxpy.geo.Location(point.latitude, point.longitude, point.elevation)
                    i += 1
        waypoints = []
        for waypoint in gpx.waypoints:
            web_point = proj_transformer.transform(waypoint.latitude, waypoint.longitude)
            waypoints.append([waypoint.name, waypoint.symbol, int(web_point[0]), int(web_point[1])])
        full_profile = {
            "profile": elevation_profile,
            "waypoints": waypoints,
            "statistics": {
                "totalLength": round(float(current_length) / 1000., 2),
                "minimumAltitude": int(elevation_min),
                "maximumAltitude": int(elevation_max),
                "totalElevationGain": int(elevation_total_gain),
                "totalElevationLoss": int(elevation_total_loss)}}
        with open(profile_path, "wb") as profile_file:
            x = lzstring.LZString()
            compressed_data = x.compressToUint8Array(json.dumps(full_profile))
            # the JavaScript decompression require an even number of bytes
            profile_file.write(compressed_data + (b"=" if (len(compressed_data) % 2) else b""))

@map_app.route("/middleware/lds/<string:layer>/<string:a_d>/<int:z>/<int:x>/<int:y>", methods=("GET",))
def middleware_lds(layer, a_d, z, x, y):
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
    if not is_same_site() and not (current_app.config["TESTING"] or current_app.config["DEBUG"]):
        abort(404)
    url = "https://tiles-{}.data-cdn.linz.govt.nz/services;key={}/tiles/v4/{}/EPSG:3857/{}/{}/{}.png".format(
        escape(a_d), current_app.config["LDS_API_KEY"], escape(layer), z, x, y)
    try:
        r = requests.get(url)
    except:
        abort(404)
    return r.content

@map_app.route("/middleware/ign", methods=("GET",))
def middleware_ign():
    """
    Tunneling map requests to the IGN servers in order to hide the API key.

    Raises:
        404: in case of IGN error or if the request comes from another website and not in testing mode.
    """
    if not is_same_site() and not (current_app.config["TESTING"] or current_app.config["DEBUG"]):
        abort(404)
    url = "https://{}:{}@wxs.ign.fr/{}/geoportail/wmts?{}".format(
        current_app.config["IGN"]["username"],
        current_app.config["IGN"]["password"],
        current_app.config["IGN"]["app"],
        secure_decode_query_string(request.query_string))
    try:
        r = requests.get(url)
    except:
        abort(404)
    return r.content

@map_app.route("/middleware/topografisk/<int:z>/<int:x>/<int:y>", methods=("GET",))
def middleware_topografisk(z, x, y):
    """
    Tunneling map requests to the Kartverket servers (Norway) in order to respect users' privacy.
    Howto available here: https://kartverket.no/en/data/lage-kart-pa-nett/

    Raises:
        404: in case of server error or if the request comes from another website and not in testing mode.

    Args:
        z (int): Z parameter of the XYZ request.
        x (int): X parameter of the XYZ request.
        y (int): Y parameter of the XYZ request.
    """
    if not is_same_site() and not (current_app.config["TESTING"] or current_app.config["DEBUG"]):
        abort(404)
    url = "https://opencache.statkart.no/gatekeeper/gk/gk.open_gmaps?layers=topo4&zoom={}&x={}&y={}".format(
        z, x, y)
    try:
        r = requests.get(url)
    except:
        abort(404)
    return r.content

@map_app.route("/middleware/canvec", methods=("GET",))
def middleware_canvec():
    """
    Tunneling map requests to the Geogratis servers (Canada) in order to respect users' privacy.

    Raises:
        404: in case of server error or if the request comes from another website and not in testing mode.
    """
    if not is_same_site() and not (current_app.config["TESTING"] or current_app.config["DEBUG"]):
        abort(404)
    url = "http://maps.geogratis.gc.ca/wms/canvec_en?{}".format(
        secure_decode_query_string(request.query_string))
    try:
        r = requests.get(url)
    except:
        abort(404)
    return r.content
