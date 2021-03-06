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

import textwrap
import xml.etree.ElementTree as eTree
from urllib.parse import quote_plus

import markdown
import pytest
from flask import render_template

from flaskr.book_processor import BookProcessor
from flaskr.book_processor import ButtonMarkdownExtension
from flaskr.book_processor import CustomFootnoteExtension
from flaskr.book_processor import StaticMapMarkdownExtension
from flaskr.book_processor import TweetableExtension
from flaskr.book_processor import TweetablePattern


@pytest.mark.parametrize(
    "data",
    (
        (
            """\
                Example:
                
                [Great Story](~pdf~)
            """,
            """\
                <p>Example:</p>
                <p>
                <a class="btn btn-light btn-outline-secondary btn-block" 
                href="Great_Story.pdf" 
                rel="noopener noreferrer" 
                role="button" 
                target="_blank" 
                title="Open PDF">
                <i class="fas fa-file-pdf"></i>
                <span> Great Story</span>
                </a>
                </p>
            """,
        ),
        (
            """\
                Example:
                
                [https://example.com/myvideo](~video~ "Great Story")
            """,
            """\
                <p>Example:</p>
                <p>
                <a class="btn btn-light btn-outline-secondary btn-block" 
                href="https://example.com/myvideo" 
                rel="noopener noreferrer" 
                role="button" 
                target="_blank" 
                title="Watch video">
                <i class="fas fa-video"></i>
                <span> Great Story</span>
                </a>
                </p>
            """,
        ),
        (
            """\
                Example:
                
                [Great Story](link)
            """,
            """\
                <p>Example:</p>
                <p>
                <a href="link">Great Story</a>
                </p>
            """,
        ),
        (
            """\
                Example:
                
                ![Great Story](~pdf~)
            """,
            """\
                <p>Example:</p>
                <p>
                <img alt="Great Story" src="~pdf~" />
                </p>
            """,
        ),
    ),
)
def test_button_markdown_extension(data) -> None:
    """ Test the button Markdown extension. """
    md = markdown.Markdown(
        extensions=[
            ButtonMarkdownExtension(),
        ]
    )
    produced_html = md.convert(textwrap.dedent(data[0])).replace("\n", "")
    expected_html = textwrap.dedent(data[1]).replace("\n", "")
    assert produced_html == expected_html


def elements_equal(e1, e2):
    """
    Compare two XML trees.
    Based on:
    https://stackoverflow.com/questions/7905380/testing-equivalence-of-xml-etree-elementtree
    """
    if e1.tag != e2.tag:
        return False
    if e1.text != e2.text:
        return False
    if e1.tail != e2.tail:
        return False
    if e1.attrib != e2.attrib:
        return False
    if len(e1) != len(e2):
        return False
    return all(elements_equal(c1, c2) for c1, c2 in zip(e1, e2))


def test_static_map_markdown_extension(app) -> None:
    """ Test the static map Markdown extension. """
    with app.app_context():
        map_height = (
            100
            * app.config["MAPBOX_STATIC_IMAGES"]["height"]
            / app.config["MAPBOX_STATIC_IMAGES"]["width"]
        )
        book_id = 42
        book_url = "super_story"
        gpx = "Great Hike"
        country_code = "nz"
        md = markdown.Markdown(
            extensions=[
                StaticMapMarkdownExtension(
                    map_height=map_height, book_id=book_id, book_url=book_url
                ),
            ]
        )
        produced_html = eTree.fromstring(
            md.convert("[" + gpx + "](~track/" + country_code + "~)")
        )
        # process the template in the same way as the extension:
        expected_html = eTree.fromstring(
            "<p>\n"
            + render_template(
                "clickable_static_map.html",
                image_height=map_height,
                book_id=book_id,
                book_url=book_url,
                gpx_file=gpx.replace(" ", "_"),
                gpx_title=gpx,
                country_code=country_code,
            )
            + "\n</p>"
        )
        assert elements_equal(produced_html, expected_html)


def test_tweetable(app) -> None:
    """ Test the tweetable Markdown extension. """
    with app.app_context():  # render_template() needs the app context
        default_url = "https://example.com/awesome_article.html#conclusion"
        quote = "Python forever!"
        quoted_quote = '"' + quote + '"'
        hashtags = ["#love", "#hate"]
        brand_name = "Bob"
        twitter_username = "Roger"
        description = quote_plus(
            (quoted_quote + TweetablePattern.format_hashtags(hashtags)).encode("utf-8")
        )
        email_body = quote_plus(
            (
                quoted_quote
                + TweetablePattern.format_hashtags(hashtags)
                + " - "
                + default_url
            ).encode("utf-8")
        )
        md = markdown.Markdown(
            extensions=[
                TweetableExtension(
                    twitter_username=twitter_username,
                    brand_name=brand_name,
                    default_url=default_url,
                ),
            ]
        )
        produced_html = md.convert(
            textwrap.dedent(
                """\
                [tweetable hashtags="#love #hate"]
                Python forever!
                [/tweetable]
                """
            )
        )
        expected_html = render_template(
            "mdx_tweetable_snippet.html",
            id=0,
            url=default_url,
            urlq=quote_plus(default_url),
            quote=quote,
            quoteq=quote_plus(quoted_quote.encode("utf-8")),
            hashtags=TweetablePattern.format_hashtags(
                hashtags, separator=",", strip_hash=True
            ),
            brand_name=brand_name,
            twitter_username=twitter_username,
            description=description,
            email_subject=quote_plus("Quote from " + brand_name),
            email_body=email_body,
            name_tumblr=quote_plus("Quote from " + brand_name),
        )
        assert produced_html == expected_html
        custom_url = "https://example.com/good_article"
        description = quote_plus(quoted_quote.encode("utf-8"))
        email_body = quote_plus((quoted_quote + " - " + custom_url).encode("utf-8"))
        produced_html = md.convert(
            textwrap.dedent(
                """\
                [tweetable url="https://example.com/good_article"]
                Python forever!
                [/tweetable]
                """
            )
        )
        expected_html = render_template(
            "mdx_tweetable_snippet.html",
            id=1,
            url=custom_url,
            urlq=quote_plus(custom_url),
            quote=quote,
            quoteq=quote_plus(quoted_quote.encode("utf-8")),
            hashtags="",
            brand_name=brand_name,
            twitter_username=twitter_username,
            description=description,
            email_subject=quote_plus("Quote from " + brand_name),
            email_body=email_body,
            name_tumblr=quote_plus("Quote from " + brand_name),
        )
        assert produced_html == expected_html


@pytest.mark.parametrize(
    "data",
    (
        (
            """\
                Example[^1]
                
                [^1]: Cañón means canyon in Spanish
            """,
            """\
                <p>
                Example
                <sup id="fnref:1">
                <a class="footnote-ref" 
                data-toggle="tooltip" 
                href="#fn:1" 
                title="Cañón means canyon in Spanish">1</a>
                </sup>
                </p>
                <div class="footnote">
                <ol>
                <li id="fn:1">
                <p>Cañón means canyon in Spanish&#160;
                <a class="footnote-backref" 
                href="#fnref:1" 
                title="Jump back to footnote 1 in the text">&#8617;</a>
                </p>
                </li>
                </ol>
                </div>
            """,
        ),
        (
            """\
                Example[^1]
    
                [^1]: Cañón means [canyon](link) in Spanish
            """,
            """\
                <p>
                Example
                <sup id="fnref:1">
                <a class="footnote-ref" 
                data-toggle="tooltip" 
                href="#fn:1" 
                title="Cañón means canyon in Spanish">1</a>
                </sup>
                </p>
                <div class="footnote">
                <ol>
                <li id="fn:1">
                <p>Cañón means <a href="link">canyon</a> in Spanish&#160;
                <a class="footnote-backref" href="#fnref:1" title="Jump back to footnote 1 in the text">&#8617;</a>
                </p>
                </li>
                </ol>
                </div>
            """,
        ),
    ),
)
def test_custom_footnotes(data) -> None:
    """ Test the custom footnotes Markdown extension. """
    md = markdown.Markdown(
        extensions=[
            CustomFootnoteExtension(),
        ]
    )
    produced_html = md.convert(textwrap.dedent(data[0])).replace("\n", "")
    expected_html = textwrap.dedent(data[1]).replace("\n", "")
    assert produced_html == expected_html


def test_empty_book():
    assert BookProcessor.get_empty_book() == {"html": "", "toc": ""}
