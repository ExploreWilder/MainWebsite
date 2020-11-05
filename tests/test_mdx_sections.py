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

import markdown
import pytest

from flaskr.mdx_sections import OutlineExtension
from flaskr.utils import verbose_md_ext


@pytest.mark.parametrize(
    "data",
    (
        (
            """\
            # Super Title
            
            ## Sub Title
            
            Blabla
            
            ## Second Sub Title
            
            Hello
            """,
            """\
            <section class="section1">
            <div class="anchor" id="super-title"></div>
            <h1>Super Title</h1>
            <section class="section2">
            <div class="anchor" id="sub-title"></div>
            <h2>Sub Title</h2>
            <p>Blabla</p>
            </section>
            <section class="section2">
            <div class="anchor" id="second-sub-title"></div>
            <h2>Second Sub Title</h2>
            <p>Hello</p>
            </section>
            </section>
            """,
        ),
    ),
)
def test_mdx_sections(data) -> None:
    """ Test the sections Markdown extension. """
    md = markdown.Markdown(
        extensions=verbose_md_ext(
            [
                "toc",
            ]
        )
        + [
            OutlineExtension(),
        ]
    )
    generated = md.convert(textwrap.dedent(data[0])).replace("\n", "")
    expected = textwrap.dedent(data[1]).replace("\n", "")
    assert generated == expected
