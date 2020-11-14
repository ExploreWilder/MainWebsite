/*!
 * Copyright (c) 2020 Clement
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

var browser;
var renderer;
var map;
var geodata;
var lineGeometry = null;
var demoTexture = null;
var usedMouseCoords = [0, 0];
var linePoint;
var lineSegment = 0;
var lastLineSegment = -1;
var distancePointer;
var pathDistance = 0;

/**
 * Add extra height to be sure the track is above the terrain.
 * The Z-buffer in the ``map_player_config/webtrack.style.json`` is also tuned.
 * It's actually a hack raised in `GitHub <https://github.com/melowntech/vts-browser-js/issues/201>`_
 */
var extra_height = 45;

/**
 * Identifier of the timeout used to hide the pointer on the map
 * after being inactive for a while.
 */
var timeoutHideMapPointerID = null;

/**
 * Minimum timeout in ms after which the tooltip and pointer are hidden
 * after being inactive. The timeout extends when the browser is
 * lagging.
 */
var timeoutHideMap = 1000;

/**
 * True when the pointer and tooltip are not redrew on the map.
 */
var partialRedraw = false;

/**
 * Add or move the position pointed by the user on the map along the track.
 * @param tooltip_item - The tooltip item.
 * @param data - Not used but required by the function call. Could be used in the future.
 */
function update_hiker_pos(tooltip_item, data) {
    pathDistance = tooltip_item.xLabel * 1000;
    linePoint = lineGeometry.getPathPoint(pathDistance);
    partialRedraw = false;
    map.redraw();
}

/**
 * Setup the entire interface. A popup will appear if the browser doesn't support
 * WebGL, otherwise the map is created in the HTML ``div`` tag identified
 * as `map-player`. The map configuration is based on the JSON file.
 * The `inspector <https://github.com/melowntech/vts-browser-js/wiki/VTS-Browser-Inspector-Mode>`_ is enabled.
 */
function startMapPlayerInterface() {
    var url = new RegExp("/([^/]*)/([^/]*)/([^/]*)/([^/#]*)#*$", "g").exec(
        window.location.href
    );

    if (url == null) {
        return;
    }

    book_id = url[1];
    book_url = url[2].toLowerCase();
    gpx_name = url[3];

    browser = vts.browser("map-player", {
        map: VTS_BROWSER_CONFIG + "main_config.json",
        inspector: true,
    });

    // check whether browser is supported
    if (!browser) {
        window.alert("Your web browser does not support WebGL");
        return;
    }

    // create ui control with info pointers
    var infoPointers = browser.ui.addControl(
        "info-pointers",
        '<div id="distance-div" class="distance-div tooltip-arrow"></div>' +
            '<div id="height-div" class="distance-div"></div>' +
            '<div id="height-div2" class="pointer-div2">' +
            "</div>"
    );

    distancePointer = infoPointers.getElement("distance-div");
    renderer = browser.renderer;

    // add mouse events to map element
    var mapElement = browser.ui.getMapElement();
    mapElement.on("mousemove", onMouseMove);
    mapElement.on("mouseleave", onMouseLeave);

    // callback once the map config is loaded
    browser.on("map-loaded", onMapLoaded);

    // callback when path hovered
    browser.on("geo-feature-hover", onFeatureHover);

    loadTexture();

    $("#dropdownMenuBoundLayer .dropdown-item").on("click", function (event) {
        event.preventDefault();
        $("#dropdownMenuBoundLayer .active").removeClass("active");
        $(this).addClass("active");
        onSwitchView($(this).attr("data-boundlayer"));
    });

    manage_subnav_click();

    $("#gpxInfo .close").click(function () {
        current_menu_on_focus = null;
        $(this).closest(".card-menu").fadeOut();
        return false;
    });

    $('abbr[data-toggle="tooltip"].layer-info').tooltip({
        animation: true,
        placement: "bottom",
        delay: { show: 100, hide: 0 },
        container: "#subNavbarNav",
        trigger: "hover",
    });
}
startMapPlayerInterface();

/**
 * Load icon used for displaying path point
 */
function loadTexture() {
    var demoImage = vts.utils.loadImage(
        "/static/images/placemark_circle.png",
        function () {
            demoTexture = renderer.createTexture({ source: demoImage });
        }
    );
}

/**
 * Add render slot for dynamic rendering
 */
function onMapLoaded() {
    map = browser.map;
    map.addRenderSlot("custom-render", onCustomRender, true);
    map.moveRenderSlotAfter("after-map-render", "custom-render");
    loadTrack();
}

/**
 * Download the binary data and update the interface.
 */
function loadTrack() {
    var oReq = new XMLHttpRequest();
    oReq.open("GET", get_webtrack_url(book_id, gpx_name), true);
    // https://developer.mozilla.org/en-US/docs/Web/API/XMLHttpRequest/Sending_and_Receiving_Binary_Data
    oReq.responseType = "arraybuffer";

    oReq.onload = function (oEvent) {
        if (oReq.status == 500) {
            // exception raised in map.py:profile_file()
            var response_str = new TextDecoder("utf-8").decode(
                new Uint8Array(oReq.response)
            );
            window.alert("Failed to fetch the WebTrack: " + response_str);
            return;
        }
        let webtrack = new WebTrack();
        webtrack.loadWebTrack(oReq.response);
        webtrack_to_geodata(webtrack);

        let data = {
            statistics: webtrack.getTrackInfo(),
            points: webtrack.getTrack()[0].points,
        };
        track_info(data);
        display_gpx_buttons();
    };

    oReq.send();
}

/**
 * Read the WebTrack and save the features into `source`.
 * @param {WebTrack} webtrack see map_player.loadTrack().
 */
function webtrack_to_geodata(webtrack) {
    geodata = map.createGeodata();
    geodata.addGroup("tracks");

    var trk = webtrack.getTrack()[0].points;
    var coords = [];
    for (var i = 0; i < trk.length; i++) {
        point = [
            trk[i][0], // longitude
            trk[i][1], // latitude
            trk[i][3] + extra_height, // elevation
        ];
        coords.push(point);
        geodata.addPoint(point, "fix", {}, "", "EPSG:3857");
    }
    geodata.addLineString(coords, "fix", {}, "some-path", "EPSG:3857");

    geodata.addGroup("waypoints");
    var wpt = webtrack.getWaypoints();
    for (var i = 0; i < wpt.length; i++) {
        switch (wpt[i].sym) {
            case "Campground":
            case "Fishing Hot Spot Facility":
                // https://vts-geospatial.org/tutorials/geojson-part2.html?highlight=addpointarray#extending-existing-data
                geodata.addPoint(
                    [wpt[i].lon, wpt[i].lat, wpt[i].ele + extra_height],
                    "fix",
                    { title: wpt[i].name },
                    "way-points",
                    "EPSG:3857"
                );
                break;
        }
    }

    onHeightProcessed(); // if unknown heights: geodata.processHeights('node-by-precision', 62, onHeightProcessed);
}

/**
 * When heights are converted then we can create free layer
 * and display that layer on the map
 */
function onHeightProcessed() {
    //extract geometry with id == 'some-path'
    lineGeometry = geodata.extractGeometry("some-path");

    //center map postion to track gemetery
    centerPositonToGeometry(lineGeometry);

    //make free layer
    var style = VTS_BROWSER_CONFIG + "webtrack.style.json";
    var freeLayer = geodata.makeFreeLayer(style);

    // self-attribution.
    // The {Y} VTS macro is not used because only 2 digits are desired.
    // The Markdown-style link is not used because relative.
    const current_year = new Date().getFullYear();
    freeLayer.credits = {
        clement: {
            id: 10,
            notice: `{copy}2015-${("" + current_year).slice(
                -2
            )} <a href="/about" target="_blank">Clement</a>`,
        },
    };

    //add free layer to the map
    map.addFreeLayer("gpxgeodata", freeLayer);

    //add free layer to the list of free layers
    //which will be rendered on the map
    var view = map.getView();
    view.freeLayers.gpxgeodata = {};
    map.setView(view);
}

/**
 * Move map position to the center of geometry and adjust
 * view extent to size of geometry
 */
function centerPositonToGeometry(geometry) {
    if (!geometry.getElements()) {
        return;
    }

    //get detailed info about map reference frame
    var refFrame = map.getReferenceFrame();
    var navigationSrsId = refFrame.navigationSrs;
    var navigationSrs = map.getSrsInfo(navigationSrsId);
    var physicalSrsId = refFrame.physicalSrs;
    var physicalSrs = map.getSrsInfo(physicalSrsId);
    var i,
        li,
        midPoint = [0, 0, 0],
        line,
        vec3 = vts.vec3;

    //find center of geometry
    for (i = 0, li = geometry.getElements() + 1; i < li; i++) {
        if (i == li - 1) {
            //last line point
            line = geometry.getElement(i - 1);
            coords = line[1];
        } else {
            line = geometry.getElement(i);
            coords = line[0];
        }

        midPoint[0] += coords[0];
        midPoint[1] += coords[1];
        midPoint[2] += coords[2];
    }

    midPoint[0] /= li;
    midPoint[1] /= li;
    midPoint[2] /= li;

    // construct line which goes through the center of geometry
    // and mesure most distant point from this line

    var cameraPosition = midPoint;
    var cameraVector = [
        -cameraPosition[0],
        -cameraPosition[1],
        -cameraPosition[2],
    ];
    vec3.normalize(cameraVector);

    var viewExtent = 500;

    for (i = 0, li = geometry.getElements() + 1; i < li; i++) {
        if (i == li - 1) {
            //last line point
            line = geometry.getElement(i - 1);
            coords = line[1];
        } else {
            line = geometry.getElement(i);
            coords = line[0];
        }

        //get line point distance
        var ab = cameraVector;
        var av = [
            coords[0] - cameraPosition[0],
            coords[1] - cameraPosition[1],
            coords[2] - cameraPosition[2],
        ];

        var b = [
            cameraPosition[0] + cameraVector[0],
            cameraPosition[1] + cameraVector[1],
            cameraPosition[2] + cameraVector[2],
        ];
        var bv = [coords[0] - b[0], coords[1] - b[1], coords[2] - b[2]];

        var af = [0, 0, 0];
        vec3.cross(ab, av, af);

        var d = (vec3.length(bv) / vec3.length(ab)) * 2;

        if (d > viewExtent) {
            viewExtent = d;
        }
    }

    //limit view extent according to planet radius
    if (viewExtent > navigationSrs.a * 1.4) {
        viewExtent = navigationSrs.a * 1.4;
    }

    //convert coods from physical to nav
    var navCoords = vts.proj4(
        physicalSrs.srsDef,
        navigationSrs.srsDef,
        midPoint
    );
    navCoords[2] = 0;

    //set new map positon
    var pos = map.getPosition();
    pos.setCoords(navCoords);
    pos.setOrientation([0, -60, 0]);
    pos.setViewExtent(viewExtent);
    map.setPosition(pos);
}

/**
 * Event handler.
 */
function onMouseMove(event) {
    if (map) {
        var coords = event.getMouseCoords();
        usedMouseCoords = coords;
        //set map to hover cusor over provided coordinates permanently
        map.hover(coords[0], coords[1], true);
    }
}

/**
 * Event handler.
 */
function onMouseLeave(event) {
    if (map) {
        var coords = event.getMouseCoords();
        //stop cursor hovering
        map.hover(coords[0], coords[1], false);
    }
}

/**
 * Event handler.
 */
function onFeatureHover(event) {
    lineSegment = event.element;

    //if there is a path, and the current segment is different from the last one, and not out of range
    if (
        lineGeometry &&
        lastLineSegment != lineSegment &&
        lineSegment <= lineGeometry.getElements()
    ) {
        //get distance of cursor on the line segment
        var res = lineGeometry.getRelationToCanvasPoint(
            lineSegment,
            usedMouseCoords[0],
            usedMouseCoords[1]
        );

        //get path length to line segment and length of the segment itself
        var lineSegmentInfo = lineGeometry.getPathLengthToElement(lineSegment);

        //compute path distance to point where cursor is hovering over the track
        pathDistance =
            lineSegmentInfo.lengthToElement +
            lineSegmentInfo.elementLengh * vts.math.clamp(res.distance, 0, 1);

        //get point coodinates
        linePoint = lineGeometry.getPathPoint(pathDistance);

        //will draw tooltip and pointer
        partialRedraw = false;

        //force redraw map (we have to redraw track point)
        map.redraw();

        //remember the current segment ID to skip the next event if it is the same ID
        lastLineSegment = lineSegment;
    }
}

/**
 * Event handler drawing the pointer and the tooltip on the map.
 */
function onCustomRender() {
    if (
        demoTexture &&
        pathDistance &&
        lineGeometry &&
        linePoint &&
        !partialRedraw
    ) {
        //check whether texture is loaded

        //get canvas postion of the track point
        var p = map.convertCoordsFromPhysToCanvas(linePoint);

        //display distance pointer (tooltip) in the track point coordinates
        var rect = distancePointer.getRect();
        distancePointer.setStyle("display", "block");
        distancePointer.setStyle("left", p[0] - rect.width * 0.5 + "px");
        distancePointer.setStyle("top", p[1] - 50 + "px");
        distancePointer.setHtml((pathDistance * 0.001).toFixed(1) + " km");

        //draw image (pointer) at the last line point
        renderer.drawImage({
            rect: [p[0] - 12 * 1.5, p[1] - 12 * 1.5, 24 * 1.5, 24 * 1.5],
            texture: demoTexture,
            color: [255, 0, 0, 255],
            depth: p[2],
            depthTest: false,
            blend: true,
        });

        if (timeoutHideMapPointerID !== null) {
            window.clearTimeout(timeoutHideMapPointerID);
            timeoutHideMapPointerID = null;
        }
        timeoutHideMapPointerID = window.setTimeout(function () {
            var rect = distancePointer.getRect();
            distancePointer.setStyle("display", "none");
            partialRedraw = true;
            //hide the tooltip and pointer on the map
            map.redraw();
        }, timeoutHideMap);
    }
}

/**
 * Change the active bound layer on the surface.
 * It could be a composition of layers if separated by commas.
 *
 * Based on the `VTS Browser API Examples
 * <https://github.com/melowntech/vts-browser-js/wiki/Examples>`_:
 * `Switching bound layers
 * <https://jsfiddle.net/jdhakmnt/>`_.
 */
function onSwitchView(newBoundLayer) {
    if (map) {
        var existingFreeLayers = map.getView().freeLayers;
        map.setView({
            surfaces: {
                "melown-viewfinder-world": newBoundLayer
                    .split(",")
                    .map((s) => s.trim()),
            },
            freeLayers: existingFreeLayers,
        });
    }
}
