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

import base64
import datetime
import functools
import glob
import hashlib
import io
import json
import logging
import os
import pickle
import random
import re
import secrets
import shutil
import stat
import string
import sys
import xml.etree.ElementTree as eltree
from fractions import Fraction
from pathlib import Path
from time import gmtime, strftime, strptime, time

import click
import exifread
import markdown
import mdx_sections
import pymysql
import requests
import sentry_sdk
import werkzeug.security
from flask import (
    Blueprint,
    Flask,
    Markup,
    abort,
    current_app,
    flash,
    g,
    jsonify,
    make_response,
    redirect,
    render_template,
    request,
    send_file,
    send_from_directory,
    session,
)
from flask.cli import with_appcontext
from flask_seasurf import SeaSurf
from flask_talisman import Talisman
from flaskext.markdown import Markdown
from PIL import Image, ImageDraw, ImageFont
from secure_cookie.cookie import SecureCookie
from sentry_sdk.integrations.flask import FlaskIntegration
from werkzeug.local import LocalProxy
from werkzeug.utils import secure_filename
from urllib.parse import quote, quote_plus, unquote_plus
from .mdx_amazon_affiliate_links import AmazonAffiliateLinksExtension
from .mdx_tweetable import TweetableExtension
from .typing import *
