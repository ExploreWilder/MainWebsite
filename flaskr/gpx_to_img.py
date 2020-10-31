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
Create a map from GPX data.
"""

from typing import Dict
from urllib.parse import quote_plus as mod_quote_plus

import gpxpy as mod_gpxpy
import polyline as mod_polyline

DEFAULT_MARGIN_POINTS_NO: int = 3
DEFAULT_MAX_ITER: int = 20


class MyGPXTrackSegment(mod_gpxpy.gpx.GPXTrackSegment):
    """ Add a custom simplification. """

    def _distance_guesser(
        self,
        points_no: int,
        margin_points_no: int = DEFAULT_MARGIN_POINTS_NO,
        max_iter: int = DEFAULT_MAX_ITER,
    ) -> int:
        """
        Find out the max distance for the 'simplify' procedure with the number of points as a requirement.

        Args:
            points_no (int): The number of points to expect.
            margin_points_no (int): The bound/range around the expected number of points, the lesser the slower.
            max_iter (int): Limit the number of calls to 'simplify' to avoid infinite loop if the margin is too small.

        Returns:
            int: The max_distance parameter to give to 'simplify'.
        """
        min_distance = 0
        max_distance = 1000
        for _ in range(max_iter):
            dicho = int((max_distance + min_distance) / 2)
            current_segment = self.clone()
            current_segment.simplify(dicho)
            current_points_no = current_segment.get_points_no()
            if current_points_no > (points_no + margin_points_no):
                min_distance = dicho
            elif current_points_no < (points_no - margin_points_no):
                max_distance = dicho
            else:
                break
        return dicho

    def simplify_with_distance_guesser(
        self,
        points_no: int,
        margin_points_no: int = DEFAULT_MARGIN_POINTS_NO,
        max_iter: int = DEFAULT_MAX_ITER,
    ) -> None:
        """
        Simplify the segment to about `points_no` more or less `margin_points_no`.

        Args:
            points_no (int): The number of points to expect.
            margin_points_no (int): The bound around the expected number of points, the lesser the slower.
            max_iter (int): Limit the number of calls to 'simplify' to avoid infinite loop if the margin is too small.
        """
        self.simplify(self._distance_guesser(points_no, margin_points_no, max_iter - 1))


def gpx_to_src(
    gpx: mod_gpxpy.gpx.GPX,
    conf: Dict,
    margin_points_no: int = DEFAULT_MARGIN_POINTS_NO,
    max_iter: int = DEFAULT_MAX_ITER,
) -> str:
    """
    Returns a url to a static JPG image that fit the track in the GPX file.
    Static image overview: https://docs.mapbox.com/help/how-mapbox-works/static-maps/
    Mapbox doc: https://docs.mapbox.com/api/maps/#static-images

    Args:
        gpx: GPX data.
        conf (Dict): Mapbox username, style_id, image width/height, access token, logo visibility.
        margin_points_no (int): The bound around the expected number of points, the lesser the slower.
        max_iter (int): Limit the number of calls to 'simplify' to avoid infinite loop if the margin is too small.
    """
    # merge all track segments to ease the simplification process and fill gaps between tracks
    merged_segments = MyGPXTrackSegment()
    for track in gpx.tracks:
        for segment in track.segments:
            merged_segments.join(segment)

    merged_segments.simplify_with_distance_guesser(
        conf["points"], margin_points_no, max_iter
    )
    coordinates = []
    for point in merged_segments.points:
        coordinates.append((point.latitude, point.longitude))

    point_fmt = "{}-{}+{}({:.7},{:.7})"
    path_fmt = "path-{}+{}-{}({})"
    return (
        "https://api.mapbox.com/styles/v1/{}/{}/static/"
        + point_fmt
        + ","
        + point_fmt
        + ","
        + path_fmt
        + "/auto/{}x{}{}?access_token={}&logo={}"
    ).format(
        conf["username"],
        conf["style_id"],
        conf["style"]["start"]["name"],
        conf["style"]["start"]["label"],
        conf["style"]["start"]["color"],
        coordinates[0][1],
        coordinates[0][0],
        conf["style"]["end"]["name"],
        conf["style"]["end"]["label"],
        conf["style"]["end"]["color"],
        coordinates[-1][1],
        coordinates[-1][0],
        conf["style"]["path"]["stroke_width"],
        conf["style"]["path"]["stroke_color"],
        conf["style"]["path"]["stroke_opacity"],
        mod_quote_plus(mod_polyline.encode(coordinates)),
        conf["width"],
        conf["height"],
        "@2x" if conf["@2x"] else "",
        conf["access_token"],
        "true" if conf["logo"] else "false",
    )
