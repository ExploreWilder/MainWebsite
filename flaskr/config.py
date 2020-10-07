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

class Config(object):
    """ Configuration in debug/development mode. """

    #: Interactive debugger for unhandled exceptions and auto-reload on code changes.
    DEBUG=True
    #: True to warn the user about a maintenance.
    MAINTENANCE=True
    #: Number of characters/digits in the CAPTCHA.
    CAPTCHA_LENGTH=3
    #: List of characters and digits without the similar ones 0O, LV, 1I, etc.
    CAPTCHA_CHARACTERS_OKAY="ABCDEFGHIJKLMNOPQRSTUVWXYZ23456789"
    #: Full path where the TTF font is located.
    CAPTCHA_TTF_FONT=absolute_path("static/web_fonts/UNDISCLOSED/UNDISCLOSED.ttf")
    #: User name to access the MySQL database.
    MYSQL_DATABASE_USER="UNDISCLOSED"
    #: Password of the user.
    MYSQL_DATABASE_PASSWORD="UNDISCLOSED"
    #: Name of the MySQL database.
    MYSQL_DATABASE_DB="UNDISCLOSED"
    #: Set to *localhost* if the database is in the same server than the application.
    MYSQL_DATABASE_HOST="UNDISCLOSED"
    #: Browsers will not allow JavaScript access to cookies marked as *HTTP only* for security.
    SESSION_COOKIE_HTTPONLY=True
    #: Browsers will not allow JavaScript access to the remember me cookie from Flask-Login.
    REMEMBER_COOKIE_HTTPONLY=True
    #: Browsers will allow JavaScript access to the CSRF cookie from Flask-SeaSurf.
    CSRF_COOKIE_HTTPONLY=True
    #: Restrict how cookies are sent with requests from external sites.
    SESSION_COOKIE_SAMESITE="Strict"
    #: Restrict how the CSRF cookie is sent with requests from external sites.
    CSRF_COOKIE_SAMESITE="Strict"
    #: Cookies secret key.
    COOKIE_SECRET_KEY=b"UNDISCLOSED"
    #: A secret key that will be used for securely signing the session cookie.
    SECRET_KEY=b"UNDISCLOSED"
    #: Salt used to hash the captcha code.
    CAPTCHA_SALT=b"UNDISCLOSED"
    #: Directory where CAPTCHAs are saved.
    CAPTCHA_FOLDER=absolute_path("captchas")
    #: Salt used to hash some user exposed data.
    RANDOM_SALT=b"UNDISCLOSED"
    #: Path where all the photographies are located.
    GALLERY_FOLDER=absolute_path("UNDISCLOSED")
    #: Path where all the books are located.
    SHELF_FOLDER=absolute_path("UNDISCLOSED")
    #: Path where all "deleted" files are moved.
    WASTEBASKET_FOLDER=absolute_path("UNDISCLOSED")
    #: Email user name.
    EMAIL_USER="UNDISCLOSED"
    #: Email domain name.
    EMAIL_DOMAIN="UNDISCLOSED.com"
    #: DKIM selector.
    DKIM_SELECTOR="default"
    #: Path to the DKIM private key.
    DKIM_PATH_PRIVATE_KEY=absolute_path("UNDISCLOSED")
    #: Brand name.
    BRAND_NAME="ExploreWilder.com"
    #: Legal name (for the copyright).
    LEGAL_NAME="Clement"
    #: No cache to develop and test with instant changes.
    CACHE_TYPE="null"
    #: Required elapsed time before the user can re-submit.
    REQUIRED_TIME_GAP=15
    #: Size (width and height) in pixel of the thumbnails.
    THUMBNAIL_SIZE=300
    #: JPEG quality compression in percent of the resized photography.
    PHOTO_QUALITY=95
    #: Maximum width/height in pixel of the big photo displayed in the interface.
    PHOTO_L_MAX_SIZE=(2560, 1440)
    #: Maximum width/height in pixel of the medium photo displayed in the interface.
    PHOTO_M_MAX_SIZE=(1366, 768)
    #: Length of the random file name for thumbnails, '.jpg' excluded.
    THUMBNAIL_FILENAME_SIZE=20
    #: Length of the random file name for medium photos, '.jpg' excluded.
    PHOTO_M_FILENAME_SIZE=25
    #: Length of the random file name for big photos, '.jpg' excluded.
    PHOTO_L_FILENAME_SIZE=30
    #: Required access level to be able to read the pictures title and description.
    ACCESS_LEVEL_READ_INFO=64
    #: Required access level to be able to download a .gpx file.
    ACCESS_LEVEL_DOWNLOAD_GPX=10
    #: List of emotions accordingly to the buttons next to the big picture.
    EMOTIONS=["love", "like", "neutral", "dislike", "hate"]
    #: Crowdfunding currency of the amount defined in the webhook table.
    CROWDFUNDING_CURRENCY="€"
    #: Number of photos per page in the admin section.
    DEFAULT_PHOTOS_PER_PAGE=15
    #: Number of books per page in the admin section.
    DEFAULT_BOOKS_PER_PAGE=15
    #: Do NOT choose an option multiple of an other one, to drag & drop from one page to an other one.
    OPTIONS_PHOTOS_PER_PAGE=[DEFAULT_PHOTOS_PER_PAGE, 70, 200]
    #: Do NOT choose an option multiple of an other one, to drag & drop from one page to an other one.
    OPTIONS_BOOKS_PER_PAGE=[DEFAULT_BOOKS_PER_PAGE, 70, 200]
    #: Twitter account details
    TWITTER_ACCOUNT={
        "name": "UNDISCLOSED", # the name displayed in the profile
        "screen_name": "UNDISCLOSED", # the name in the URL
        "user_access_token": "UNDISCLOSED",
        "user_access_token_secret": "UNDISCLOSED",
        "app_name": "UNDISCLOSED",
        "app_id": "UNDISCLOSED",
        "api_key": "UNDISCLOSED",
        "api_secret_key": "UNDISCLOSED",
        "bearer_token": "UNDISCLOSED",
        "data_store": absolute_path("UNDISCLOSED"),
        "max_refresh_period": 60*60, # seconds
        "connection_timeout": 5, # seconds to wait before giving up the timeline download
    }
    #: Mastodon account details
    MASTODON_ACCOUNT={
        "name": "UNDISCLOSED", # the name displayed in the profile
        "screen_name": "UNDISCLOSED", # the name in the URL
        "community_url": "https://UNDISCLOSED/",
        "data_store": absolute_path("UNDISCLOSED"),
        "max_refresh_period": 60*60, # seconds
        "connection_timeout": 5, # seconds to wait before giving up the timeline download
    }
    #: More Markdown extensions: https://python-markdown.github.io/extensions/
    MD_EXT=verbose_md_ext(["admonition", "footnotes", "attr_list", "abbr", "toc", "def_list", "tables"]) + [
        AmazonAffiliateLinksExtension(),
        TweetableExtension(twitter_username=TWITTER_ACCOUNT["screen_name"], brand_name=BRAND_NAME)]
    #: Additional extensions for processing the stories.
    BOOK_MD_EXT=MD_EXT + ["mdx_sections",]
    #: Publicly available country-specific layers accessible by the map viewer app.
    MAP_LAYERS=["NZ", "FR", "CA", "NO", "CH"]
    #: LDS API key.
    LDS_API_KEY="UNDISCLOSED"
    #: Thunderforest API key.
    THUNDERFOREST_API_KEY="UNDISCLOSED"
    #: Microsoft Bing key.
    BING_API_KEY="UNDISCLOSED"
    #: IGN app key and credentials.
    IGN={"username": "UNDISCLOSED", "password": "UNDISCLOSED", "app": "UNDISCLOSED"}
    #: Mapbox public token.
    MAPBOX_PUB_KEY="pk.UNDISCLOSED.UNDISCLOSED"
    #: NASA Earthdata credentials: https://urs.earthdata.nasa.gov/home
    NASA_EARTHDATA={"username": "UNDISCLOSED", "password": "UNDISCLOSED"}
    #: Social networks (excluding donation platforms).
    SOCIAL_NETWORKS=[
        ("Mastodon", MASTODON_ACCOUNT["community_url"] + "@" + MASTODON_ACCOUNT["screen_name"]),
        ("Twitter", "https://twitter.com/" + TWITTER_ACCOUNT["screen_name"]),
        ("Pixelfed", "https://pixelfed.social/UNDISCLOSED")]
    #: Mapbox Static Images Configuration (kind of): https://docs.mapbox.com/api/maps/#static-images
    MAPBOX_STATIC_IMAGES={
        "username": "UNDISCLOSED",
        "style_id": "UNDISCLOSED",
        "width": 800,
        "height": 500,
        "@2x": True,
        "access_token": "pk.UNDISCLOSED.UNDISCLOSED",
        "logo": False,
        "points": 150
    }
    #: Content Security Policy Configuration.
    CSP_CONFIG={
        "default-src": "'none'",
        "base-uri": "'none'",
        "script-src": [
            "'unsafe-inline'", # ignored
            "https:", # ignored
            "'strict-dynamic'"
        ],
        "connect-src": [
            "'self'",
            "https://*.sentry.io", # for error reporting
            "https://*.tiles.mapbox.com", # Mapbox GL JS
            "https://api.mapbox.com", # Mapbox GL JS
            "https://cdn.melown.com", # map viewer (3D only)
            "https://*.geo.admin.ch" # map viewer (3D only)
        ],
        "img-src": [
            "'self'",
            "data:",
            "blob:", # Mapbox GL JS
            "https://api.mapbox.com", # map viewer (2D only)
            "https://*.geo.admin.ch", # map viewer (2D only)
            "https://opencache.statkart.no", # map viewers (2D+3D)
            "https://maps.geogratis.gc.ca" # map viewer (2D only)
        ],
        "style-src": [
            "'self'",
            "'unsafe-inline'"
        ],
        "font-src": "'self'",
        "media-src": "'self'",
        "worker-src": "blob:", # Mapbox GL JS
        "child-src": "blob:", # Mapbox GL JS
    }
    #: A list of CSP sections to include a per-request nonce value in.
    CSP_NONCE_IN=["script-src"]

class Testing_config(object):
    """ Configuration to append. For remote/local testing purposes only. """

    #: Testing.
    TESTING=True
    #: Use a different database because tests drop all tables.
    MYSQL_DATABASE_DB="UNDISCLOSED"
    #: Required elapsed time before the user can re-submit.
    REQUIRED_TIME_GAP=1

class Production_config(Config):
    """ Configuration in production mode (online) based on the debug-mode config. """

    #: Do not enable debug mode when deploying in production.
    DEBUG=False
    #: Not testing.
    TESTING=False
    #: Sentry Data Source Name found from the Sentry web app.
    SENTRY_DSN="https://UNDISCLOSED@sentry.io/UNDISCLOSED"
    #: Browsers will only send cookies with requests over HTTPS if the cookie is marked *secure*.
    SESSION_COOKIE_SECURE=True
    #: Browsers will only send the remember me cookie with requests over HTTPS.
    REMEMBER_COOKIE_SECURE=True
    #: Browsers will only send the CSRF cookie with requests over HTTPS.
    CSRF_COOKIE_SECURE=True
    #: User name to access the MySQL database.
    MYSQL_DATABASE_USER="UNDISCLOSED"
    #: Password of the user.
    MYSQL_DATABASE_PASSWORD="UNDISCLOSED"
    #: Name of the MySQL database.
    MYSQL_DATABASE_DB="UNDISCLOSED"
    #: Type of caching: https://pythonhosted.org/Flask-Caching/
    CACHE_TYPE="filesystem"
    #: Directory to store cache. Make sure that nobody stores files there.
    CACHE_DIR=absolute_path("UNDISCLOSED")
    #: The default timeout that is used if no timeout is specified. Cache for 1 day.
    CACHE_DEFAULT_TIMEOUT=60*60*24
