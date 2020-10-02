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

@pytest.mark.parametrize("path", (
    ("/admin/members/revoke"),
    ("/admin/members/delete"),
    ("/admin/members/change_access_level"),
    ("/admin/members/list"),
    ("/admin/members/send_password_creation"),
    ("/admin/members/send_newsletter"),
    ("/admin/photos/add/form"),
    ("/admin/books/add/form"),
    ("/admin/photos/add/request"),
    ("/admin/books/add/request"),
    ("/admin/photos/list"),
    ("/admin/books/list"),
    ("/admin/photos/metadata"),
    ("/admin/books/metadata"),
    ("/admin/photos/move"),
    ("/admin/books/move"),
    ("/admin/photos/delete"),
    ("/admin/books/delete"),
    ("/admin/photos/lost"),
    ("/admin/photos/move_into_wastebasket"),
    ("/admin/photos/open/test_1zy071k164o6rjjjynvms47kr16a9h.jpg"),
    ("/admin/statistics"),
    ("/photos/3/test_74gdf8hpw41i4qbpnl7b.jpg"), # access level = 1
    ("/photos/3/test_wkd6xdrmbt9io96zcygpg12gt.jpg"), # access level = 1
    ("/photos/4/test_1zy071k164o6rjjjynvms47kr16a9h.jpg"), # access level = 240
    ("/photos/4/test_b4f6add9a5657725d156a94cde808ce8a5d4cf38.tif"), # access level = 240
    ("/books/5/fifth_story/test_image.jpg"), # access level = 1
    ("/stories/5/fifth_story"), # access level = 1
    ("/map/viewer/4/fourth_story/my_track/fr"), # access level = 1
    ("/map/player/4/fourth_story/my_track/fr"), # access level = 1
    ("/map/webtracks/4/fourth_story/my_track.webtrack"), # access level = 1
    ("/change_password"), # restricted to members
    ("/change_email"), # restricted to members
    ("/audit_log"), # restricted to members
    ("/social_networks/twitter/my_timeline"), # POST only
    ("/social_networks/mastodon/my_timeline"), # POST only
))
def test_restricted_access_denied(files, client, path):
    """
    Visitors not logged should be redirected to the login or the 404-error page.
    Test excludes XHR-only requests.
    """
    rv = client.get(path, follow_redirects=True)
    assert rv.status_code == 404 or b"Password required" in rv.data

@pytest.mark.parametrize("path", (
    ("/index"), # access level = 0
    ("/photos/3/test_74gdf8hpw41i4qbpnl7b.jpg"), # access level = 1
    ("/photos/3/test_wkd6xdrmbt9io96zcygpg12gt.jpg"), # access level = 1
    ("/books/5/fifth_story/test_image.jpg"), # access level = 1
    ("/stories/5/fifth_story"), # access level = 1
    ("/map/viewer/4/fourth_story/my_track/fr"), # access level = 1
    ("/map/player/4/fourth_story/my_track/fr"), # access level = 1
    ("/books/4/fourth_story/my_track.gpx"), # access level = 1
    ("/change_password"),
    ("/change_email"),
    ("/audit_log"),
))
def test_member_access_granted(files, client, auth, path):
    """
    Members should be able to access some content.
    Test excludes XHR-only requests.
    """
    auth.login()
    rv = client.get(path)
    assert rv.status_code == 200

def test_webtrack_failed(client, auth):
    """
    Ask for a restricted WebTrack that cannot be created because the GPX file is missing.
    """
    auth.login()
    rv = client.get("/map/webtracks/4/fourth_story/my_track.webtrack")
    assert rv.status_code == 500
    assert b"GPX file missing or empty" in rv.data

@pytest.mark.parametrize("path", (
    ("/admin/members/revoke"),
    ("/admin/members/delete"),
    ("/admin/members/change_access_level"),
    ("/admin/members/list"),
    ("/admin/members/send_password_creation"),
    ("/admin/members/send_newsletter"),
    ("/admin/photos/add/form"),
    ("/admin/books/add/form"),
    ("/admin/photos/add/request"),
    ("/admin/books/add/request"),
    ("/admin/photos/list"),
    ("/admin/books/list"),
    ("/admin/photos/metadata"),
    ("/admin/books/metadata"),
    ("/admin/photos/move"),
    ("/admin/books/move"),
    ("/admin/photos/delete"),
    ("/admin/books/delete"),
    ("/admin/photos/lost"),
    ("/admin/photos/move_into_wastebasket"),
    ("/admin/photos/open/test_1zy071k164o6rjjjynvms47kr16a9h.jpg"),
    ("/admin/statistics"),
    ("/photos/4/test_1zy071k164o6rjjjynvms47kr16a9h.jpg"), # access level = 240
    ("/photos/4/test_b4f6add9a5657725d156a94cde808ce8a5d4cf38.tif"), # access level = 240
    ("/create_password"),
))
def test_member_access_denied(files, client, auth, path):
    """
    Check some restrictions for logged in members.
    Test excludes XHR-only requests.
    """
    auth.login()
    rv = client.get(path, follow_redirects=True)
    assert rv.status_code == 404 or b"Password required" in rv.data

@pytest.mark.parametrize("path", (
    ("/members/list"),
    ("/photos/add/form"),
    ("/books/add/form"),
    ("/photos/list"),
    ("/books/list"),
    ("/photos/lost"),
    ("/photos/open/test_74gdf8hpw41i4qbpnl7b.jpg"),
    ("/statistics"),
))
def test_admin_access_granted(files, client, auth, path):
    """ Test pages not fetched otherwise. """
    auth.login("root@test.com", "admin")
    rv = client.get("/admin" + path)
    assert rv.status_code == 200
    auth.logout()
