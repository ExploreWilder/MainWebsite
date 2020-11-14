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

import time

from flask import session

from flaskr.db import get_db


def test_failed_login(client, auth, app):
    """ Make sure failed login connections work, anti-bruteforce and log as well. """
    # test untick box:
    rv = client.post(
        "/login",
        data=dict(
            email="wrongemail@test.com",
            password="test-bad-password",
            captcha="empty",
            copyrightNotice=True,
        ),
        follow_redirects=True,
    )
    assert b"Missing data" in rv.data
    time.sleep(2)
    # test email format:
    rv = auth.login("wrongemailtest.com", "user")
    assert b"Bad email address format" in rv.data
    # test wrong email address:
    time.sleep(2)
    rv = auth.login("wrongemail@test.com", "user")
    assert b"Wrong email address or password" in rv.data
    # test bruteforce:
    rv = auth.login("user@test.com", "test-bad-password")
    assert b"Wrong email address or password" not in rv.data
    assert b"Too many attempts" in rv.data
    # test bad password:
    time.sleep(2)
    rv = auth.login("user@test.com", "test-bad-password")
    assert b"Wrong email address or password" in rv.data
    # test good username and password:
    time.sleep(2)

    with app.app_context():
        cursor = get_db().cursor()
        cursor.execute("SELECT * FROM members_audit_log")
        cursor.fetchone()
        assert cursor.rowcount == 0  # empty table


def test_successful_login_logout(client, auth, app):
    """ Make sure login and logout work, log as well. """
    rv = auth.login("user@test.com", "user")
    assert b"animated-full-screen" in rv.data
    with client:
        client.get("/", follow_redirects=True)
        assert session["username"] == "test-user"
        assert session["access_level"] == 190
        assert session["member_id"] == 2
        assert session["email"] == "user@test.com"

    with app.app_context():
        cursor = get_db().cursor()
        cursor.execute(
            "SELECT member_id FROM members_audit_log WHERE event_description='logged_in'"
        )
        entry = cursor.fetchone()
        assert entry[0] == 2  # successful connection logged

    # test logout:
    rv = auth.logout()
    assert b"You are logged out" in rv.data
    with client:
        client.get("/", follow_redirects=True)
        assert "username" not in session
        assert "access_level" not in session
        assert "member_id" not in session
        assert "email" not in session
