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

import json
import os
import time
from urllib.parse import urlparse

from flaskr.social_networks import encode_media_origin


def test_mastodon_timeline(client, app, tmpdir):
    """ Download the Mastodon timeline. """
    with app.app_context():
        # force download:
        new_dir = str(tmpdir)
        app.config["MASTODON_ACCOUNT"]["data_store"] = new_dir
        rv = client.post("/social_networks/mastodon/my_timeline")
        assert rv.status_code == 200
        timeline_path = os.path.join(new_dir, "my_timeline.json")
        timeline_timestamp = os.path.getmtime(timeline_path)
        with open(timeline_path) as timeline_file:
            timeline_json = json.load(timeline_file)
        send_media_tested = False
        for toot in timeline_json:
            assert "text" in toot
            url = urlparse(toot["guid"])
            expected_url = urlparse(app.config["MASTODON_ACCOUNT"]["community_url"])
            assert url.scheme == expected_url.scheme
            assert url.netloc == expected_url.netloc
            assert (
                url.path.split("/")[1][1:]
                == app.config["MASTODON_ACCOUNT"]["screen_name"]
            )
            assert "created_at" in toot

            # test send_media():
            if (not send_media_tested) and "images" in toot:
                first_image = toot["images"][0]
                image_filename = first_image["filename"]

                # bad download from compromised origin:
                image_origin = encode_media_origin("https://example.com/image.jpg")
                media = (
                    "/social_networks/mastodon/media/"
                    + image_origin
                    + "/"
                    + image_filename
                )
                rv = client.get(media)
                assert rv.status_code == 404

                # bad download from unknown social platform:
                media = (
                    "/social_networks/facebook/media/"
                    + first_image["origin"]
                    + "/"
                    + image_filename
                )
                rv = client.get(media)
                assert rv.status_code == 404

                # good download:
                media = (
                    "/social_networks/mastodon/media/"
                    + first_image["origin"]
                    + "/"
                    + image_filename
                )
                rv = client.get(media)
                assert rv.status_code == 200

                # check cache:
                image_path = os.path.join(new_dir, image_filename)
                image_timestamp = os.path.getmtime(image_path)
                time.sleep(1)
                rv = client.get(media)
                assert rv.status_code == 200
                new_image_timestamp = os.path.getmtime(image_path)
                assert image_timestamp == new_image_timestamp

                send_media_tested = True

        # should not re-download or overwrite within a short period:
        time.sleep(1)
        rv = client.post("/social_networks/mastodon/my_timeline")
        assert rv.status_code == 200
        new_timeline_timestamp = os.path.getmtime(timeline_path)
        assert timeline_timestamp == new_timeline_timestamp


def test_twitter_timeline(client, app, tmpdir):
    """ Download the Mastodon timeline. """
    with app.app_context():
        # force download:
        new_dir = str(tmpdir)
        app.config["TWITTER_ACCOUNT"]["data_store"] = new_dir
        rv = client.post("/social_networks/twitter/my_timeline")
        assert rv.status_code == 200
        timeline_filename = (
            "timeline_" + app.config["TWITTER_ACCOUNT"]["screen_name"] + ".json"
        )
        timeline_path = os.path.join(new_dir, timeline_filename)
        timeline_timestamp = os.path.getmtime(timeline_path)
        with open(timeline_path) as timeline_file:
            timeline_json = json.load(timeline_file)
        for tweet in timeline_json:
            assert all(x in tweet for x in ("user", "text", "created_at"))

        # should not re-download or overwrite within a short period:
        time.sleep(1)
        rv = client.post("/social_networks/twitter/my_timeline")
        assert rv.status_code == 200
        new_timeline_timestamp = os.path.getmtime(timeline_path)
        assert timeline_timestamp == new_timeline_timestamp
