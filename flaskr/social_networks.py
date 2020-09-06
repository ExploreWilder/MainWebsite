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
from twython import Twython
from xml.dom import minidom

social_networks_app = Blueprint("social_networks_app", __name__)

def share_link(link, network, subject=None):
    """ Format a social platform link and return a string. """
    networks = {"twitter": 'https://twitter.com/intent/tweet?via=' + current_app.config["TWITTER_ACCOUNT"]["screen_name"] + '&url=',
                "facebook": 'https://www.facebook.com/sharer/sharer.php?u=',
                "linkedin": 'https://www.linkedin.com/shareArticle?mini=true&url=',
                "vkontakte": 'https://vk.com/share.php?url=',
                "email": 'mailto:?subject=' + (quote_plus(subject) if subject else '') + '&amp;body=',
                "tumblr": 'http://www.tumblr.com/share/link?url='}
    return networks[network] + quote_plus(link if link.startswith('http') else request.url_root + link)

def download_image(src, data_store):
    """
    Download `src` and save it in the `data_store` directory and return the renamed image name.

    Args:
        src (str): External URL of the image to download.
        data_store (str): Path to the (local) directory where the image will be saved.
    
    Returns:
        str: The SHA1 of `src` plus the `src` extension. That is the (local) filename.
    """
    ext = file_extension(src)
    hashed_src = hashlib.sha1(src.encode()).hexdigest() + "." + ext
    path_file = os.path.join(data_store, hashed_src)
    if not os.path.isfile(path_file):
        r = requests.get(src)
        with open(path_file, "wb") as f:
            f.write(r.content)
    return hashed_src

def compress_timeline(timeline, data_store):
    """
    Compress the verbose Twitter feed into a small one. Just keep the useful elements.
    All images are downloaded and image links are just filenames of the local version.
    The media download is intended to avoid enlarging the image-src rule of the CSP,
    bypass the blocking browser plugins, and reduced the social platforms tracking
    capabilities and comply with my "Your Privacy Is My Priority" policy.

    Args:
        timeline (Dict): The Twitter timeline.
        data_store (str): Path of the (local) directory where images will be saved.
    
    Returns:
        Dict: The timeline with less information and links to the (locally) stored images.
    """
    compressed_timeline = []
    for tweet in timeline:
        compressed_tweet = {
            "created_at": tweet["created_at"],
            "text": tweet["text"],
            "id_str": tweet["id_str"],
            "user": {
                "name": tweet["user"]["name"],
                "screen_name": tweet["user"]["screen_name"],
                "profile_image_url_https": download_image(tweet["user"]["profile_image_url_https"], data_store)
            }
        }
        if tweet["retweeted"]:
            original_source = tweet["retweeted_status"]["user"]
            compressed_tweet["retweeted_status"] = {
                "user": {
                    "name": original_source["name"],
                    "screen_name": original_source["screen_name"],
                    "profile_image_url_https": download_image(original_source["profile_image_url_https"], data_store)
                }
            }
        compressed_timeline.append(compressed_tweet)

    return compressed_timeline

@social_networks_app.route("/<string:network>/media/<string:filename>", methods=("GET",))
def twitter_media(network, filename):
    """
    Make media reachable by the user. The HTTP referrer must point to the website.

    Args:
        network (str): Social platform name in small cap, "twitter" or "mastodon".
        filename (str): The filename of the image (locally) saved, excluding the directory.
    
    Returns:
        The image.
    """
    if not is_same_site() and not (current_app.config["TESTING"] or current_app.config["DEBUG"]):
        abort(404)
    network = escape(network)
    if network == "twitter":
        data_store = current_app.config["TWITTER_ACCOUNT"]["data_store"]
    elif network == "mastodon":
        data_store = current_app.config["MASTODON_ACCOUNT"]["data_store"]
    else:
        abort(404)
    return send_from_directory(data_store, secure_filename(escape(filename)))

@social_networks_app.route("/twitter/my_timeline", methods=("POST",))
def my_twitter_timeline():
    """ Update the locally saved timeline (if too old) and return it. """
    if not is_same_site() and not (current_app.config["TESTING"] or current_app.config["DEBUG"]):
        abort(404)
    timeline_filename = "timeline_" + current_app.config["TWITTER_ACCOUNT"]["screen_name"] + ".json"
    data_store = current_app.config["TWITTER_ACCOUNT"]["data_store"]
    old_timeline = os.path.join(data_store, timeline_filename)
    current_timestamp = datetime.datetime.now().timestamp()
    delta = current_app.config["TWITTER_ACCOUNT"]["max_refresh_period"]

    # update:
    if (not os.path.isfile(old_timeline)) or (os.stat(old_timeline).st_mtime + delta) < current_timestamp:
        # authenticate:
        twitter = Twython(
            current_app.config["TWITTER_ACCOUNT"]["api_key"],
            current_app.config["TWITTER_ACCOUNT"]["api_secret_key"],
            current_app.config["TWITTER_ACCOUNT"]["user_access_token"],
            current_app.config["TWITTER_ACCOUNT"]["user_access_token_secret"])
        
        # download:
        content = twitter.get_user_timeline(
            screen_name=current_app.config["TWITTER_ACCOUNT"]["screen_name"],
            json_encoded=True)

        # compress and overwrite the old timeline:
        with open(old_timeline, "w") as new_timeline:
            new_timeline.write(json.dumps(compress_timeline(content, current_app.config["TWITTER_ACCOUNT"]["data_store"])))
    
    return send_from_directory(data_store, timeline_filename)

def get_dom_text(nodelist):
    """ Find out the text node of `nodelist` and return a string. """
    rc = []
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
            rc.append(node.data)
    return ''.join(rc)

@social_networks_app.route("/mastodon/my_timeline", methods=("POST",))
def my_mastodon_timeline():
    """ Update the locally saved timeline (if too old) and return it. """
    if not is_same_site() and not (current_app.config["TESTING"] or current_app.config["DEBUG"]):
        abort(404)
    timeline_filename = "my_timeline.json"
    data_store = current_app.config["MASTODON_ACCOUNT"]["data_store"]
    old_timeline = os.path.join(data_store, timeline_filename)
    current_timestamp = datetime.datetime.now().timestamp()
    delta = current_app.config["MASTODON_ACCOUNT"]["max_refresh_period"]

    # update:
    if (not os.path.isfile(old_timeline)) or (os.stat(old_timeline).st_mtime + delta) < current_timestamp:
        account_url = current_app.config["MASTODON_ACCOUNT"]["community_url"] + "@" + current_app.config["MASTODON_ACCOUNT"]["screen_name"]
        r = requests.get(account_url + ".rss")
        content = r.content
        dom = minidom.parseString(content)
        toots = dom.getElementsByTagName("item")
        all_my_toots = []

        for toot_dom in toots:
            toot_dict = {
                "text": get_dom_text(toot_dom.getElementsByTagName("title")[0].childNodes),
                "guid": get_dom_text(toot_dom.getElementsByTagName("guid")[0].childNodes),
                "created_at": get_dom_text(toot_dom.getElementsByTagName("pubDate")[0].childNodes)
            }
            media = toot_dom.getElementsByTagName("enclosure")
            if len(media) > 0:
                images = []
                for image in media:
                    images.append({
                        "url": download_image(image.getAttribute("url"), data_store),
                        "type": image.getAttribute("type").split('/')[-1]
                    })
                toot_dict["images"] = images
            all_my_toots.append(toot_dict)
        
        # overwrite the old timeline:
        with open(old_timeline, "w") as new_timeline:
            new_timeline.write(json.dumps(all_my_toots))
    
    return send_from_directory(data_store, timeline_filename)
