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
Transform images into figures. The image size is saved into the img tag and its
style is updated to force the figure to have the final height from the beginning.

The existing figure processors are under the GPL version, incompatible with the BSD.
Alternatives are:
* https://github.com/flywire/caption (GPL 3.0)
* https://github.com/Evidlo/markdown_captions (GPL 3)
* https://github.com/jdittrich/figureAltCaption (GPL 2)

Learn how to make a Python-Markdown extension:
    https://python-markdown.github.io/extensions/api/
"""

import logging
import os
import re
from typing import Any
from typing import Match
from typing import Optional
from typing import Tuple
from xml.etree.ElementTree import Element
from xml.etree.ElementTree import SubElement

from markdown.blockprocessors import BlockProcessor
from markdown.extensions import Extension
from PIL import Image

Logger = logging.getLogger("mdx_figure")


class FigureProcessor(BlockProcessor):
    """ Figure processor used by the extension. """

    #: Regex used to get the image metadata.
    regex_run = re.compile(
        r"!\[([^\]]*)]\(([^\) ]*) \"([^\"]*)\"( class=\"([^\"]*)\")?( config=\"([^\"]*)\")?\)"
    )

    #: Regex used to find images.
    regex_test = re.compile(
        r"!\[[^\]]*]\([^\)]* \"[^\"]*\"( class=\"[^\"]*\")?( config=\"[^\"]*\")?\)"
    )

    def __init__(self, parser, config):
        """ Set the directory path of the image. """
        self.config = config
        super().__init__(parser)

    def test(self, parent: Element, block) -> Optional[Match[Any]]:
        """ The test condition to run self.run(). """
        return re.match(self.regex_test, block)

    @staticmethod
    def create_image_node(
        parent: Element, alt: str, src: str, width: int, height: int
    ) -> Element:
        """ Create an image tag under its parent and returns it. """
        img = SubElement(parent, "img")
        img.set("alt", alt)
        img.set("src", src)
        img.set("data-width", str(width))
        img.set("data-height", str(height))
        return img

    def image_size(self, src: str) -> Optional[Tuple[int, int]]:
        """ Open the image and returns its size or none. """
        img_path = (
            os.path.join(self.config["src_path"], src)
            if self.config["src_path"] is not None
            else src
        )
        try:
            with Image.open(img_path) as image:
                return image.size
        except FileNotFoundError as err:
            Logger.debug("%s", str(err))
            return None

    def run(self, parent: Element, blocks) -> bool:
        """ Process the one-line block. """
        raw_block: Match[Any] = re.search(self.regex_run, blocks[0])  # type: ignore[assignment]
        alt, src, desc = raw_block.group(1), raw_block.group(2), raw_block.group(3)
        class_attr = raw_block.group(5)
        config = raw_block.group(7)
        size = self.image_size(src)
        if size is None:  # remove the image
            blocks.pop(0)
            return False
        figure = SubElement(parent, "figure")
        div = SubElement(figure, "div")
        if class_attr:
            div.set("class", class_attr)
        img = self.create_image_node(div, alt, src, size[0], size[1])
        Logger.debug(
            "%s (%dx%d) alt='%s', class='%s'",
            src,
            size[0],
            size[1],
            alt,
            class_attr if class_attr else "",
        )
        if config and "no-resize" in config:
            div.set(
                "style",
                "height:" + str(size[1]) + "px",
            )
        else:
            rel_height = str(round(100 * size[1] / size[0], 2)) + "%"
            img.set("style", "position:absolute; top:0; left:0; max-width:100%;")
            div.set(
                "style",
                "position:relative; width:100%; height:0; padding-top:" + rel_height,
            )
        if desc:
            caption = SubElement(figure, "figcaption")
            caption.text = desc
        blocks.pop(0)
        return True


class FigureExtension(Extension):
    """ Figure extension. """

    def __init__(self, **kwargs):
        self.config = {
            "src_path": [
                kwargs.get("src_path", None),
                "Path to the image directory.",
            ],
        }
        super().__init__(**kwargs)
        self.setConfigs(kwargs)

    def extendMarkdown(self, md):
        """ Add pieces to Markdown. """
        md.parser.blockprocessors.register(
            FigureProcessor(md.parser, self.getConfigs()), "figure_processor", 175
        )
        md.registerExtension(self)


def makeExtension(*args, **kwargs):  # pylint: disable=invalid-name; as specified
    """ Returns the extension instance. """
    return FigureExtension(*args, **kwargs)
