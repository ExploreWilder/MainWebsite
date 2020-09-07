/*!
 *
 * BSD 3-Clause License
 *
 * Copyright (c) 2019, Mapbox
 * Copyright (c) 2019-2020, Clement
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are met:
 *
 * 1. Redistributions of source code must retain the above copyright notice, this
 *    list of conditions and the following disclaimer.
 *
 * 2. Redistributions in binary form must reproduce the above copyright notice,
 *    this list of conditions and the following disclaimer in the documentation
 *    and/or other materials provided with the distribution.
 *
 * 3. Neither the name of the copyright holder nor the names of its
 *    contributors may be used to endorse or promote products derived from
 *    this software without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
 * AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
 * DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
 * FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
 * DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
 * SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
 * CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
 * OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
 * OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

/**
 * This app is based on the following mapbox example:
 * https://github.com/mapbox/storytelling
 * I used mapbox Studio-generated layers including hillshading
 * made available by the USGS 3D Elevation Program.
 * It is integrated in the website (core design and scripts required.)
 * A message error is displayed if Mapbox GL is not supported.
 * The interface loads once the JSON-formated story has been successfully fetched.
 */

/**
 * The book ID found in the database.
 */
BOOK_ID = parseInt(BOOK_ID);

/**
 * The book directory found in the database.
 */
BOOK_DIR = encodeURIComponent(BOOK_DIR);

/**
 * The external book path excluding the book file.
 * Example: "/book/1/awesome_story/"
 */
var book_path = "/books/" + BOOK_ID + "/" + BOOK_DIR + "/";

/**
 * Declared but always set'ed before get'ed.
 */
var contextual_map = null;

/**
 * Declared but always set'ed before get'ed.
 */
var contextual_marker = null;

/**
 * Update the content of #storytelling-location-helper-info based on the current
 * map position and orientation. It is intended to create the JSON story.
 * The update is on map move.
 * @param map The main MapboxGL map object.
 */
var update_location_helper = function(map) {
    const settings = `"center": [${map.getCenter().lng.toFixed(5)}, ${map.getCenter().lat.toFixed(5)}],
        "zoom": ${map.getZoom().toFixed(2)},
        "pitch": ${map.getPitch().toFixed(2)},
        "bearing": ${map.getBearing().toFixed(2)}`;
    document.getElementById("storytelling-location-helper-info").innerText = settings;
};

/**
 * The external track path.
 * Example: "/map/viewer/1/awesome_story/``track_name``/fr"
 */
var track_path = function(track_name) {
    return "/map/viewer/" + BOOK_ID + "/" + BOOK_DIR + "/" + track_name + "/fr";
};

/**
 * Since the images are JS-loaded, using the src attribute would trigger
 * a download. However, it really slows down the map initialisation.
 * Therefore, the data-lazysrc attribute contains the src and this
 * procedure actually set the src of img and source tags.
 */
var load_images = function() {
    $("img[data-lazysrc], source[data-lazysrc]").each(function() {
        $(this).attr("src", $(this).attr("data-lazysrc"));
    });
};

/**
 * Initialise the mini contextual map displayed on the top left corner.
 * That map is movable/scrollable/zoomable. The + and - buttons are displayed
 * but not the compass since the map cannot rotate.
 * @param start_location Location on map load.
 */
var init_storytelling_contextual_map = function(start_location) {
    contextual_map = new mapboxgl.Map({
        container: 'storytelling-map-context',
        style: 'mapbox://styles/mapbox/streets-v11',
        center: start_location.center,
        zoom: start_location.zoom,
        attributionControl: false
    });
    contextual_map.addControl(new mapboxgl.NavigationControl({
        showCompass: false
    }));
    contextual_marker = new mapboxgl.Marker()
    .setLngLat(start_location.center)
    .addTo(contextual_map);
};

/**
 * Fetch the JSON-formated story and load the entire interface.
 */
var init_storytelling_map = function() {
    var story = document.getElementById('storytelling-map-story');
    $("#loading-progress-info").text("Downloading story...");
    $.getJSON(book_path + BOOK_FILENAME, function(data) {
        $("#loading-progress-info").text("Processing story...");
        var config = data;
        
        var layerTypes = {
            'fill': ['fill-opacity'],
            'line': ['line-opacity'],
            'circle': ['circle-opacity', 'circle-stroke-opacity'],
            'symbol': ['icon-opacity', 'text-opacity'],
            'raster': ['raster-opacity'],
            'fill-extrusion': ['fill-extrusion-opacity']
        }

        var alignments = {
            'left': 'lefty',
            'center': 'centered',
            'right': 'righty'
        }

        function getLayerPaintType(layer) {
            var layerType = map.getLayer(layer).type;
            return layerTypes[layerType];
        }

        function setLayerOpacity(layer) {
            var paintProps = getLayerPaintType(layer.layer);
            paintProps.forEach(function(prop) {
                map.setPaintProperty(layer.layer, prop, layer.opacity);
            });
        }

        var features = document.createElement('div');
        features.classList.add(alignments[config.alignment]);
        features.setAttribute('id', 'storytelling-map-features');

        var header = document.getElementById('storytelling-map-header');

        if (header.innerText.length > 0) {
            header.classList.add(config.theme); // overwrite static CSS
        }

        config.chapters.forEach((record, idx) => {
            var container = document.createElement('div');
            var chapter = document.createElement('div');
            
            if (record.card) {
                var card = document.createElement('div');
                card.className += "card-progress";
                card.innerText = record.card.curr + "/" + record.card.last;
                chapter.appendChild(card);
            }
            
            if (record.title) {
                var title = document.createElement('h1');
                title.innerText = record.title;
                chapter.appendChild(title);
            }
            
            if (record.image) {
                var image = new Image();
                image.setAttribute("data-lazysrc", book_path + record.image);
                image.addEventListener("contextmenu", function(e){
                    e.preventDefault();
                }, false);
                var blockImage = document.createElement('div');
                blockImage.className += "image-inside";
                blockImage.appendChild(image);
                chapter.appendChild(blockImage);
            }
            
            if (record.video) {
                var video = document.createElement('video');
                video.setAttribute('width', '100%');
                video.setAttribute('controls', '');
                video.setAttribute('preload', 'none'); // https://developers.google.com/web/fundamentals/performance/lazy-loading-guidance/images-and-video/#for_video_that_doesnt_autoplay
                var source = document.createElement('source');
                source.src = book_path + record.video;
                source.setAttribute('type', 'video/mp4');
                video.appendChild(source);
                video.appendChild(document.createTextNode("Your browser does not support the video tag."));
                chapter.appendChild(video);
            }
            
            if (record.trackInfo) {
                var trackInfoTitle = document.createElement('h4');
                trackInfoTitle.innerText = "Track info:";
                
                var trackData = document.createElement('ul');

                if(record.trackInfo.period) {
                    var trackPeriod = document.createElement('li');
                    trackPeriod.innerHTML = "Period: " + record.trackInfo.period + " (<abbr title='Meteorological season'>" + record.trackInfo.season + "</abbr>)";
                    trackData.appendChild(trackPeriod);
                }

                if(record.trackInfo.duration) {
                    var trackDuration = document.createElement('li');
                    trackDuration.innerHTML = "Duration: <abbr title='Excluding transport'>" + record.trackInfo.duration + "</abbr>";
                    trackData.appendChild(trackDuration);
                }
                
                if(record.trackInfo.distance) {
                    var trackLength = document.createElement('li');
                    trackLength.innerText = "Distance: " + record.trackInfo.distance + " km";
                    trackData.appendChild(trackLength);
                }
                
                if(record.trackInfo.totalElevation) {
                    var trackElevation = document.createElement('li');
                    trackElevation.innerHTML = "Total Elevation: <abbr title='Gain+loss, filtered radar data'>"
                        + number_with_commas(record.trackInfo.totalElevation)
                        + " m</abbr>";
                    trackData.appendChild(trackElevation);
                }
                
                var trackDetails = document.createElement('div');
                trackDetails.className += 'more-info';
                var buttonInfoMap = document.createElement('a');
                buttonInfoMap.setAttribute('href', track_path(record.trackInfo.details));
                buttonInfoMap.setAttribute('target', '_blank');
                buttonInfoMap.setAttribute('title', 'Open map with track and topographic information');
                var img_info = document.createElement('i');
                img_info.className += 'fas fa-info-circle';
                buttonInfoMap.appendChild(img_info);
                trackDetails.appendChild(buttonInfoMap);
                
                var groupTrackInfo = document.createElement('div');
                groupTrackInfo.className += 'group-info-track';
                groupTrackInfo.appendChild(trackDetails);
                groupTrackInfo.appendChild(trackInfoTitle);
                groupTrackInfo.appendChild(trackData);
                chapter.appendChild(groupTrackInfo);
            }
            
            if (record.description) {
                var story = document.createElement('div');
                story.innerHTML = record.description;
                chapter.appendChild(story);
            }
            
            if (record.detailedTrack) {
                var buttonTopoMap = document.createElement('a');
                buttonTopoMap.className += 'btn btn-success';
                buttonTopoMap.setAttribute('href', track_path(record.detailedTrack));
                buttonTopoMap.setAttribute('target', '_blank');
                buttonTopoMap.setAttribute('role', 'button');
                buttonTopoMap.setAttribute('title', 'Open map with track and topographic information');
                buttonTopoMap.innerHTML = '<i class="fas fa-map-marked-alt"></i> Detailed track';
                var blockButton = document.createElement('p');
                blockButton.appendChild(buttonTopoMap);
                blockButton.className += 'text-center';
                chapter.appendChild(blockButton);
            }

            container.setAttribute('id', record.id);
            container.classList.add('step');
            if (idx === 0) {
                container.classList.add('active');
            }

            chapter.classList.add(config.theme);
            container.appendChild(chapter);
            features.appendChild(container);
        });

        story.appendChild(features);

        var footer = document.getElementById('storytelling-map-footer');

        if (footer.innerText.length > 0) {
            footer.classList.add(config.theme);
            story.appendChild(footer);
        }
        
        $("#loading-progress-info").text("Initialising interface...");

        mapboxgl.accessToken = config.accessToken;

        var scale = new mapboxgl.ScaleControl({
            maxWidth: 300,
            unit: 'metric'
        });

        var compass = new mapboxgl.NavigationControl({
            showZoom: false
        });
        
        /**
         * Change the zoom to fit the same map boundary whatever the window width.
         */
        var computeZoom = function(location) {
            var actual_location = Object.assign({}, location); // clone, don't change the config
            const a = (8.81-8)/(1920-948), b = 8.81-a*1920;
            var x = document.getElementById('storytelling-map-map').offsetWidth, z = a*x+b;
            actual_location.zoom *= z/8.81;
            return actual_location;
        }
        
        var start_location = computeZoom(config.chapters[0].location);

        var map = new mapboxgl.Map({
            container: 'storytelling-map-map',
            style: config.style,
            center: start_location.center,
            zoom: start_location.zoom,
            bearing: start_location.bearing,
            pitch: start_location.pitch,
            scrollZoom: DEBUG_MODE,
            dragPan: DEBUG_MODE,
            dragRotate: DEBUG_MODE,
            attributionControl: false
        });

        map.addControl(scale);
        map.addControl(compass, 'bottom-left');

        var marker = new mapboxgl.Marker();
        if (config.showMarkers) {
            marker.setLngLat(start_location.center).addTo(map);
        }

        // instantiate the scrollama
        var scroller = scrollama();

        init_storytelling_contextual_map(start_location);

        $("#loading-progress-info").text("Loading map...");
        map.on("load", function() {
                config.geojsons.forEach((record) => {
                    map.addSource(record.layer.source, {
                        'type': 'geojson',
                        'data': book_path + record.data
                    });
                    map.addLayer(record.layer);
                    var paintProps = layerTypes[record.layer.type];
                    paintProps.forEach(function(prop) {
                        map.setPaintProperty(record.layer.id, prop, record.opacity);
                    });
                });

                // setup the instance, pass callback functions
                scroller
                .setup({
                    step: '.step',
                    offset: 0.5,
                    progress: true
                })
                .onStepEnter(response => {
                    var chapter = config.chapters.find(chap => chap.id === response.element.id);
                    map.flyTo(computeZoom(chapter.location));
                    if(chapter.showContext) {
                        var was_visible = $("#storytelling-map-context").css("display") != "none";
                        $("#storytelling-map-context").show(0, function() {
                            if(Array.isArray(chapter.showContext)) {
                                if(was_visible) {
                                    contextual_map.flyTo({
                                        center: chapter.showContext,
                                        zoom: 8
                                    });
                                }
                                else {
                                    contextual_map.jumpTo({
                                        center: chapter.showContext,
                                        zoom: 8
                                    });
                                }
                                contextual_map.resize();
                                contextual_marker.setLngLat(chapter.showContext);
                            }
                        });
                    }
                    else {
                        $("#storytelling-map-context").hide(0);
                    }
                    if (config.showMarkers) {
                        marker.setLngLat(chapter.location.center);
                    }
                    if (chapter.onChapterEnter.length > 0) {
                        chapter.onChapterEnter.forEach(setLayerOpacity);
                    }
                })
                .onStepExit(response => {
                    var chapter = config.chapters.find(chap => chap.id === response.element.id);
                    if (chapter.onChapterExit.length > 0) {
                        chapter.onChapterExit.forEach(setLayerOpacity);
                    }
                });
                console.log("Scrollytelling map ready");
                document.getElementById('wait-before-visible').style.display = "none";
                document.getElementById('storytelling-map-map').style.opacity = 1;
                document.getElementsByClassName('mapboxgl-canvas')[0].style.cursor = "default";
                document.getElementById('storytelling-map-features').style.display = "block";
                $("body").removeClass("loading-storytelling-map");
                footer.style.display = "block";
                load_images();
        })
        .on("moveend", () => {
            if(DEBUG_MODE) {
                update_location_helper(map);
            }
        });

        // setup resize event
        window.addEventListener('resize', scroller.resize);
    });
    $("#map-on-top").change(function() {
        $("#storytelling-map-map").css("z-index", (this.checked) ? 2 : -5); // above or below story
    });
};
