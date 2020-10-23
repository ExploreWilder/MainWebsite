# -*- coding: utf-8 -*-

#
# From https://github.com/max-arnold/markdown-tweetable
#

#
# Copyright © 2014 Max Arnold. All rights reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
#

#
# Copyright 2020 Clement
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

from __future__ import print_function, unicode_literals
import re
from urllib.parse import quote_plus
from markdown.extensions import Extension
from markdown.inlinepatterns import Pattern

TWEETABLE_RE = r'''
\[tweetable
  (?:\s+
    (?:
        alt=["'](?P<alt>[^"']+)["']
      |
        url=["'](?P<url>[^"']+)["']
      |
        hashtags=["'](?P<hashtags>[^"']+)["']
    )
  \s*)*
\]
  (?P<quote>[^\[]+)
\[/tweetable\]
'''

HASHTAGS_RE = re.compile(r'^(?:(#\w+)(?:\s+(#\w+))*)?', re.UNICODE)

# TODO: email
NETWORKS = ('twitter', 'vkontakte', 'facebook', 'tumblr', 'linkedin', 'email',)

SNIPPET = '''<blockquote class="tweetable">
<div class="btn-group dropdown dropdown-share-on-social-network tweetable-buttons px-1 ml-3">
    <button class="btn btn-sm btn-outline-secondary dropdown-toggle" type="button" id="dropdownMenuShareSocialMediaButtonsMD{id}" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
        <i class="fas fa-share-alt"></i>
    </button>
    <div class="dropdown-menu dropdown-menu-right share-on-social-network" aria-labelledby="dropdownMenuShareSocialMediaButtonsMD{id}">
        {buttons}
    </div>
</div>
<p>{quote}</p>
</blockquote>'''

# TODO: find a way to get current page url if not specified
# TODO: button text localization

ICON_FACEBOOK = (
    '<i class="fab fa-facebook-f"></i>'
)

SNIPPET_FACEBOOK = (
    '<a class="dropdown-item tweetable-button" '
    'title="Copy the text, then click to share on Facebook" '
    'data-toggle="tooltip" '
    'href="https://www.facebook.com/sharer/sharer.php?u={urlq}" '
    'role="button" '
    'target="_blank">'
    '{icon_facebook} Facebook</a>'
)

def create_facebook_button(url, quote, hashtags, config):
    return config['snippet_facebook'].format(
        url=url,
        urlq=quote_plus(url),
        quote=quote_plus((quote + format_hashtags(hashtags)).encode('utf-8')),
        icon_facebook=config['icon_facebook']
    )


ICON_LINKEDIN = (
    '<i class="fab fa-linkedin-in"></i>'
)

SNIPPET_LINKEDIN = (
    '<a class="dropdown-item tweetable-button" '
    'title="Click to share on LinkedIn" '
    'data-toggle="tooltip" '
    'href="https://www.linkedin.com/shareArticle?mini=true&url={urlq}&title={quote}" '
    'role="button" '
    'target="_blank">'
    '{icon_linkedin} LinkedIn</a>'
)

def create_linkedin_button(url, quote, hashtags, config):
    return config['snippet_linkedin'].format(
        url=url,
        urlq=quote_plus(url),
        quote=quote_plus(quote.encode('utf-8')),
        icon_linkedin=config['icon_linkedin']
    )


ICON_TWITTER = (
    '<i class="fab fa-twitter"></i>'
)

SNIPPET_TWITTER = (
    '<a class="dropdown-item tweetable-button" '
    'title="Click to share on Twitter" '
    'data-toggle="tooltip" '
    'href="https://twitter.com/intent/tweet?text={quote}{via_username}&url={urlq}&hashtags={hashtags}" '
    'role="button" '
    'target="_blank">'
    '{icon_twitter} Twitter</a>'
)

def create_twitter_button(url, quote, hashtags, config):
    # TODO: validate length
    # short_url_length_https: 23, short_url_length: 22, total_length: 140
    return config['snippet_twitter'].format(
        url=url,
        urlq=quote_plus(url),
        via_username=('&via='+config['twitter_username']) if config['twitter_username'] else '',
        quote=quote_plus(quote.encode('utf-8')),
        hashtags=format_hashtags(hashtags, separator=',', strip_hash=True),
        icon_twitter=config['icon_twitter']
    )


ICON_VKONTAKTE = (
    '<i class="fab fa-vk"></i>'
)

# TODO: optional source
SNIPPET_VKONTAKTE = (
    '<a class="dropdown-item tweetable-button" '
    'title="Click to share on VKontakte" '
    'data-toggle="tooltip" '
    'href="https://vk.com/share.php?url={urlq}&title={quote}" '
    'role="button" '
    'target="_blank">'
    '{icon_vkontakte} VKontakte</a>'
)

def create_vkontakte_button(url, quote, hashtags, config):
    return config['snippet_vkontakte'].format(
        url=url,
        urlq=quote_plus(url),
        quote=quote_plus((quote + format_hashtags(hashtags)).encode('utf-8')),
        icon_vkontakte=config['icon_vkontakte']
    )


ICON_TUMBLR = (
    '<i class="fab fa-tumblr"></i>'
)

SNIPPET_TUMBLR = (
    '<a class="dropdown-item tweetable-button" '
    'title="Click to share on Tumblr" '
    'data-toggle="tooltip" '
    'href="http://www.tumblr.com/share/link?url={urlq}&amp;name={name}&amp;description={description}" '
    'role="button" '
    'target="_blank">'
    '{icon_tumblr} Tumblr</a>'
)

def create_tumblr_button(url, quote, hashtags, config):
    return config['snippet_tumblr'].format(
        url=url,
        urlq=quote_plus(url),
        name=quote_plus("Quote" + (" from " + config['brand_name']) if config['brand_name'] else ''),
        description=quote_plus((quote + format_hashtags(hashtags)).encode('utf-8')),
        icon_tumblr=config['icon_tumblr']
    )


ICON_EMAIL = (
    '<i class="fas fa-envelope"></i>'
)

SNIPPET_EMAIL = (
    '<a class="dropdown-item tweetable-button" '
    'title="Click to share via email" '
    'data-toggle="tooltip" '
    'role="button" '
    'href="mailto:?subject={email_subject}&amp;body={email_body}">'
    '{icon_email} Email</a>'
)

def create_email_button(url, quote, hashtags, config):
    return config['snippet_email'].format(
        email_subject=quote_plus("Quote" + (" from " + config['brand_name']) if config['brand_name'] else ''),
        email_body=quote_plus((quote + format_hashtags(hashtags) + " - " + url).encode('utf-8')),
        icon_email=config['icon_email']
    )

BUTTONS = {
    'facebook': create_facebook_button,
    'linkedin': create_linkedin_button,
    'twitter': create_twitter_button,
    'vkontakte': create_vkontakte_button,
    'tumblr': create_tumblr_button,
    'email': create_email_button,
}

def create_buttons(url, quote, hashtags, config):
    buttons = [BUTTONS[n](url, quote, hashtags, config) for n in config['networks']]
    return '\n'.join(buttons)


def format_hashtags(hashtags, separator=' ', strip_hash=False):
    return separator.join(hashtags).replace('#' if strip_hash else '', '')


class TweetablePattern(Pattern):
    """InlinePattern for tweetable quotes"""
    def __init__(self, pattern, config, markdown_instance=None):
        self.inc = 0
        self.pattern = pattern
        self.compiled_re = re.compile("^(.*?)%s(.*?)$" % pattern, re.DOTALL | re.UNICODE | re.VERBOSE)

        # Api for Markdown to pass safe_mode into instance
        self.safe_mode = False
        if markdown_instance:
            self.m_markdown = markdown_instance

        self.config = config

    def handleMatch(self, m):
        quote, alt, url, hashtags = ['' if m.group(a) is None else m.group(a).strip() for a in ('quote', 'alt', 'url', 'hashtags')]
        alt_quote = alt or quote
        hashtags = [h for h in re.match(HASHTAGS_RE, hashtags).groups() if h is not None]
        if not url.startswith('http'):
            url = '#' # JavaScript will replace this character with window.location.href
        buttons = create_buttons(url, '"' + alt_quote + '"', hashtags, self.config)
        snippet = self.config['snippet'].format(quote=quote, buttons=buttons, id=self.inc)
        self.inc += 1
        placeholder = self.m_markdown.htmlStash.store(snippet)
        return placeholder


class TweetableExtension(Extension):
    def __init__(self, **kwargs):
        self.config = {
            'twitter_username': [kwargs.get("twitter_username", None), 'Twitter account username.'],
            'brand_name': [kwargs.get("brand_name", None), 'Website brand name.'],

            'networks': [NETWORKS, 'Social networks for sharing.'],
            'snippet': [SNIPPET, 'HTML snippet.'],

            'snippet_facebook': [SNIPPET_FACEBOOK, 'Facebook HTML snippet.'],
            'icon_facebook': [ICON_FACEBOOK, 'Facebook icon.'],

            'snippet_linkedin': [SNIPPET_LINKEDIN, 'LinkedIn HTML snippet.'],
            'icon_linkedin': [ICON_LINKEDIN, 'LinkedIn icon.'],

            'snippet_twitter': [SNIPPET_TWITTER, 'Twitter HTML snippet.'],
            'icon_twitter': [ICON_TWITTER, 'Twitter icon.'],

            'snippet_vkontakte': [SNIPPET_VKONTAKTE, 'VKontakte HTML snippet.'],
            'icon_vkontakte': [ICON_VKONTAKTE, 'VKontakte icon.'],
            
            'snippet_tumblr': [SNIPPET_TUMBLR, 'Tumblr HTML snippet.'],
            'icon_tumblr': [ICON_TUMBLR, 'Tumblr icon.'],
            
            'snippet_email': [SNIPPET_EMAIL, 'Email HTML snippet.'],
            'icon_email': [ICON_EMAIL, 'Email icon.'],
        }
        super(TweetableExtension, self).__init__(**kwargs)

        # Accept not only list/tuple but also a string, with values separated by semicolon
        networks = kwargs.pop('networks', '')
        if not isinstance(networks, (list, tuple)):
            networks = tuple(filter(None, networks.split(';')))

        # Validate network list
        diff = set(networks).difference(set(NETWORKS))
        if diff:
            raise ValueError('Unsupported social network(s): {}'.format(', '.join(list(diff))))

        networks = networks or NETWORKS
        self.setConfig('networks', networks)

        self.setConfigs(kwargs)

    def extendMarkdown(self, md, md_globals):
        tweetable_md_pattern = TweetablePattern(TWEETABLE_RE, self.getConfigs(), markdown_instance=md)
        md.inlinePatterns.register(tweetable_md_pattern, 'tweetable', 165)
        md.registerExtension(self)


def makeExtension(*args, **kwargs):
    return TweetableExtension(*args, **kwargs)
