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

# Learn how to make a Python-Markdown extension:
# https://python-markdown.github.io/extensions/api/
# https://github.com/Python-Markdown/markdown/wiki/Tutorial-Altering-Markdown-Rendering

# Short links (from amzn.to) are not supported. Use full link only.

import json
import re

from markdown.extensions import Extension
from markdown.treeprocessors import Treeprocessor

AMAZON_MARKETPLACES = (
    ("fr", "France", 0),
    ("es", "Spain", 1),
    ("de", "Germany", 2),
    ("co.uk", "United Kingdom", 3),
    ("it", "Italy", 4),
    ("ca", "Canada", 5),
    ("com", "United States", 6),
    ("com", "New Zealand", 7),
    ("co.jp", "Japan", 8),
    ("com.au", "Australia", 9),
)


class InlineLinkProcessor(Treeprocessor):
    def run(self, root):
        for element in root.iter("a"):
            attrib = element.attrib
            href = attrib["href"]
            if href.startswith("https://www.amazon."):
                links = href.split(",")
                data_links = []
                pattern = re.compile(r"https://www\.(amazon\.[a-z]+(\.[a-z]+)?)/")
                for link in links:
                    amazon_website = re.match(pattern, link).group(1)
                    domain = amazon_website.split(".", 1)[-1]
                    marketplaces = [
                        (m[1], m[2]) for m in AMAZON_MARKETPLACES if m[0] == domain
                    ]
                    for marketplace in marketplaces:
                        data_links.append(
                            {
                                "website": amazon_website,
                                "marketplace": marketplace[0],
                                "flagId": marketplace[1],
                                "link": link,
                            }
                        )
                product_name = (
                    attrib.get("title") if attrib.get("title") else element.text
                )
                element.set("href", "#")
                element.set("data-amazon-product-name", product_name)
                element.set("data-amazon-affiliate-links", str(data_links))
                existing_classes = (
                    attrib.get("class") + " " if attrib.get("class") else ""
                )
                element.set("class", existing_classes + "amazon-affiliate-link")


class AmazonAffiliateLinksExtension(Extension):
    def extendMarkdown(self, md, md_globals):
        md.treeprocessors.register(InlineLinkProcessor(md), "inlinelinkprocessor", 15)
