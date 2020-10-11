/*!
 * Copyright 2018-2020 Clement
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are met:
 *
 * 1. Redistributions of source code must retain the above copyright notice,
 *    this list of conditions and the following disclaimer.
 *
 * 2. Redistributions in binary form must reproduce the above copyright notice,
 *    this list of conditions and the following disclaimer in the documentation
 *    and/or other materials provided with the distribution.
 *
 * 3. Neither the name of the copyright holder nor the names of its contributors
 *    may be used to endorse or promote products derived from this software
 *    without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
 * AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
 * ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
 * LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
 * CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
 * SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
 * INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
 * CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
 * ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
 * POSSIBILITY OF SUCH DAMAGE.
 */

/**
 * Default opacity of the Aerial Imagery basemap in percent.
 * Default value is 50.
 * 0 for total transparency (no aerial view, just the topo map).
 * 100 for full opacity (only the aerial view, the topo map is hidden).
 */
const default_opacity = 50;

/**
 * Duration of the zoom in/out animation in ms.
 * Default value is 300.
 */
const duration_zoom_animation = 300;

/**
 * URL to the map tiles proxy server. It can be an external link if a private key is not required.
 * Example: "/map/middleware/lds/" or "https://..."
 * Notice: Update the Content Security Policy in case of external requests
 */
const middleware_url = {
    "nz": "/map/middleware/lds/",
    "fr": "/map/middleware/ign",
    "topo-otm": "/map/vts_proxy/world/topo/otm/{z}/{x}/{y}.png",
    "topo-thunderforest": "/map/vts_proxy/world/topo/thunderforest/",
    "aerial-bing": "/map/vts_proxy/world/satellite/bing/{z}/{x}/{y}.jpeg",
    "aerial-mapbox": "https://api.mapbox.com/v4/mapbox.satellite/{z}/{x}/{y}@2x.jpg90?access_token=" + MAPBOX_PUB_KEY,
    "aerial-eox": "https://tiles.maps.eox.at/wmts/1.0.0/s2cloudless-2019_3857/default/GoogleMapsCompatible/{z}/{y}/{x}.jpg",
    "ca": "https://maps.geogratis.gc.ca/wms/canvec_en",
    "no": "https://opencache.statkart.no/gatekeeper/gk/gk.open_gmaps?layers=topo4&zoom={z}&x={x}&y={y}",
    "ch": "https://wmts10.geo.admin.ch/1.0.0/",
};

/**
 * OpenStreetMap attribution.
 */
const osm_attributions = '© <a href="http://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap contributors</a> (ODbL)'

/**
 * Attributions in addition to the aerial and topo layers attributions.
 */
const more_attributions = ' | Overview tiles ' + osm_attributions + ' | Map viewer © <a href="https://github.com/ExploreWilder/MainWebsite" target="_blank">Clement</a> (BSD-3-Clause)';

/**
 * List of world aerial layers.
 */
const world_aerial = ["aerial-bing", "aerial-mapbox", "aerial-eox"];

/**
 * List of world topo layers.
 */
const world_topo = ["topo-otm", "topo-thunderforest-outdoors", "topo-thunderforest-landscape"];

/**
 * Minimum padding (in pixels) to be cleared inside the view, around the GPX track.
 * Padding may be excessive due to discret zoom.
 */
const track_padding = 5;

/**
 * Default position when the map is displayed.
 * The position is updated once the track is downloaded.
 */
const default_gps_position = [0, 0];

/**
 * Default zoom when the map is displayed.
 * The zoom is updated once the track is downloaded.
 */
const default_zoom = 7;

/**
 * Minimum zoom of the map.
 * It does not make sense to allow the user to zoom more than the map resolution.
 */
const min_zoom = 1;

/**
 * Maximum zoom of the map.
 * It does not make sense to allow the user to zoom out of the available range.
 */
const max_zoom = 19;

/**
 * Fontawesome icon size.
 * Default is 1em.
 */
const icon_size = "1em";
