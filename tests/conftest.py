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

import os
import shutil
from shutil import copyfile

import pytest

from flaskr import create_app
from flaskr import db


@pytest.fixture(scope="session")
def files():
    """ This client fixture will be called once. """
    app = create_app(True)

    with app.app_context():
        db.init_db()
        db.load_from_file(
            open(os.path.join(os.path.dirname(__file__), "data.sql"), "rb")
        )
        directories = []

        # Create the files referred by the database
        cursor = db.get_db().cursor()
        cursor.execute(
            """SELECT thumbnail_src, photo_m_src, photo_l_src, raw_src
            FROM gallery"""
        )
        data = cursor.fetchall()
        for picture in data:
            for src in picture:
                try:
                    os.mknod(os.path.join("../photos", src))
                except:
                    pass

        # Create files in books - see test_links.py
        try:
            os.mknod(os.path.join("../books", "locked.jpg"))
        except:
            pass

        # Create stories based on the testing database
        cursor.execute(
            """SELECT url, file_name
            FROM shelf"""
        )
        data = cursor.fetchall()
        for book in data:
            try:
                new_dir = os.path.join("../books", book[0])
                directories.append(new_dir)
                os.mkdir(new_dir)
                os.mknod(os.path.join("../books", book[0], book[1]))
            except:
                pass

        # Create files in books - see test_restricted_access.py
        try:
            os.mknod(os.path.join("../books", "fifth_story", "test_image.jpg"))
        except:
            pass
        try:
            os.mknod(os.path.join("../books", "fourth_story", "my_track.gpx"))
        except:
            pass

        # Create a GPX file in an open book - see test_map.py
        try:
            copyfile(
                "Gillespie_Circuit.gpx",
                os.path.join("../books", "first_story", "test_Gillespie_Circuit.gpx"),
            )
        except:
            pass

        # Create an other GPX file in an open book - see test_map.py
        try:
            copyfile(
                "test_gpx_to_geojson.gpx",
                os.path.join("../books", "first_story", "test_gpx_to_geojson.gpx"),
            )
        except:
            pass

        # Create a book folder not in the database - see test_xhr_admin_space.py
        try:
            new_dir = os.path.join("../books", "lovely_poem")
            directories.append(new_dir)
            os.mkdir(new_dir)
        except:
            pass

    yield files

    for directory in directories:  # clean up
        shutil.rmtree(directory)


@pytest.fixture
def app():
    """ This client fixture will be called by each individual test. """
    app = create_app(True)

    with app.app_context():
        db.init_db()
        db.load_from_file(
            open(os.path.join(os.path.dirname(__file__), "data.sql"), "rb")
        )

    yield app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def runner(app):
    return app.test_cli_runner()


class auth_actions(object):
    def __init__(self, client):
        self._client = client

    def login(self, email="user@test.com", password="user"):
        self._client.get("/login", data=dict(), follow_redirects=True)  # load CAPTCHA
        return self._client.post(
            "/login",
            data=dict(
                email=email,
                password=password,
                captcha="empty",
                privacyPolicy=True,
                copyrightNotice=True,
            ),
            follow_redirects=True,
        )

    def logout(self):
        return self._client.get("/logout", follow_redirects=True)


@pytest.fixture
def auth(client):
    return auth_actions(client)
