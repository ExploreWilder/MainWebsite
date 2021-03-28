#
# Copyright 2021 Clement
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
App handling the member token for the customized QMapShack software.
The app also forwards map tiles requiring a registered account to third parties
including Thunderforest, Microsoft Bing, LINZ (New Zealand), and IGN (France).
"""

# pylint: disable=invalid-name; allow one letter variables (f.i. x, y, z)
# pylint: disable=line-too-long; allow long URLs

from .db import get_db
from .utils import *
from .visitor_space import add_audit_log
from .vts_proxy import download_bing_metadata

#: IGN parameters used for all IGN layers.
IGN_COMMON_PARAMS = {
    "style": "normal",
    "tilematrixset": "PM",
    "Service": "WMTS",
    "Request": "GetTile",
    "Version": "1.0.0",
    "Format": "image/jpeg",
}

qmapshack_app = Blueprint("qmapshack_app", __name__)
mysql = LocalProxy(get_db)


@qmapshack_app.route("/")
def welcome_page() -> Any:
    """ Welcome page. Find a token to the connected member if existing. """
    token = None
    if actual_access_level() > 0 and "member_id" in session:
        cursor = mysql.cursor()
        cursor.execute(
            """SELECT app_token
            FROM members
            WHERE member_id={member_id}
            AND app_token IS NOT NULL
            AND app_hashed_token IS NOT NULL
            AND access_level>0""".format(
                member_id=int(session["member_id"]),
            )
        )
        member_data = cursor.fetchone()
        token = member_data[0] if member_data else None
    return render_template(
        "welcome_qmapshack.html",
        is_logged="access_level" in session,
        token=token,
        thumbnail_networks=request.url_root + "static/images/qmapshack/overview.png"
    )


@qmapshack_app.route("/token/check", methods=("POST",))
def check_token() -> FlaskResponse:
    """
    Test the hashed token. The request is POST to reduce exposure and
    includes a UUID to use as session token for the next requests.
    The Bing metadata is requested and partially sent back to the user as
    a VTS formatted URL. A new entry in the audit log is added if the
    authentication succeeds. This function is exposed to external
    requests (CSRF exempt).

    Raises:
        400: In case of missing input arguments or bad UUID.
        403: In case of denied access or missing token.
        500: If failed to retreive the Bing metadata.
    """
    if not all(x in request.form for x in ["hashed_token", "uuid"]):
        return "Bad Request", 400
    tested_hash = escape(request.form["hashed_token"])
    tmp_uuid = escape(request.form["uuid"])
    cursor = mysql.cursor()
    cursor.execute(
        """SELECT member_id, username, app_hashed_token
        FROM members
        WHERE app_token IS NOT NULL
        AND app_hashed_token='{hashed_token}'
        AND access_level>0""".format(
            hashed_token=tested_hash,
        )
    )
    member_data = cursor.fetchone()
    if cursor.rowcount == 0 or not member_data:
        return "Bad member", 403

    member_id = member_data[0]
    try:
        cursor.execute(
            """UPDATE members
            SET app_uuid=UNHEX('{tmp_uuid}')
            WHERE member_id={member_id}""".format(
                tmp_uuid=tmp_uuid,
                member_id=member_id,
            )
        )
    except pymysql.err.OperationalError:
        return "Bad UUID", 400
    mysql.commit()

    try:
        url, subdomains = download_bing_metadata(current_app.config["BING_API_KEY"])
    except Exception:  # pylint: disable=broad-except
        return "Bing Error", 500

    result = {
        "success": True,
        "member_id": member_id,
        "username": member_data[1],
        "mapbox_token": current_app.config["MAPBOX_PUB_KEY"],
        "bing_url": url.format(
            subdomain="{alt(" + ",".join(subdomains) + ")}",
            quadkey="{quad(loclod,locx,locy)}",
        ),
    }
    add_audit_log(member_id, request.remote_addr, "app_token_used")
    return jsonify(result)


@qmapshack_app.route("/token/generate", methods=("POST",))
def generate_token() -> FlaskResponse:
    """
    Generate a token and reset the UUID of the connected member.
    The action is logged if successful.
    """
    if "member_id" not in session:
        abort(404)
    member_id = int(session["member_id"])
    token = generate_newsletter_id()
    cursor = mysql.cursor()
    cursor.execute(
        """UPDATE members
        SET app_token='{token}', app_hashed_token='{hashed_token}', app_uuid=NULL
        WHERE member_id={member_id} AND access_level>0""".format(
            token=token,
            hashed_token=hashlib.sha512(token.encode()).hexdigest(),  # unsalted
            member_id=member_id,
        )
    )
    mysql.commit()
    add_audit_log(member_id, request.remote_addr, "app_token_generated")
    return basic_json(True, token)


@qmapshack_app.route("/token/delete", methods=("POST",))
def delete_token() -> FlaskResponse:
    """
    Delete the token and UUID of the connected member.
    The action is logged if successful.
    """
    if "member_id" not in session:
        abort(404)
    member_id = int(session["member_id"])
    cursor = mysql.cursor()
    cursor.execute(
        """UPDATE members
        SET app_token=NULL, app_hashed_token=NULL, app_uuid=NULL
        WHERE member_id={member_id} AND access_level>0""".format(
            member_id=member_id
        )
    )
    mysql.commit()
    add_audit_log(member_id, request.remote_addr, "app_token_deleted")
    return basic_json(True, "Token successfully deleted.")


def is_valid_uuid(uuid: str) -> bool:
    """ Check that the UUID is registered. """
    if not uuid:
        return False
    try:
        cursor = mysql.cursor()
        cursor.execute(
            """SELECT member_id
            FROM members
            WHERE app_uuid=UNHEX('{tmp_uuid}')
            AND access_level>0
            AND app_token IS NOT NULL
            AND app_hashed_token IS NOT NULL""".format(
                tmp_uuid=escape(uuid),
            )
        )
    except pymysql.err.OperationalError:  # pragma: no cover
        return False
    member_data = cursor.fetchone()
    if cursor.rowcount == 0 or not member_data:
        return False
    return True


def valid_app_uuid(view: Any) -> Any:
    """
    Wrapper checking the User Agent and the UUID in the Authorization (Basic) HTTP Raw Header.
    This is used for the QMapShack 2D maps.
    """

    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if request.headers.get("User-Agent") != "QMapShack":
            return "Bad Request", 400
        try:
            http_authorization = request.headers.get("Authorization").split(" ")
            if http_authorization[0] != "Basic":
                return "Bad Request", 400
            _, uuid = base64.b64decode(http_authorization[1]).decode().split(":")
        except Exception:  # pylint: disable=broad-except
            return "Bad Request", 400
        if not is_valid_uuid(uuid):
            return "Bad UUID", 400
        return view(**kwargs)

    return wrapped_view


@qmapshack_app.route(
    "/map/thunderforest/<string:layer>/<int:z>/<int:x>/<int:y>.png",
    methods=("GET",),
)
@valid_app_uuid
def proxy_thunderforest(layer: str, z: int, x: int, y: int) -> FlaskResponse:
    """
    Tunneling map requests to the Thunderforest servers in order to hide the API key.
    Other tile layer URLs: https://manage.thunderforest.com/dashboard

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
    ):
        return tile_not_found(mimetype)  # pragma: no cover
    url = "https://tile.thunderforest.com/{}/{}/{}/{}.png?apikey={}".format(
        layer, z, x, y, current_app.config["THUNDERFOREST_API_KEY"]
    )
    try:
        r = requests.get(url)
        r.raise_for_status()  # raise for not found tiles
    except requests.exceptions.HTTPError:  # pragma: no cover
        return tile_not_found(mimetype)
    return Response(r.content, mimetype=mimetype)


@qmapshack_app.route(
    "/map/fr/<string:layer>/<int:z>/<int:x>/<int:y>.jpg",
    methods=("GET",),
)
@valid_app_uuid
def proxy_ign_auth_http_header(layer: str, z: int, x: int, y: int) -> FlaskResponse:
    """
    Tunneling map requests to the IGN servers in order to hide the API key.
    The QMapShack map (2D) is configurable with the HTTP Raw Header (Authorization).
    """
    layer = escape(layer)
    mimetype = "image/jpeg"
    if layer == "satellite":
        layer = "ORTHOIMAGERY.ORTHOPHOTOS"
    elif layer == "topo":
        layer = "GEOGRAPHICALGRIDSYSTEMS.MAPS"
    else:
        return tile_not_found(mimetype)  # pragma: no cover

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


@qmapshack_app.route(
    "/3d/map/fr/satellite/<int:z>/<int:x>/<int:y>.jpg",
    methods=("GET",),
)
def proxy_ign_auth_url(z: int, x: int, y: int) -> FlaskResponse:
    """
    Tunneling map requests to the IGN servers in order to hide the API key.
    The VTS Browser CPP (3D) is configurable with the URL in the mapConfig.
    The 3D map is used for terrain analysis, so only the satellite layer is displayed.
    """
    mimetype = "image/jpeg"
    uuid = request.args.get("access_token", "")
    if not uuid:
        return "Bad Request", 400
    if not is_valid_uuid(uuid):
        return "Bad UUID", 400
    url = "https://{}:{}@wxs.ign.fr/{}/geoportail/wmts?layer={}&{}&TileMatrix={}&TileCol={}&TileRow={}".format(
        current_app.config["IGN"]["username"],
        current_app.config["IGN"]["password"],
        current_app.config["IGN"]["app"],
        "ORTHOIMAGERY.ORTHOPHOTOS",
        params_urlencode(IGN_COMMON_PARAMS),
        z,
        x,
        y,
    )
    try:
        r = requests.get(url, timeout=12)
        r.raise_for_status()
    except requests.exceptions.HTTPError:  # pragma: no cover
        return tile_not_found(mimetype)
    return Response(r.content, mimetype=mimetype)


@qmapshack_app.route(
    "/map/nz/<string:layer>/<int:z>/<int:x>/<int:y>.<string:file_format>",
    methods=("GET",),
)
@valid_app_uuid
def proxy_lds(layer: str, z: int, x: int, y: int, file_format: str) -> FlaskResponse:
    """
    Tunneling map requests to the LINZ servers in order to hide the API key.
    Help using LINZ with OpenLayers:
    https://www.linz.govt.nz/data/linz-data-service/guides-and-documentation/using-lds-xyz-services-in-openlayers

    Notes:
        WebP format currently not handled by the software.

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
        url = "https://tiles-{}.data-cdn.linz.govt.nz/services;key={}/tiles/v4/{}/EPSG:3857/{}/{}/{}.png".format(
            "d",
            current_app.config["LINZ_API_KEYS"]["lds"],
            "layer=767",
            z,
            x,
            y,
        )
    else:
        return tile_not_found(mimetype)  # pragma: no cover

    try:
        r = requests.get(url)
        r.raise_for_status()  # raise for not found tiles
    except requests.exceptions.HTTPError:  # pragma: no cover
        return tile_not_found(mimetype)
    return Response(r.content, mimetype=mimetype)
