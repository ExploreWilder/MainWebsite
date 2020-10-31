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
This script transform the Coverage.py JSON report into a pretty readme file.
It is executed by the coverage rule of the main Makefile.
"""

import io
import json
from typing import Dict

HEADER = """
# Tests

Run ``make test`` or ``make coverage`` in the main directory.
``make commit`` will run all tests and generate both the HTML and this readme file.

# Coverage Report

"""

FOOTER = """

This report has automatically been generated with ``make coverage``
and formatted with [coverage_to_readme.py](coverage_to_readme.py).

# Tools

[![Pytest](readme_media/pytest.png)](https://docs.pytest.org "Pytest")
[![Coverage.py](readme_media/coverage.png)](https://coverage.readthedocs.io "Coverage.py")
"""


def inner_line(join_tags: str, first_el: str, tab: Dict) -> str:
    return join_tags.join(
        (
            first_el,
            str(tab["num_statements"]),
            str(tab["missing_lines"]),
            str(tab["excluded_lines"]),
            str(round(tab["percent_covered"])) + "%",
        )
    )


def convert(
    coverage_file: io.TextIOBase,
    readme_file: io.TextIOBase,
    header: str = HEADER,
    footer: str = FOOTER,
) -> None:
    coverage_json = json.load(coverage_file)
    readme_file.write(
        header
        + "<table><thead><tr><th>"
        + "</th><th>".join(("Module", "Statements", "Missing", "Excluded", "Coverage"))
        + "</th></tr></thead><tbody>"
    )
    for file, data in coverage_json["files"].items():
        relative_file = "../flaskr/" + file.split("/")[-1]
        summary = data["summary"]
        readme_file.write(
            "<tr><td>"
            + inner_line(
                "</td><td>",
                '<a href="' + relative_file + '">' + relative_file + "</a>",
                summary,
            )
            + "</td></tr>"
        )
    readme_file.write(
        "</tbody><tfoot><tr><th>"
        + inner_line("</th><th>", "Total", coverage_json["totals"])
        + "</th></tr></tfoot></table>"
        + footer
    )


if __name__ == "__main__":
    with open("coverage.json") as coverage, open("readme.md", "w") as readme:
        convert(coverage, readme)
