/*!
 * Copyright (c) 2020 Melown Technologies SE
 * 
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are met:
 * 
 * *  Redistributions of source code must retain the above copyright notice,
 *    this list of conditions and the following disclaimer.
 * 
 * *  Redistributions in binary form must reproduce the above copyright
 *    notice, this list of conditions and the following disclaimer in the
 *    documentation and/or other materials provided with the distribution.
 * 
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
 * AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
 * ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
 * LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
 * CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
 * SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
 * INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
 * CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
 * ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
 * POSSIBILITY OF SUCH DAMAGE.
 */

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

/*
 * Information about the mapConfig.json:
 * https://github.com/melowntech/vts-mapproxy/blob/master/docs/resources.md
 */

var browser, renderer, map;
var geodata, lineGeometry = null;
var demoTexture = null;
var usedMouseCoords = [0,0];
var linePoint, lineSegment = 0, lastLineSegment = -1;
var distancePointer;
var pathDistance = 0;

/**
 * Add or move the position pointed by the user on the map along the track.
 */
function update_hiker_pos(tooltip_item, data) {
    var el = data.datasets[tooltip_item.datasetIndex].data[tooltip_item.index];
    pathDistance = tooltip_item.xLabel * 1000;
    linePoint = lineGeometry.getPathPoint(pathDistance);
    map.redraw();
}

/**
 * Setup the entire interface.
 */
(function startMapPlayerInterface() {
    var url = new RegExp("/([^/]*)/([^/]*)/([^/]*)/([^/#]*)#*$", "g").exec(window.location.href);

    if(url == null) {
        return;
    }

    book_id = url[1];
    book_url = url[2].toLowerCase();
    gpx_name = url[3];

    // create map in the html div with id 'map-player'
    // parameter 'map' sets path to the map which will be displayed
    // you can create your own map on melown.com
    // position parameter is described in documentation 
    // https://github.com/Melown/vts-browser-js/wiki/VTS-Browser-Map-API#position
    // view parameter is described in documentation 
    // https://github.com/Melown/vts-browser-js/wiki/VTS-Browser-Map-API#definition-of-view
    browser = vts.browser('map-player', {
        map: VTS_BROWSER_CONFIG,
        position : [ 'obj', 16.402434, 48.079867, 'float', 0.00, 9.60, -90.00, 0.00, 2595540.94, 45.00 ]
    });

    //check whether browser is supported
    if (!browser) {
        console.log('Your web browser does not support WebGL');
        return;
    }

    // create ui control with info pointers
    var infoPointers = browser.ui.addControl('info-pointers',
        '<div id="distance-div" class="distance-div tooltip-arrow"></div>' +
        '<div id="height-div" class="distance-div"></div>' +
        '<div id="height-div2" class="pointer-div2">' +
        '</div>');

    distancePointer = infoPointers.getElement('distance-div');
    renderer = browser.renderer;

    //add mouse events to map element
    var mapElement = browser.ui.getMapElement();
    mapElement.on('mousemove', onMouseMove);
    mapElement.on('mouseleave', onMouseLeave);
    
    //callback once the map config is loaded
    browser.on('map-loaded', onMapLoaded);

    //callback when path hovered
    browser.on('geo-feature-hover', onFeatureHover);

    loadTexture();

    $('#dropdownMenuBoundLayer .dropdown-item').on('click', function (event) {
        event.preventDefault();
        $('#dropdownMenuBoundLayer .active').removeClass("active");
        $(this).addClass("active");
        onSwitchView($(this).attr("data-boundlayer"));
    });

    manage_subnav_click();

    $("#gpxInfo .close").click(function() {
        current_menu_on_focus = null;
        $(this).closest(".card-menu").fadeOut();
        return false;
    });

    $('abbr[data-toggle="tooltip"].layer-info').tooltip({
        animation: true,
        placement: "bottom",
        delay: { "show": 100, "hide": 0 },
        container: "#subNavbarNav",
        trigger: "hover"
    });
})();

/**
 * Load icon used for displaying path point
 */
function loadTexture() {
    var demoImage = vts.utils.loadImage(
        '/static/images/placemark_circle.png',
        (function(){
            demoTexture = renderer.createTexture({ source: demoImage });
        })
    );
}

/**
 * Add render slot for dynamic rendering
 */
function onMapLoaded() {
    map = browser.map;
    map.addRenderSlot('custom-render', onCustomRender, true);
    map.moveRenderSlotAfter('after-map-render', 'custom-render');
    loadTrack();
}

/**
 * Download the data and update the interface.
 */
function loadTrack() {
    var oReq = new XMLHttpRequest();
    oReq.open("GET", get_webtrack_url(book_id, book_url, gpx_name), true);
    // https://developer.mozilla.org/en-US/docs/Web/API/XMLHttpRequest/Sending_and_Receiving_Binary_Data
    oReq.responseType = "arraybuffer";

    oReq.onload = function(oEvent) {
        if(oReq.status == 500) { // exception raised in map.py:profile_file()
            var response_str = new TextDecoder("utf-8").decode(new Uint8Array(oReq.response));
            window.alert("Failed to fetch the WebTrack: " + response_str);
            return;
        }
        let webtrack = new WebTrack();
        webtrack.loadWebTrack(oReq.response);
        webtrack_to_geodata(webtrack);

        let data = {
            statistics: webtrack.getTrackInfo(),
            points: webtrack.getTrack()[0].points
        }
        track_info(data);
        display_gpx_buttons();
    };
    
    oReq.send();
}

/**
 * Read the `webtrack` and save the features into `source`.
 * @param {WebTrack} webtrack see map_player.loadTrack().
 */
function webtrack_to_geodata(webtrack) {
    geodata = map.createGeodata();
    geodata.addGroup('tracks');

    var trk = webtrack.getTrack()[0].points;
    var coords = [];
    for(var i = 0; i < trk.length; i++) {
        point = [
            trk[i][0], // longitude
            trk[i][1], // latitude
            trk[i][3] // elevation
        ];
        coords.push(point);
        geodata.addPoint(point, 'fix', {}, '', "EPSG:3857");
    }
    geodata.addLineString(coords, 'fix', {}, 'some-path', "EPSG:3857");

    geodata.addGroup('waypoints');
    var wpt = webtrack.getWaypoints();
    for(var i = 0; i < wpt.length; i++) {
        switch(wpt[i].sym) {
            case "Campground":
            case "Fishing Hot Spot Facility":
                // https://vts-geospatial.org/tutorials/geojson-part2.html?highlight=addpointarray#extending-existing-data
                geodata.addPoint([
                    wpt[i].lon,
                    wpt[i].lat,
                    wpt[i].ele
                ], 'fix', {title: wpt[i].name}, 'way-points', "EPSG:3857");
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
    lineGeometry = geodata.extractGeometry('some-path');
    
    //center map postion to track gemetery
    centerPositonToGeometry(lineGeometry);
  
    //style used for displaying geodata
    //find out more about styles: https://vts-geospatial.org/tutorials/geojson.html
    var style = {
        'constants': {
            '@icon-marker': ['icons', 6, 8, 18, 18]
        },
    
        'bitmaps': {
            'icons': '/static/images/placemark_circle.png'
        },

        "layers" : {
            "track-line" : {
                "filter" : ["==", "#type", "line"],
                "line": true,
                "line-width" : 6,
                "line-color": [255,0,0,255],
                "zbuffer-offset" : [-5,0,0],
                "z-index" : -1
            },

            "track-shadow" : {
                "filter" : ["==", "#type", "line"],
                "line": true,
                "line-width" : 20,
                "line-color": [255,255,255,60],
                "zbuffer-offset" : [-5,0,0],
                "hover-event" : true,
                "advanced-hit" : true
            },

            "way-points" : {
                "filter" : ["all", ["==", "#type", "point"], ["==", "#group", "waypoints"]],
                "icon": true,
                "icon-source": "@icon-marker",
                "icon-color": [255,255,0,255], // yellow
                "icon-scale": 2,
                "icon-origin": "center-center",
                "zbuffer-offset" : [-6,0,0],
                "label": true,
                "label-size": 18,
                "label-source": "$title",
                "label-offset": [0,-20],
            },

        }
    };

    //make free layer
    var freeLayer = geodata.makeFreeLayer(style);

    //add free layer to the map
    map.addFreeLayer('gpxgeodata', freeLayer);

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
    var i, li, midPoint = [0,0,0], line, vec3 = vts.vec3;

    //find center of geometry
    for (i = 0, li = geometry.getElements() + 1; i < li; i++) {
        if (i == (li - 1)) { //last line point
            line = geometry.getElement(i-1);
            coords = line[1];
        } else {
            line = geometry.getElement(i);
            coords = line[0];
        }

        midPoint[0] += coords[0];
        midPoint[1] += coords[1];
        midPoint[2] += coords[2];
    };


    midPoint[0] /= li;
    midPoint[1] /= li;
    midPoint[2] /= li;

    // construct line which goes through the center of geometry
    // and mesure most distant point from this line

    var cameraPosition = midPoint;
    var cameraVector = [-cameraPosition[0], -cameraPosition[1], -cameraPosition[2]];
    vec3.normalize(cameraVector);

    var viewExtent = 500;

    for (i = 0, li = geometry.getElements() + 1; i < li; i++) {
        if (i == (li - 1)) { //last line point
            line = geometry.getElement(i - 1);
            coords = line[1];
        } else {
            line = geometry.getElement(i);
            coords = line[0];
        }

        //get line point distance
        var ab = cameraVector;
        var av = [coords[0] - cameraPosition[0], coords[1] - cameraPosition[1], coords[2] - cameraPosition[2]];

        var b = [cameraPosition[0] + cameraVector[0], cameraPosition[1] + cameraVector[1], cameraPosition[2] + cameraVector[2]];
        var bv = [coords[0] - b[0], coords[1] - b[1], coords[2] - b[2]];

        var af = [0,0,0];
        vec3.cross(ab, av, af);

        var d = (vec3.length(bv) / vec3.length(ab)) * 2;

        if (d > viewExtent) {
            viewExtent = d;
        }
    }

    //limit view extent according to planet radius
    if (viewExtent > navigationSrs.a*1.4) {
        viewExtent = navigationSrs.a*1.4;
    }

    //convert coods from physical to nav
    var navCoords = vts.proj4(physicalSrs.srsDef, navigationSrs.srsDef, midPoint);
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
};

/**
 * Event handler.
 */
function onFeatureHover(event) {
    lineSegment = event.element;

    //if there is a path, and the current segment is different from the last one, and not out of range
    if (lineGeometry && (lastLineSegment != lineSegment) && lineSegment <= lineGeometry.getElements()) { 
        //get distance of cursor on the line segment
        var res = lineGeometry.getRelationToCanvasPoint(lineSegment, usedMouseCoords[0], usedMouseCoords[1]);

        //get path length to line segment and length of the segment itself
        var lineSegmentInfo = lineGeometry.getPathLengthToElement(lineSegment);

        //compute path distance to point where cursor is hovering over the track
        pathDistance = lineSegmentInfo.lengthToElement + (lineSegmentInfo.elementLengh * vts.math.clamp(res.distance, 0, 1)); 

        //get point coodinates
        linePoint = lineGeometry.getPathPoint(pathDistance);

        //force redraw map (we have to redraw track point)
        map.redraw();

        //remember the current segment ID to skip the next event if it is the same ID
        lastLineSegment = lineSegment;
    }
}

/**
 * Event handler.
 */
function onCustomRender() {
    if (demoTexture && pathDistance && lineGeometry && linePoint) { //check whether texture is loaded

        //get canvas postion of the track point
        var p = map.convertCoordsFromPhysToCanvas(linePoint);

        //display distance pointer in the track point coordiantes
        var rect = distancePointer.getRect();
        distancePointer.setStyle("display", "block");
        distancePointer.setStyle("left", (p[0]-(rect.width*0.5)) + "px");
        distancePointer.setStyle("top", (p[1]-50) + "px");
        distancePointer.setHtml((pathDistance*0.001).toFixed(1) + " km");

        //draw point image at the last line point
        renderer.drawImage({
            rect : [p[0]-12*1.5, p[1]-12*1.5, 24*1.5, 24*1.5],
            texture : demoTexture,
            color : [255,0,0,255],
            depth : p[2],
            depthTest : false,
            blend : true
            });
    }
}

/**
 * Change the active bound layer on the surface.
 * It could be a composition of layers if separated by commas.
 * 
 * Based on the 'VTS Browser API Examples'
 * https://github.com/melowntech/vts-browser-js/wiki/Examples
 * Switching bound layers:
 * https://jsfiddle.net/jdhakmnt/
 */
function onSwitchView(newBoundLayer) {
    if (map) {
        var existingFreeLayers = map.getView().freeLayers;
        map.setView({
            surfaces: {
                'melown-viewfinder-world': newBoundLayer.split(",").map(s => s.trim())
            },
            freeLayers: existingFreeLayers
        }); 
    }
}
