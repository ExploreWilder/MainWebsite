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

from flask import (
    Flask, request, render_template, jsonify, abort, redirect, g, session,
    send_file, make_response, Markup, send_from_directory, Blueprint,
    current_app, flash
)
from flaskext.markdown import Markdown
from flask.cli import with_appcontext
from time import strftime, strptime, gmtime, time
from secure_cookie.cookie import SecureCookie # https://github.com/pallets/secure-cookie
from werkzeug.utils import secure_filename
from werkzeug.local import LocalProxy
from flask_talisman import Talisman
from flask_seasurf import SeaSurf
from PIL import Image, ImageFont, ImageDraw
from fractions import Fraction
from pathlib import Path
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
import werkzeug.security, markdown, exifread, pymysql, functools, click
import hashlib, os, sys, string, random, datetime, re, io, base64, secrets
import requests, json, stat, shutil, logging, pickle, glob, mdx_sections
import xml.etree.ElementTree as eltree

try:
    from urllib.parse import quote, quote_plus, unquote_plus
except ImportError:
    from urllib import quote, quote_plus, unquote_plus

from .mdx_amazon_affiliate_links import AmazonAffiliateLinksExtension
from .mdx_tweetable import TweetableExtension
from typing import List, Dict
