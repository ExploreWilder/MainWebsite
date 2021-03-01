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

import hashlib

import pytest
from flask import json

from flaskr.db import get_db


def test_welcome_page(client, auth):
    """ Check that the page is reachable and displays a login button or token section. """
    rv = client.get("/qmapshack/")
    assert rv.status_code == 200 and b"please sign in" in rv.data

    auth.login()
    rv = client.get("/qmapshack/")
    assert rv.status_code == 200 and b"Your Token:" in rv.data
    assert b'value="none"' not in rv.data


def test_generate_check_delete_token(client, auth, app):
    """ Test token manipulation. """
    with app.app_context():
        cursor = get_db().cursor()
        rv = client.get("/qmapshack/token/generate", follow_redirects=True)
        assert rv.status_code == 404 or b"Password required" in rv.data

        auth.login()
        rv = client.get("/qmapshack/token/generate", follow_redirects=True)
        assert rv.status_code == 404 or b"Password required" in rv.data

        rv = client.post("/qmapshack/token/generate")
        assert rv.status_code == 200
        returned_json = json.loads(rv.data)
        assert returned_json["success"]
        token = returned_json["info"]
        cursor.execute(
            "SELECT member_id FROM members_audit_log WHERE event_description='app_token_generated'"
        )
        entry = cursor.fetchone()
        assert entry[0] == 2

        rv = client.get("/qmapshack/")
        assert token.encode() in rv.data

        rv = client.post("/qmapshack/token/check")
        assert rv.status_code == 400

        rv = client.post(
            "/qmapshack/token/check", data=dict(hashed_token="abc", uuid="xyz")
        )
        assert rv.status_code == 403

        hashed_token = hashlib.sha512(token.encode()).hexdigest()
        rv = client.post(
            "/qmapshack/token/check", data=dict(hashed_token=hashed_token, uuid="xyz")
        )
        assert rv.status_code == 400 and b"Bad UUID" in rv.data

        rv = client.post(
            "/qmapshack/token/check", data=dict(hashed_token=hashed_token, uuid="fe3a")
        )
        assert rv.status_code == 200
        returned_json = json.loads(rv.data)
        assert returned_json["success"]
        assert (
            returned_json["member_id"] == 2 and returned_json["username"] == "test-user"
        )
        assert returned_json["bing_url"].startswith("https://")

        rv = client.post("/qmapshack/token/generate")
        assert token.encode() not in rv.data
        assert json.loads(rv.data)["info"].encode() in rv.data
        cursor.execute(
            "SELECT member_id FROM members_audit_log WHERE event_description='app_token_generated'"
        )
        entry = cursor.fetchall()
        assert cursor.rowcount == 2

        rv = client.post("/qmapshack/token/delete")
        assert b'value="none"' not in rv.data
        cursor.execute(
            "SELECT member_id FROM members_audit_log WHERE event_description='app_token_deleted'"
        )
        entry = cursor.fetchone()
        assert entry[0] == 2
