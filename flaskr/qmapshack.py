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
Server app for handling data for the customized QMapShack software.
"""

from .db import get_db
from .utils import *
from .visitor_space import add_audit_log
from .vts_proxy import download_bing_metadata

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
