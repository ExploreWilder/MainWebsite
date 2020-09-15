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

/**
 * This awesome interactive 3D map viewer displaying a track and the elevation profile
 * is mostly based on the VTS Browser JS demo:
 * https://vts-geospatial.org/tutorials/gpx-viewer.html
 * 
 * The differences with the original demo are:
 * 
 * * Removed the GPX drop capability because the track is automatically loaded,
 * * Rewrote the GPX loading function to handle my custom format,
 * * Removed the slow geodata.processHeights() because my custom format already includes the elevation,
 * * Removed the search box and the 2D/3D button,
 * * Managed to fit the tooltip inside the canvas and fixed an onresize bug,
 * * Changed the interface style and nested the map in my layout,
 * * Optimized onFeatureHover() to skip useless heavy computation,
 * * Changed centerPositonToGeometry() in a way to move the track above the elevation profile,
 * * Fixed some NaN error on tooltips.
 *
 */

var browser, renderer, map;
var geodata, lineGeometry = null;
var demoTexture = null;
var usedMouseCoords = [0,0];
var linePoint, lineSegment = 0, lastLineSegment = -1;
var distancePointer, heightPointer, heightPointer2;
var trackHeights = [], trackLengths = [];
var trackMinHeight, trackMaxHeight;
var canvas, canvasCtx;
var pathLength = 0, pathDistance = 0;

/**
 * Setup the entire interface.
 */
(function startMapPlayerInterface() {
    var url = new RegExp("/([^/]*)/([^/]*)/([^/]*)/([^/]*)$", "g").exec(window.location.href);

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

    //move map controls little bit higher
    browser.ui.getControl('credits').getElement('vts-credits').setStyle('bottom', '134px');
    browser.ui.getControl('zoom').getElement('vts-zoom-plus').setStyle('bottom', '140px');
    browser.ui.getControl('zoom').getElement('vts-zoom-minus').setStyle('bottom', '140px');
    browser.ui.getControl('compass').getElement('vts-compass').setStyle('bottom', '170px');

    // create ui control with info pointers
    var infoPointers = browser.ui.addControl('info-pointers',
        '<div id="distance-div" class="distance-div tooltip-arrow"></div>' +
        '<div id="height-div" class="distance-div"></div>' +
        '<div id="height-div2" class="pointer-div2">' +
        '</div>');

    distancePointer = infoPointers.getElement('distance-div');
    heightPointer = infoPointers.getElement('height-div'); // tooltip
    heightPointer2 = infoPointers.getElement('height-div2'); // line

    // create panel with path profile
    var profilePanel = browser.ui.addControl('profile-panel',
        '<div id="profile-div" class="profile-div">' +
            '<div id="profile-canvas-holder" class="profile-canvas-holder">' +
                '<canvas id="profile-canvas" class="profile-canvas">' +
                '</canvas>' +
            '</div>' + 
        '</div>');

    renderer = browser.renderer;

    //add mouse events to map element
    var mapElement = browser.ui.getMapElement();
    mapElement.on('mousemove', onMouseMove);
    mapElement.on('mouseleave', onMouseLeave);
    mapElement.on('resize', onResize, window);

    //add mouse events to canvas element
    canvas = profilePanel.getElement('profile-canvas');
    canvas.on('mousemove', onCanvasHover);
    canvasCtx = canvas.getElement().getContext("2d");
    
    //callback once is map config loaded
    browser.on('map-loaded', onMapLoaded);

    //callback when path hovered
    browser.on('geo-feature-hover', onFeatureHover);

    loadTexture();
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
    oReq.open("GET", "/map/profile/" + book_id + "/" + book_url + "/" + gpx_name, true);
    // https://developer.mozilla.org/en-US/docs/Web/API/XMLHttpRequest/Sending_and_Receiving_Binary_Data
    oReq.responseType = "arraybuffer";

    oReq.onload = function(oEvent) {
        if(oReq.status == 500) { // exception raised in map.py:profile_file()
            var response_str = new TextDecoder("utf-8").decode(new Uint8Array(oReq.response));
            window.alert("Failed to fetch profile data: " + response_str);
            return;
        }
        var arrayBuffer = oReq.response;
        var data = new Uint8Array(arrayBuffer);
        data = LZString.decompressFromUint8Array(data);
        data = JSON.parse(data);
        profile_to_geodata(data);
    };
    oReq.send();
}

/**
 * Read the XHR `data` and save the features into `source`.
 * @param {Array} data XHR data, see map_player.loadTrack().
 */
function profile_to_geodata(data) {
    geodata = map.createGeodata();
    geodata.addGroup('tracks');

    var trk = data["profile"];
    var coords = [];
    for(var i = 0; i < trk.length; i++) {
        point = [
            trk[i][2] - 485 + i * 30, // longitude
            trk[i][3] - 1567, // latitude
            parseFloat(trk[i][0]) // elevation
        ];
        coords.push(point);
        geodata.addPoint(point, 'fix', {}, '', "EPSG:3857");
    }
    geodata.addLineString(coords, 'fix', {}, 'some-path', "EPSG:3857");
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

    //draw track profile
    drawPathProfile(lineGeometry);
  
    //style used for displaying geodata
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
                "point": true,
                "point-radius" : 20,
                "point-color": [0,255,255,255],              
                "zbuffer-offset" : [-5,0,0]
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

    //move the track above the profile canvas
    var offsetBottom = parseInt(browser.ui.getControl('zoom').getElement('vts-zoom-plus').getStyle('bottom')); // px
    var mapHeight = renderer.getCanvasSize()[1];
    midPoint[0] += viewExtent * offsetBottom / mapHeight; // should be 'viewExtentY' instead

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
 * Set heigth profile pointer accoring to current track position
 */
function setProfilePointer(p) {
    var rect = canvas.getRect();
    var x = (pathDistance / pathLength) * rect.width;

    var rect2 = heightPointer.getRect();

    if(typeof(p) === 'undefined' && typeof(last_p) !== 'undefined') {
        p = last_p;
    }
    else {
        p = map.convertCoordsFromPhysToPublic(p);
        last_p = p;
    }

    //keep the tooltip inside the canvas
    var minLeft = rect.left, maxLeft = rect.width + rect.left - rect2.width;
    var tooltipLeft = rect.left + x - rect2.width * 0.5;
    
    if(tooltipLeft < minLeft) {
        tooltipLeft = minLeft;
    }
    else if(tooltipLeft > maxLeft) {
        tooltipLeft = maxLeft;
    }

    heightPointer.setStyle('display', 'block');
    heightPointer.setStyle('left', tooltipLeft + 'px');
    heightPointer.setStyle('top', (rect.top) + 'px');
    heightPointer.setHtml((p[2]).toFixed(0) + " m");

    heightPointer2.setStyle('display', 'block');
    heightPointer2.setStyle('left', (rect.left + x - 1) + 'px');
    heightPointer2.setStyle('top', (rect.top) + 'px');
}

/**
 * Redraw track profile when browser window is resized
 */
function onResize() {
    refereshCanvasDimensions();
    drawPathProfile(lineGeometry);
    if(heightPointer.getStyle('display') == 'block') {
        setProfilePointer();
    }
}

/**
 * Sets canvas size accoding to HTML element size
 */
function refereshCanvasDimensions() {
    var rect = canvas.getRect();
    var canvasElement = canvas.getElement();
    if (canvasElement.width != rect.width) { 
        canvasElement.width = rect.width;
    }
    if (canvasElement.height != rect.height) {
        canvasElement.height = rect.height;
    }
    return [rect.width, rect.height];
}

/**
 * Process track geometry and display track profile
 */
function drawPathProfile(geometry) {
    if (!geometry) {
        return;
    }

    var totalElements = geometry.getElements();

    if (!totalElements) {
        return;
    }

    pathLength = geometry.getPathLength();

    trackHeights = new Array(totalElements);
    trackLengths = new Array(totalElements);
    trackMinHeight = Number.POSITIVE_INFINITY;
    trackMaxHeight = Number.NEGATIVE_INFINITY;

    var totalLength = 0;

    //get track point heights and length between track points
    for (var i = 0, li = totalElements; i < li; i++) {
        var l = geometry.getElement(i);
        var p = map.convertCoordsFromPhysToPublic(l[0]);
        trackHeights[i] = p[2];

        totalLength += vts.vec3.length([l[1][0] - l[0][0], l[1][1] - l[0][1], l[1][2] - l[0][2]]);
        trackLengths[i] = totalLength;

        if (p[2] > trackMaxHeight) {
            trackMaxHeight = p[2];
        }

        if (p[2] < trackMinHeight) {
            trackMinHeight = p[2];
        }
    }

    //draw track profile
    var dim = refereshCanvasDimensions();
    var lx = dim[0], ly = dim[1];

    canvasCtx.clearRect(0,0,lx,ly);
    canvasCtx.beginPath();
    canvasCtx.moveTo(-1,ly-1);

    if (trackMaxHeight == trackMinHeight) {
        canvasCtx.lineTo(lx,ly);
    } else {

        canvasCtx.lineTo(-1, (ly - 2) - ((trackHeights[0] - trackMinHeight) / (trackMaxHeight - trackMinHeight)) * (ly-30) );

        for (var i = 0, li = trackHeights.length; i < li; i++) {
            canvasCtx.lineTo((trackLengths[i]/pathLength)*lx, (ly - 2) - ((trackHeights[i] - trackMinHeight) / (trackMaxHeight - trackMinHeight)) * (ly-30) );
        }
    }

    canvasCtx.lineTo(lx,ly-1);
    canvasCtx.lineTo(0,ly-1);

    // Create gradient
    var grd = canvasCtx.createLinearGradient(0,0,0,ly);
    grd.addColorStop(0,"rgba(252,186,136,0.3)");
    grd.addColorStop(1,"rgba(94,45,18,0.3)");

    // Fill profile with gradient
    canvasCtx.fillStyle = grd;
    canvasCtx.fill();

    //draw profile outline
    canvasCtx.strokeStyle = "rgba(50,50,50,0.7)";
    canvasCtx.stroke();
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

        //refresh pointer in height profile
        setProfilePointer(linePoint);

        //force redraw map (we have to redraw track point)
        map.redraw();

        //remember the current segment ID to skip the next event if it is the same ID
        lastLineSegment = lineSegment;
    }
}

/**
 * Event handler.
 */
function onCanvasHover(event) {
    if (map && lineGeometry) {
        var coords = event.getMouseCoords();
        usedMouseCoords = coords;

        //compute new path distance from cursor position in canvas
        pathDistance = (coords[0] / canvas.getElement().width) * pathLength; // m

        //get point coodinates
        linePoint = lineGeometry.getPathPoint(pathDistance);

        //refresh pointer in height profile
        setProfilePointer(linePoint);

        //force redraw map (we have to redraw track point)
        map.redraw();
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
