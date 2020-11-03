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

from flaskr.mdx_figure import FigureExtension


def same_html(html_text: str, other_html_text: str, md: markdown.Markdown) -> bool:
    """ Removes all new lines and compare. """
    generated = md.convert(textwrap.dedent(html_text)).replace("\n", "")
    expected = textwrap.dedent(other_html_text).replace("\n", "")
    return generated == expected


@pytest.mark.parametrize(
    "data",
    (
        (
            """\
            Example:
                    
            ![Alt](image.jpg "Caption")
            """,
            """\
            <p>Example:</p>
            """,
        ),
        (
            """\
            Example:
            
            ![Alt](card2.jpg "Caption")
            """,
            """\
            <p>Example:</p>
            <figure>
            <div style="position:relative; width:100%; height:0; padding-top:66.67%">
            <img alt="Alt" data-height="600" data-width="900" src="card2.jpg" 
            style="position:absolute; top:0; left:0; max-width:100%;" />
            </div>
            <figcaption>Caption</figcaption>
            </figure>
            """,
        ),
    ),
)
def test_mdx_figure(data) -> None:
    """ Test the figure Markdown extension. """
    md = markdown.Markdown(
        extensions=[
            FigureExtension(),
        ]
    )
    assert same_html(data[0], data[1], md)


@pytest.mark.parametrize(
    "data",
    (
        (
            """\
            Example:
        
            ![Alt](pytest.png "Caption")
            """,
            """\
            <p>Example:</p>
            <figure>
            <div style="position:relative; width:100%; height:0; padding-top:95.33%">
            <img alt="Alt" data-height="143" data-width="150" src="pytest.png" 
            style="position:absolute; top:0; left:0; max-width:100%;" />
            </div>
            <figcaption>Caption</figcaption>
            </figure>
            """,
        ),
        (
            """\
            Example:
        
            ![Alt](pytest.png "Caption" config="no-resize")
            """,
            """\
            <p>Example:</p>
            <figure>
            <div style="height:143px">
            <img alt="Alt" data-height="143" data-width="150" src="pytest.png" />
            </div>
            <figcaption>Caption</figcaption>
            </figure>
            """,
        ),
        (
            """\
            Example:
        
            ![Alt](pytest.png "Caption" class="can-zoom-in" config="no-resize")
            """,
            """\
            <p>Example:</p>
            <figure>
            <div class="can-zoom-in" style="height:143px">
            <img alt="Alt" data-height="143" data-width="150" src="pytest.png" />
            </div>
            <figcaption>Caption</figcaption>
            </figure>
            """,
        ),
    ),
)
def test_mdx_figure_custom_src_path(data) -> None:
    md = markdown.Markdown(
        extensions=[
            FigureExtension(src_path="readme_media"),
        ]
    )
    assert same_html(data[0], data[1], md)
