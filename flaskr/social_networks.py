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
Socials-related functions and routes.
"""

from xml.dom import minidom

from twython import Twython
from twython import TwythonError
from werkzeug.exceptions import BadRequest
from werkzeug.exceptions import NotFound

from .utils import *

social_networks_app = Blueprint("social_networks_app", __name__)


def share_link(link: str, network: str, subject: str = "") -> str:
    """ Format a social platform link and return a string. """
    networks = {
        "twitter": "https://twitter.com/intent/tweet?via="
        + current_app.config["TWITTER_ACCOUNT"]["screen_name"]
        + "&url=",
        "facebook": "https://www.facebook.com/sharer/sharer.php?u=",
        "linkedin": "https://www.linkedin.com/shareArticle?mini=true&url=",
        "vkontakte": "https://vk.com/share.php?url=",
        "email": "mailto:?subject="
        + (quote_plus(subject) if subject else "")
        + "&amp;body=",
        "tumblr": "http://www.tumblr.com/share/link?url=",
    }
    return networks[network] + quote_plus(
        link if link.startswith("http") else request.url_root + link
    )


def create_media_filename(src: str, salt: bytes) -> str:
    """ Hash `src` with a secret `salt` so that the authenticity can be checked, and return a string. """
    return werkzeug.security.pbkdf2_hex(src, salt) + "." + file_extension(src)


def encode_media_origin(url: str) -> str:
    """ Convert the string `url` into an hexadecimal string (URL safer than base64, no trailing '='). """
    return url.encode().hex()


def decode_media_origin(hex_str: str) -> str:
    """ Decode a string encoded with encode_media_origin() and return a string. """
    return bytes.fromhex(hex_str).decode()


def download_image(
    clear_url: str,
    hashed_filename: str,
    data_store: str,
    timeout: Union[float, Tuple[float, float]],
) -> None:
    """
    Download `clear_url` and save it in the `data_store` directory as `hashed_filename`.
    The media download is intended to avoid enlarging the image-src rule of the CSP,
    bypass the blocking browser plugins, and reduced the social platforms tracking
    capabilities, and comply with my "Your Privacy Is My Priority" policy.

    Args:
        clear_url (str): External URL of the image to download (source must be trusted).
        hashed_filename (str): The local filename with the proper extension.
        data_store (str): Path to the (local) directory where the image will be saved.
        timeout (float or tuple): Refer to https://requests.readthedocs.io/en/master/user/advanced/#timeouts
    """
    path_file = os.path.join(data_store, hashed_filename)
    if not os.path.isfile(path_file):
        r = requests.get(clear_url, timeout=timeout)  # pylint: disable=invalid-name
        r.raise_for_status()
        with open(path_file, "wb") as image_file:
            image_file.write(r.content)


def compress_timeline(timeline: List, salt: bytes) -> List:
    """
    Compress the verbose Twitter feed into a small one. Just keep the useful elements.
    The images are downloaded per-request.

    Args:
        timeline (List): The Twitter timeline.
        salt (bytes): The salt to apply on the filename.

    Returns:
        List: The timeline with less information and links to the (locally) stored images.
    """
    compressed_timeline = []
    for tweet in timeline:
        profile_image_url = tweet["user"]["profile_image_url_https"]
        compressed_tweet = {
            "created_at": tweet["created_at"],
            "text": tweet["text"],
            "id_str": tweet["id_str"],
            "user": {
                "name": tweet["user"]["name"],
                "screen_name": tweet["user"]["screen_name"],
                "profile_image_origin": encode_media_origin(profile_image_url),
                "profile_image_filename": create_media_filename(
                    profile_image_url, salt
                ),
            },
        }
        if tweet["retweeted"]:
            original_source = tweet["retweeted_status"]["user"]
            profile_image_url = original_source["profile_image_url_https"]
            compressed_tweet["retweeted_status"] = {
                "user": {
                    "name": original_source["name"],
                    "screen_name": original_source["screen_name"],
                    "profile_image_origin": encode_media_origin(profile_image_url),
                    "profile_image_filename": create_media_filename(
                        profile_image_url, salt
                    ),
                }
            }
        compressed_timeline.append(compressed_tweet)

    return compressed_timeline


def get_dom_text(nodelist) -> str:
    """ Find out the text node of `nodelist` and return a string. """
    rc = []  # pylint: disable=invalid-name
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
            rc.append(node.data)
    return "".join(rc)


@social_networks_app.route(
    "/<string:network>/media/<string:origin>/<string:filename>", methods=("GET",)
)
@same_site
def send_media(network: str, origin: str, filename: str) -> FlaskResponse:
    """
    Make media reachable by the user. The HTTP referrer must point to the website.

    Args:
        network (str): Social platform name in small cap, "twitter" or "mastodon".
        origin (str): Encoded URL to the original file.
        filename (str): The filename of the image (locally) saved, excluding the directory.

    Returns:
        The image.
    """
    network = escape(network).upper()
    origin = escape(origin)
    filename = secure_filename(escape(filename))
    if network in ["TWITTER", "MASTODON"]:
        data_store = current_app.config[network + "_ACCOUNT"]["data_store"]
        timeout = current_app.config[network + "_ACCOUNT"]["connection_timeout"]
    else:
        abort(404)

    if not os.path.isfile(
        os.path.join(data_store, filename)
    ):  # download and save locally
        origin_url = decode_media_origin(origin)
        reverse_filename = create_media_filename(
            origin_url, current_app.config["RANDOM_SALT"]
        )
        if reverse_filename == filename:
            download_image(origin_url, reverse_filename, data_store, timeout)
        else:
            abort(404)  # compromised origin

    return send_from_directory(data_store, filename)


@social_networks_app.route("/twitter/my_timeline", methods=("POST",))
@same_site
def my_twitter_timeline() -> FlaskResponse:
    """ Update the locally saved timeline (if too old) and return it. """
    screen_name = current_app.config["TWITTER_ACCOUNT"]["screen_name"]
    timeline_filename = "timeline_" + screen_name + ".json"
    data_store = current_app.config["TWITTER_ACCOUNT"]["data_store"]
    old_timeline = os.path.join(data_store, timeline_filename)
    current_timestamp = datetime.datetime.now().timestamp()
    delta = current_app.config["TWITTER_ACCOUNT"]["max_refresh_period"]

    # update:
    if (not os.path.isfile(old_timeline)) or (
        os.stat(old_timeline).st_mtime + delta
    ) < current_timestamp:
        # authenticate:
        twitter = Twython(
            current_app.config["TWITTER_ACCOUNT"]["api_key"],
            current_app.config["TWITTER_ACCOUNT"]["api_secret_key"],
            current_app.config["TWITTER_ACCOUNT"]["user_access_token"],
            current_app.config["TWITTER_ACCOUNT"]["user_access_token_secret"],
        )

        try:  # download:
            content = twitter.get_user_timeline(
                screen_name=screen_name, json_encoded=True
            )
        # https://twython.readthedocs.io/en/latest/api.html#exceptions
        except TwythonError:  # pragma: no cover
            current_app.logger.exception(
                "Failed to get the " + screen_name + " timeline from Twitter"
            )
        else:  # compress and overwrite the old timeline:
            with open(old_timeline, "w") as new_timeline:
                new_timeline.write(
                    json.dumps(
                        compress_timeline(content, current_app.config["RANDOM_SALT"])
                    )
                )

    try:
        return send_from_directory(data_store, timeline_filename)
    except (NotFound, BadRequest):  # pragma: no cover; system error
        current_app.logger.exception(
            "Failed to locally retrieve the Twitter timeline @" + screen_name
        )
        abort(404)


@social_networks_app.route("/mastodon/my_timeline", methods=("POST",))
@same_site
def my_mastodon_timeline() -> FlaskResponse:
    """ Update the locally saved timeline (if too old) and return it. """
    timeline_filename = "my_timeline.json"
    data_store = current_app.config["MASTODON_ACCOUNT"]["data_store"]
    old_timeline = os.path.join(data_store, timeline_filename)
    current_timestamp = datetime.datetime.now().timestamp()
    delta = current_app.config["MASTODON_ACCOUNT"]["max_refresh_period"]
    file_exists = os.path.isfile(old_timeline)
    timeout = current_app.config["MASTODON_ACCOUNT"]["connection_timeout"]
    account_url = (
        current_app.config["MASTODON_ACCOUNT"]["community_url"]
        + "@"
        + current_app.config["MASTODON_ACCOUNT"]["screen_name"]
    )

    # update:
    if (not file_exists) or (
        os.stat(old_timeline).st_mtime + delta
    ) < current_timestamp:
        try:
            r = requests.get(  # pylint: disable=invalid-name
                account_url + ".rss", timeout=timeout
            )
            r.raise_for_status()
        except requests.exceptions.HTTPError:  # pragma: no cover
            current_app.logger.exception(
                "Failed to get the Mastodon timeline: " + account_url
            )
        else:
            if current_app.config["DEBUG"]:
                r.raise_for_status()  # keep silent in prod, no error threw, no update

            # if the HTTP status code < 400 (error), so it could be 200 (OK) or 301 (Not Modified):
            if r.status_code == requests.codes.ok:
                content = r.content
                dom = minidom.parseString(content)
                toots = dom.getElementsByTagName("item")
                all_my_toots = []

                for toot_dom in toots:
                    toot_dict: Dict[str, Any] = {
                        "text": get_dom_text(
                            toot_dom.getElementsByTagName("title")[0].childNodes
                        ),
                        "guid": get_dom_text(
                            toot_dom.getElementsByTagName("guid")[0].childNodes
                        ),
                        "created_at": get_dom_text(
                            toot_dom.getElementsByTagName("pubDate")[0].childNodes
                        ),
                    }
                    media = toot_dom.getElementsByTagName("enclosure")
                    if len(media) > 0:
                        images = []
                        for image in media:
                            image_url = image.getAttribute("url")
                            images.append(
                                {
                                    "filename": create_media_filename(
                                        image_url, current_app.config["RANDOM_SALT"]
                                    ),
                                    "origin": encode_media_origin(image_url),
                                    "type": image.getAttribute("type").split("/")[-1],
                                }
                            )
                        toot_dict["images"] = images
                    all_my_toots.append(toot_dict)

                # overwrite the old timeline:
                with open(old_timeline, "w") as new_timeline:
                    new_timeline.write(json.dumps(all_my_toots))

    try:
        return send_from_directory(data_store, timeline_filename)
    except (NotFound, BadRequest):  # pragma: no cover; system error
        current_app.logger.exception(
            "Failed to locally retrieve the Mastodon timeline " + account_url
        )
        abort(404)
