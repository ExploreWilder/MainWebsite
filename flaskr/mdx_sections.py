#
# Copyright © 2011, 2012 [The active archives contributors](http://activearchives.org/)
# Copyright © 2011, 2012 [Michael Murtaugh](http://automatist.org/)
# Copyright © 2011, 2012, 2017 [Alexandre Leray](http://stdin.fr/)
# Copyright © 2020 Clement
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
Sections Markdown Extension: wraps the document logical sections (as implied by h1-h6 headings).

.. note::
    Based on the `mdx_outline <https://github.com/aleray/mdx_outline>`_ Markdown
    extension. The changes from the original extensions are:

    * Removed all deprecation warnings,
    * Added anchors for the CSS-offset trick,
    * Added tests.

.. note::
    The `toc extension <https://python-markdown.github.io/extensions/toc/>`_
    is required to automatically generate a unique ``id`` attribute for headers.
    This `Sections` extension moves the ``id`` to a created anchor preceding the
    title. Those invisible anchors are used by the frontend to dynamically update
    the URL according to the current visible section. The anchor is not actually
    the title itself in order to create a CSS offset which is used to offset the
    title below the top navigation bar (Bootstrap navbar).
"""

import re
import xml.etree.ElementTree as eTree

from markdown.extensions import Extension
from markdown.treeprocessors import Treeprocessor

__version__ = "1.4.0"


class OutlineProcessor(Treeprocessor):
    """ Section processor used by the extension. """

    def __init__(self, md, config):
        """ Configure. """
        self.wrapper_tag = config.get("wrapper_tag")[0]
        self.wrapper_cls = config.get("wrapper_cls")[0]
        self.move_attrib = config.get("move_attrib")[0]
        super().__init__(md)

    def process_nodes(self, node):
        """ Process nodes. """
        sections = []
        pattern = re.compile(r"^h(\d)")
        wrapper_cls = self.wrapper_cls

        for child in list(node):
            match = pattern.match(child.tag.lower())

            if match:
                depth = int(match.group(1))

                section = eTree.SubElement(node, self.wrapper_tag)
                anchor = eTree.SubElement(section, "div")
                anchor.set("class", "anchor")
                section.append(child)

                if self.move_attrib:
                    for key, value in list(child.attrib.items()):
                        if key == "id":
                            anchor.set("id", value)
                        else:
                            section.set(key, value)  # pragma: no cover; not used
                        del child.attrib[key]

                node.remove(child)

                if "%(LEVEL)d" in self.wrapper_cls:
                    wrapper_cls = self.wrapper_cls % {"LEVEL": depth}

                cls = section.attrib.get("class")
                if cls:
                    section.attrib["class"] = " ".join(
                        [cls, wrapper_cls]
                    )  # pragma: no cover; not used
                elif wrapper_cls:  # no class attribute if wrapper_cls==''
                    section.attrib["class"] = wrapper_cls

                contained = False

                while sections:
                    container, container_depth = sections[-1]
                    if depth <= container_depth:
                        sections.pop()
                    else:
                        contained = True
                        break

                if contained:
                    container.append(section)
                    node.remove(section)

                sections.append((section, depth))

            else:
                if sections:
                    container, container_depth = sections[-1]
                    container.append(child)
                    node.remove(child)

    def run(self, root):
        self.process_nodes(root)
        return root


class OutlineExtension(Extension):
    """ Sections Markdown Extension. """

    def __init__(self, *args, **kwargs):  # pylint: disable=unused-argument
        self.config = {
            "wrapper_tag": ["section", "Tag name to use, default: section"],
            "wrapper_cls": [
                "section%(LEVEL)d",
                "Default CSS class applied to sections",
            ],
            "move_attrib": [True, "Move header attributes to the wrapper"],
        }
        super().__init__(**kwargs)

    def extendMarkdown(self, md):
        """ Add pieces to Markdown. """
        ext = OutlineProcessor(md, self.config)
        # run after the toc, which has a priority = 5
        md.treeprocessors.register(ext, "outline", 4)


def makeExtension(*args, **kwargs):  # pylint: disable=invalid-name; as specified
    """ Returns the extension instance. """
    return OutlineExtension(*args, **kwargs)  # pragma: no cover
