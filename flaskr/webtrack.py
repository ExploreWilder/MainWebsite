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
Utility module for the WebTrack format.
WebTrack specifications:
https://github.com/ExploreWilder/WebTrack.js/blob/main/SPEC.md
"""

# pylint: disable=invalid-name; allow one letter variables (f.i. c for character, n for number)

import pyproj

from .typing import *


class WebTrack:
    """
    Implementation of the WebTrack format.
    Refer to map.py for an example of use.
    TODO: full read capability
    """

    #: Big-endian order as specified.
    byteorder: str = "big"

    #: GPS to Web Mercator converter with coordinates in the GIS order: (lon, lat).
    proj = pyproj.Transformer.from_crs("epsg:4326", "epsg:3857", always_xy=True)

    #: The WebTrack file data.
    webtrack: Any = None

    #: The data to write into the WebTrack.
    data_src: Dict = {}

    #: The total amount of segments in the current WebTrack.
    total_segments: int = 0

    #: The total amount of waypoints in the current WebTrack.
    total_waypoints: int = 0

    def __init__(
        self,
        format_name: bytes = b"webtrack-bin",
        format_version: bytes = b"0.1.0",
    ):
        self.format_name = format_name
        self.format_version = format_version

    def get_format_information(self, file_path: str = "") -> Dict[str, bytes]:
        """
        Returns the format name and version.

        Returns:
            The default values if `file_path` is not specified.
            The information from the file `file_path` if specified.
        """
        if file_path:
            with open(file_path, "rb") as stream:
                self.webtrack = stream
                self._read_format_information()
        return {
            "format_name": self.format_name,
            "format_version": self.format_version,
        }

    def to_file(self, file_path: str, data: Dict) -> None:
        """ Open the binary file and write the WebTrack data. """
        with open(file_path, "wb") as stream:
            self.webtrack = stream
            self.data_src = data
            self.total_segments = len(data["segments"])
            self.total_waypoints = len(data["waypoints"])

            self._write_format_information()
            self._write_segment_headers()
            self._write_track_information()
            self._write_segments()
            self._write_waypoints()

    def _w_sep(self):
        """ Append a separator to the stream. """
        self.webtrack.write(b":")

    def _w_sep_wpt(self):
        """ Append a waypoint separator to the stream. """
        self.webtrack.write(b"\n")

    def _w_uint8(self, c: int) -> None:
        """ Append an unsigned byte (character) to the stream. """
        self.webtrack.write(bytes([c]))

    def _w_uint16(self, n: int) -> None:
        """ Append an unsigned 2-byte integer to the stream. """
        self.webtrack.write(
            (int(round(n))).to_bytes(2, byteorder=self.byteorder, signed=False)
        )

    def _w_int16(self, n: int) -> None:
        """ Append a signed 2-byte integer to the stream. """
        self.webtrack.write(
            (int(round(n))).to_bytes(2, byteorder=self.byteorder, signed=True)
        )

    def _w_uint32(self, n: int) -> None:
        """ Append an unsigned 4-byte integer to the stream. """
        self.webtrack.write(
            (int(round(n))).to_bytes(4, byteorder=self.byteorder, signed=False)
        )

    def _w_int32(self, n: int) -> None:
        """ Append a signed 4-byte integer to the stream. """
        self.webtrack.write(
            (int(round(n))).to_bytes(4, byteorder=self.byteorder, signed=True)
        )

    def _w_str(self, s: str) -> None:
        """ Append a string to the stream. The string is UTF-8 encoded. """
        self.webtrack.write(s.encode("utf-8"))

    def _write_format_information(self) -> None:
        """ Write the "Format Information" section of the WebTrack file. """
        self.webtrack.write(self.format_name)
        self._w_sep()
        self.webtrack.write(self.format_version)
        self._w_sep()
        self._w_uint8(self.total_segments)
        self._w_uint16(self.total_waypoints)

    def _read_up_to_separator(self, separator: bytes = b":") -> bytes:
        """
        Read the WebTrack until the 1-byte `separator`.

        Returns:
            The block read excluding the separator.
        """
        c = self.webtrack.read(1)
        arr_bytes = bytearray([c[0]])
        while c != separator:
            c = self.webtrack.read(1)
            arr_bytes.append(c[0])
        return bytes(arr_bytes[:-1])

    def _read_format_information(self) -> None:
        """ Read the "Format Information" section of the WebTrack file. """
        if self.webtrack.tell() > 0:
            self.webtrack.seek(0)
        self.format_name = self._read_up_to_separator()
        self.format_version = self._read_up_to_separator()

    def _write_segment_headers(self) -> None:
        """ Write the "Segment Headers" section of the WebTrack file. """
        segments = self.data_src["segments"]
        for segment in segments:
            self.webtrack.write(b"E" if segment["withEle"] else b"F")
            self._w_uint32(len(segment["points"]))

    def _write_track_information(self) -> None:
        """ Write the "Track Information" section of the WebTrack file. """
        track_info = self.data_src["trackInformation"]
        self._w_uint32(track_info["length"])
        self._w_int16(track_info["minimumAltitude"])
        self._w_int16(track_info["maximumAltitude"])
        self._w_uint32(track_info["elevationGain"])
        self._w_uint32(track_info["elevationLoss"])

    def _write_segments(self) -> None:
        """ Write all segments in the stream. """
        segments = self.data_src["segments"]
        for segment in segments:
            points = segment["points"]
            with_ele = segment["withEle"]
            web_prev_point: Union[Tuple[float, float], None] = None
            for point in points:
                web_curr_point = self.proj.transform(point[0], point[1])  # lon, lat
                if web_prev_point is None:
                    self._w_int32(web_curr_point[0])  # lon
                    self._w_int32(web_curr_point[1])  # lat
                else:
                    delta_lon = round(web_curr_point[0]) - round(
                        web_prev_point[0]  # pylint: disable=unsubscriptable-object
                    )
                    delta_lat = round(web_curr_point[1]) - round(
                        web_prev_point[1]  # pylint: disable=unsubscriptable-object
                    )
                    self._w_int16(delta_lon)
                    self._w_int16(delta_lat)
                web_prev_point = web_curr_point
                self._w_uint16(point[2] / 10.0)
                if with_ele:
                    self._w_int16(point[3])

    def _write_waypoints(self) -> None:
        """ Write all waypoints in the stream. """
        waypoints = self.data_src["waypoints"]
        for waypoint in waypoints:
            web_point = self.proj.transform(waypoint[0], waypoint[1])
            self._w_int32(web_point[0])
            self._w_int32(web_point[1])
            if waypoint[2]:  # with elevation
                self.webtrack.write(b"E")
                self._w_int16(waypoint[3])
            else:  # without elevation
                self.webtrack.write(b"F")
            if waypoint[4]:  # symbole
                self._w_str(waypoint[4])
            self._w_sep_wpt()
            if waypoint[5]:  # name
                self._w_str(waypoint[5])
            self._w_sep_wpt()
