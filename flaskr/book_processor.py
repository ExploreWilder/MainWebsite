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

"""
Process a Markdown story. The generated HTML and ToC are cached.

The Markdown processors and extensions below are greatly inspired by the
default Markdown processors:

* Source: https://github.com/Python-Markdown/markdown
* Version: 3.3.3
* Licence: BSD-3-Clause

"""

import xml.etree.ElementTree as eTree

from markdown.extensions import Extension
from markdown.extensions.footnotes import FN_BACKLINK_TEXT
from markdown.extensions.footnotes import NBSP_PLACEHOLDER
from markdown.extensions.footnotes import FootnoteExtension
from markdown.extensions.footnotes import FootnoteInlineProcessor
from markdown.inlinepatterns import LinkInlineProcessor
from markdown.inlinepatterns import Pattern

from .utils import *

NOIMG = r"(?<!\!)"

# [text](~*~) or [text](<~*~>) or [text](~*~ "title")
BUTTON_LINK_RE = NOIMG + r"\["

TWEETABLE_RE = r"""
\[tweetable
  (?:\s+
    (?:
        url=["'](?P<url>[^"']+)["']
      |
        hashtags=["'](?P<hashtags>[^"']+)["']
    )
  \s*)*
\]
  (?P<quote>[^\[]+)
\[/tweetable\]
"""

HASHTAGS_RE = re.compile(r"^(?:(#\w+)(?:\s+(#\w+))*)?", re.UNICODE)


class ButtonInlineProcessor(LinkInlineProcessor):
    """ Return a button element from the given match. """

    def handleMatch(self, m, data):  # pylint: disable=invalid-name; override
        """ Override to customise the original link. """
        text, index, handled = self.getText(data, m.end(0))

        if not handled:
            return None, None, None  # pragma: no cover

        href, title, index, handled = self.getLink(data, index)
        if not handled:
            return None, None, None  # pragma: no cover

        if href == "~pdf~":
            icon = "fa-file-pdf"
            actual_href = text.replace(" ", "_") + ".pdf"  # local file
            actual_title = "Open PDF"
        elif href == "~video~":
            icon = "fa-video"
            actual_href = text  # external file
            actual_title = "Watch video"
        else:
            return None, None, None  # will be handled with the default processor

        a_tag = eTree.Element("a")
        a_tag.append(eTree.Element("i", {"class": "fas " + icon}))
        displayed_text = eTree.Element("span")
        displayed_text.text = " " + (text if title is None else title)
        a_tag.append(displayed_text)
        a_tag.set("href", actual_href)
        a_tag.set("class", "btn btn-light btn-outline-secondary btn-block")
        a_tag.set("role", "button")
        a_tag.set("target", "_blank")
        a_tag.set("rel", "noopener noreferrer")
        a_tag.set("title", actual_title)

        return a_tag, m.start(0), index


class ButtonMarkdownExtension(Extension):
    """ Figure extension. """

    def extendMarkdown(self, md):
        """ Add pieces to Markdown. """
        # priority = 162 > 160 (LinkInlineProcessor)
        md.inlinePatterns.register(
            ButtonInlineProcessor(BUTTON_LINK_RE, md), "button", 162
        )
        md.registerExtension(self)


class StaticMapInlineProcessor(LinkInlineProcessor):
    """ Return a static map element from the given match. """

    def __init__(self, pattern, md, config):
        """ Configure the static map and compile the regex. """
        self.config = config
        self.map_type_re = re.compile(r"~track/([^~]*)~")
        super().__init__(pattern, md)

    def handleMatch(self, m, data):  # pylint: disable=invalid-name; override
        """ Override to customise the original link. """
        text, index, handled = self.getText(data, m.end(0))

        if not handled:
            return None, None, None  # pragma: no cover

        href, _, index, handled = self.getLink(data, index)
        if not handled:
            return None, None, None  # pragma: no cover

        track_type = re.search(self.map_type_re, href)
        if track_type is None:
            return None, None, None  # pragma: no cover

        map_block = eTree.fromstring(
            render_template(
                "clickable_static_map.html",
                image_height=self.config["map_height"],
                book_id=self.config["book_id"],
                book_url=self.config["book_url"],
                gpx_file=text.replace(" ", "_"),
                gpx_title=text,
                country_code=track_type.group(1),
            )
        )

        return map_block, m.start(0), index


class StaticMapMarkdownExtension(Extension):
    """ Figure extension. """

    def __init__(self, **kwargs):
        self.config = {
            "map_height": [
                kwargs.get("map_height", None),
                "Static map relative height in percent considering the width at 100%.",
            ],
            "book_id": [
                kwargs.get("book_id", None),
                "Book ID.",
            ],
            "book_url": [
                kwargs.get("book_url", None),
                "Book URL.",
            ],
        }
        super().__init__(**kwargs)
        self.setConfigs(kwargs)

    def extendMarkdown(self, md):
        """ Add pieces to Markdown. """
        # priority = 163 > 160 (LinkInlineProcessor)
        md.inlinePatterns.register(
            StaticMapInlineProcessor(BUTTON_LINK_RE, md, self.getConfigs()),
            "static_map",
            163,
        )
        md.registerExtension(self)


class CustomFootnoteInlineProcessor(FootnoteInlineProcessor):
    """ InlinePattern for footnote markers in a document's body text. """

    markdown_link_re = re.compile(r"\[([^\]]*)\]\([^\)]*\)")

    def remove_markdown_link(self, text: str) -> str:
        """ Replaces all links the the title element, f.i. '[title](link)' becomes 'title'. """
        return re.sub(self.markdown_link_re, r"\1", text)

    def handleMatch(self, m, data):
        footnote_id = m.group(1)
        if footnote_id in self.footnotes.footnotes.keys():
            sup = eTree.Element("sup")
            a_tag = eTree.SubElement(sup, "a")
            sup.set("id", self.footnotes.makeFootnoteRefId(footnote_id, found=True))
            a_tag.set("href", "#" + self.footnotes.makeFootnoteId(footnote_id))
            a_tag.set("data-toggle", "tooltip")
            a_tag.set(
                "title",
                self.remove_markdown_link(self.footnotes.footnotes[footnote_id]),
            )
            a_tag.set("class", "footnote-ref")
            a_tag.text = str(
                list(self.footnotes.footnotes.keys()).index(footnote_id) + 1
            )
            return sup, m.start(0), m.end(0)
        return None, None, None  # pragma: no cover


class CustomFootnoteExtension(FootnoteExtension):
    """ Customised footnotes: removed the hr tag. """

    def extendMarkdown(self, md):
        """ Add pieces to Markdown. """
        super().extendMarkdown(md)
        # override:
        md.inlinePatterns.deregister("footnote")
        md.inlinePatterns.register(
            CustomFootnoteInlineProcessor(r"\[\^([^\]]*)\]", self), "footnote", 175
        )

    def makeFootnotesDiv(self, root):  # pylint: disable=invalid-name; override
        """ Return div of footnotes as et Element. """

        if not list(self.footnotes.keys()):
            return None  # pragma: no cover

        div = eTree.Element("div")
        div.set("class", "footnote")
        ol_tag = eTree.SubElement(div, "ol")
        surrogate_parent = eTree.Element("div")

        for index, footnote_id in enumerate(self.footnotes.keys(), start=1):
            li_tag = eTree.SubElement(ol_tag, "li")
            li_tag.set("id", self.makeFootnoteId(footnote_id))
            # Parse footnote with surrogate parent as li cannot be used.
            # List block handlers have special logic to deal with li.
            # When we are done parsing, we will copy everything over to li.
            self.parser.parseChunk(surrogate_parent, self.footnotes[footnote_id])
            for element in list(surrogate_parent):
                li_tag.append(element)
                surrogate_parent.remove(element)
            backlink = eTree.Element("a")
            backlink.set("href", "#" + self.makeFootnoteRefId(footnote_id))
            backlink.set("class", "footnote-backref")
            backlink.set("title", self.getConfig("BACKLINK_TITLE") % index)
            backlink.text = FN_BACKLINK_TEXT

            if li_tag:
                node = li_tag[-1]
                if node.tag == "p":
                    node.text = node.text + NBSP_PLACEHOLDER
                    node.append(backlink)
                else:  # pragma: no cover; not used
                    p_tag = eTree.SubElement(li_tag, "p")
                    p_tag.append(backlink)
        return div


class TweetablePattern(Pattern):
    """InlinePattern for tweetable quotes"""

    def __init__(self, pattern, config, markdown_instance=None):
        super().__init__(pattern)
        self.inc = 0
        self.pattern = pattern
        self.compiled_re = re.compile(
            "^(.*?)%s(.*?)$" % pattern, re.DOTALL | re.UNICODE | re.VERBOSE
        )

        # Api for Markdown to pass safe_mode into instance
        self.safe_mode = False
        if markdown_instance:
            self.m_markdown = markdown_instance

        self.config = config

    @staticmethod
    def format_hashtags(hashtags, separator=" ", strip_hash=False):
        """ Transform an array of hashtags into a string. Remove the # if existing. """
        return separator.join(hashtags).replace("#" if strip_hash else "", "")

    def handleMatch(self, m):
        my_quote, url, hashtags = [
            "" if m.group(a) is None else m.group(a).strip()
            for a in ("quote", "url", "hashtags")
        ]
        hashtags = [
            h for h in re.match(HASHTAGS_RE, hashtags).groups() if h is not None
        ]
        if not url.startswith("http"):
            url = self.config["default_url"]
        quoted_quote = '"' + my_quote + '"'
        snippet = render_template(
            "mdx_tweetable_snippet.html",
            id=self.inc,
            url=url,
            urlq=quote_plus(url),
            quote=my_quote,
            quoteq=quote_plus(quoted_quote.encode("utf-8")),
            hashtags=self.format_hashtags(hashtags, separator=",", strip_hash=True),
            brand_name=self.config["brand_name"],
            twitter_username=self.config["twitter_username"],
            description=quote_plus(
                (quoted_quote + self.format_hashtags(hashtags)).encode("utf-8")
            ),
            email_subject=quote_plus(
                "Quote" + (" from " + self.config["brand_name"])
                if self.config["brand_name"]
                else ""
            ),
            email_body=quote_plus(
                (quoted_quote + self.format_hashtags(hashtags) + " - " + url).encode(
                    "utf-8"
                )
            ),
            name_tumblr=quote_plus(
                "Quote" + (" from " + self.config["brand_name"])
                if self.config["brand_name"]
                else ""
            ),
        )
        self.inc += 1
        placeholder = self.m_markdown.htmlStash.store(snippet)
        return placeholder


class TweetableExtension(Extension):
    """
    This Markdown extension creates blockquotes with social network buttons.
    The idea is to embed shareable quotes right into the text in order to
    increase content sharing since people prefer to quote a story rather than
    its headline.

    This extension is greatly inspired by the following one:

    * Source: https://github.com/max-arnold/markdown-tweetable
    * Copyright: © 2014 Max Arnold
    * Licence: MIT

    """

    def __init__(self, **kwargs):
        self.config = {
            "twitter_username": [
                kwargs.get("twitter_username", None),
                "Twitter account username.",
            ],
            "brand_name": [kwargs.get("brand_name", None), "Website brand name."],
            "default_url": [
                kwargs.get("default_url", None),
                "URL to share if set to # in the quote.",
            ],
        }
        super().__init__(**kwargs)
        self.setConfigs(kwargs)

    def extendMarkdown(self, md):
        tweetable_md_pattern = TweetablePattern(
            TWEETABLE_RE, self.getConfigs(), markdown_instance=md
        )
        md.inlinePatterns.register(tweetable_md_pattern, "tweetable", 165)
        md.registerExtension(self)


class BookProcessor:
    """
    Process a Markdown story.

    Notice:
        The Markdown file and the processed Markdown (HTML files) are TRUSTED.
        Do NOT allow changes on those files by anyone but the webmaster.
    """

    #: Processed book.
    html: Optional[str] = None

    #: Table of content.
    toc: Optional[str] = None

    def __init__(
        self,
        app: Flask,
        default_url: str,
        book_id: int,
        book_url: str,
        book_filename: str,
    ) -> None:
        """
        Args:
            app: The Flask app.
            book_id (int): Book ID.
            book_url (str): Book URL.
            book_filename (str): Book file name.
        """
        self.path_to_book_dir = os.path.join(app.config["SHELF_FOLDER"], book_url)
        self.path_to_md_book = os.path.join(self.path_to_book_dir, book_filename)
        self.p_md_book = Path(self.path_to_md_book)
        self.p_html_content = Path(self.path_to_md_book + ".html")
        self.p_html_toc = Path(self.path_to_md_book + ".toc.html")
        self.markdown = markdown.Markdown(
            extensions=app.config["MD_EXT"]
            + [
                "mdx_sections",
                ButtonMarkdownExtension(),
                CustomFootnoteExtension(),
                FigureExtension(src_path=self.path_to_book_dir),
                StaticMapMarkdownExtension(
                    map_height=(
                        100
                        * app.config["MAPBOX_STATIC_IMAGES"]["height"]
                        / app.config["MAPBOX_STATIC_IMAGES"]["width"]
                    ),
                    book_id=book_id,
                    book_url=book_url,
                ),
                TweetableExtension(
                    twitter_username=app.config["TWITTER_ACCOUNT"]["screen_name"],
                    brand_name=app.config["BRAND_NAME"],
                    default_url=default_url,
                ),
            ]
        )
        self.current_app = app

    @staticmethod
    def get_empty_book() -> Dict[str, str]:
        """ Returns an empty book dictionary. Static member. """
        return {"html": "", "toc": ""}

    def is_outdated(self) -> bool:
        """ Returns true if the HTML and the ToC are older than the Markdown file. """
        return not (
            self.p_html_content.is_file()
            and self.p_html_toc.is_file()
            and self.p_html_content.stat().st_mtime > self.p_md_book.stat().st_mtime
        )

    def print_book(self) -> Dict[str, str]:
        """
        Returns:
            A dictionary ``{ "html": ..., "toc": ... }``
        """
        if self.is_outdated():
            with self.p_md_book.open("r", encoding="utf-8") as markdown_file:
                html = self.markdown.convert(markdown_file.read())
                self.p_html_content.open("w", encoding="utf-8").write(html)
                # pylint: disable=no-member
                toc = self.markdown.toc  # type: ignore[attr-defined]
                self.p_html_toc.open("w", encoding="utf-8").write(toc)  # type: ignore[arg-type]
        else:
            html = self.p_html_content.open("r", encoding="utf-8").read()
            toc = self.p_html_toc.open("r", encoding="utf-8").read()
        return {"html": Markup(html), "toc": Markup(toc)}  # type: ignore[arg-type]
