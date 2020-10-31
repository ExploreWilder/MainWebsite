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

import pytest

from flaskr import utils
from flaskr.db import get_db


@pytest.mark.parametrize(
    "real_ip,anonimized_ip",
    [
        ("127.0.0.1", "127.0.0.0"),
        ("43.674.128.425", "43.674.128.0"),
        ("34.88.06.35", "34.88.06.0"),
        ("3.2.1.0", "3.2.1.0"),
    ],
)
def test_anonymize_ip(real_ip, anonimized_ip):
    """ Test the IP address anonymization. """
    assert utils.anonymize_ip(real_ip) == anonimized_ip


@pytest.mark.parametrize(
    "real_ip",
    (
        ("127.0.0.1.0"),
        ("3.2.1"),
        ("34.88.06.35.8"),
        ("43.674"),
    ),
)
def test_anonymize_invalid_ip(real_ip):
    """ Try anonimizing badly formatted IP addresses. """
    try:
        utils.anonymize_ip(real_ip)
        assert False
    except ValueError:
        assert True


@pytest.mark.parametrize(
    "pdf",
    (
        ("file.pdf"),
        ("dignvoend.pdf"),
        ("hello.pdf.pdf"),
    ),
)
def test_file_is_pdf(pdf):
    """ Test valid PDF file name. """
    assert utils.file_is_pdf(pdf)


@pytest.mark.parametrize(
    "pdf",
    (
        ("file.pedf"),
        ("dignvoendpdf"),
        ("hello.pdf.txt"),
    ),
)
def test_file_is_not_pdf(pdf):
    """ Test invalid PDF file name. """
    assert not utils.file_is_pdf(pdf)


@pytest.mark.parametrize(
    "path",
    (
        ("http://hello.com"),
        ("https://hello.com/abc"),
    ),
)
def test_match_absolute_path(path):
    """ Test valid absolute path. """
    assert utils.match_absolute_path(path)


@pytest.mark.parametrize(
    "path",
    (
        ("file:///home"),
        ("/index"),
    ),
)
def test_not_match_absolute_path(path):
    """ Test invalid absolute path. """
    assert not utils.match_absolute_path(path)


@pytest.mark.parametrize(
    "email",
    (
        ("user@test.com"),
        ("user+newsletter@test.fr"),
        ("user+newsletter@test.cern"),
        ("user+test@127.0.0.1"),  # dodgy but valid
    ),
)
def test_valid_emails(email):
    """ Test valid emails. """
    assert utils.email_is_valid(email)


def test_get_image_exif_with_no_exif():
    """ Try to get exif data from an empty file without fail. """
    assert utils.get_image_exif("original.tifi") == (None, None, None, None, None)


@pytest.mark.parametrize(
    "email",
    (
        ("user@test"),
        ("user@test+c.om"),
        ("us er@test.com"),
        ("user@127.0.0.1:42"),  # too dodgy
    ),
)
def test_invalid_emails(email):
    """ Test invalid or dodgy emails. """
    assert not utils.email_is_valid(email)


def test_check_access_level_range(client):
    """ Access level is in the range [0-255]. """
    assert utils.check_access_level_range(42)
    assert utils.check_access_level_range(0)
    assert utils.check_access_level_range(255)
    assert not utils.check_access_level_range(-1)
    assert not utils.check_access_level_range(256)


def test_is_admin(client, auth):
    """ Check admin identification. """
    with client:
        client.get("/")
        assert not utils.is_admin()
        auth.login("root@test.com", "admin")
        assert utils.is_admin()
        auth.logout()
        assert not utils.is_admin()


@pytest.mark.parametrize(
    "str",
    (
        ("hello"),
        (" hello "),
        ("\nhello"),
        ("\nhello"),
        ("hel lo"),
        ("hello\t"),
    ),
)
def test_remove_whitespaces(str):
    """ Check whitespaces removal. """
    assert utils.remove_whitespaces(str) == "hello"


def test_get_access_level_from_id(app):
    """ Check members' access level according to the database. """
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        assert utils.get_access_level_from_id(1, cursor) == 255
        assert utils.get_access_level_from_id(2, cursor) == 190


def test_preview_image():
    """ Test the tiny image creation. """
    assert utils.preview_image("card2.jpg").startswith(
        b"data:image/jpeg;base64,/9j/4AAQSkZ"
    )
    assert utils.preview_image("card42.jpg") == b""


def test_secure_decode_query_string():
    """ Check the query_string security layer. """
    input_str = b"<script>bla%3Cbla</script>"
    output_str = "scriptblabla/script"
    assert utils.secure_decode_query_string(input_str) == output_str


def test_params_urlencode():
    """ Test the URL params encoder. """
    example_params = {"style": "normal", "tilematrixset": "PM", "Service": "WMTS"}
    assert (
        utils.params_urlencode(example_params)
        == "style=normal&tilematrixset=PM&Service=WMTS"
    )


def test_replace_extension():
    """ Test the file extension replacer. """
    assert utils.replace_extension("hello/file.txt", "bin") == "hello/file.bin"
    assert (
        utils.replace_extension("super_track.gpx", "webtrack") == "super_track.webtrack"
    )
    assert utils.replace_extension("main", "txt") == "main.txt"
    assert utils.replace_extension(".main", "txt") == ".main.txt"
