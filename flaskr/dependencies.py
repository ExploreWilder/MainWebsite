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
Globally used modules.
"""

# pylint: disable=unused-import

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
from time import gmtime
from time import strftime
from time import strptime
from time import time
from urllib.parse import quote
from urllib.parse import quote_plus
from urllib.parse import unquote_plus

import click
import exifread
import markdown
import mdx_sections
import pymysql
import requests
import sentry_sdk
import werkzeug.security
from flask import Blueprint
from flask import Flask
from flask import Markup
from flask import abort
from flask import current_app
from flask import flash
from flask import g
from flask import jsonify
from flask import make_response
from flask import redirect
from flask import render_template
from flask import request
from flask import send_file
from flask import send_from_directory
from flask import session
from flask.cli import with_appcontext
from flask_seasurf import SeaSurf
from flask_talisman import Talisman
from flaskext.markdown import Markdown
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
from secure_cookie.cookie import SecureCookie
from sentry_sdk.integrations.flask import FlaskIntegration
from werkzeug.local import LocalProxy
from werkzeug.utils import secure_filename

from .mdx_amazon_affiliate_links import AmazonAffiliateLinksExtension
from .mdx_tweetable import TweetableExtension
from .typing import *
