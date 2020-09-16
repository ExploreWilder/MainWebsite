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
 * The interface loads once the JSON-formated story has been successfully fetched.
 */
class StorytellingMap {
    /** The book ID found in the database. */
    #book_id;

    /** The book directory found in the database. */
    #book_dir;

    /** The external book path excluding the book file. Example: "/book/1/awesome_story/" */
    #book_path;

    /** Filename of the book. Example: "config.json" */
    #book_filename;

    /** True to make this.map interactive and display the location helper to create chapters. */
    #debug_mode;

    /** Used to add style capabilites (opacity) to Mapbox elements. */
    #layer_types = {
        'fill': ['fill-opacity'],
        'line': ['line-opacity'],
        'circle': ['circle-opacity', 'circle-stroke-opacity'],
        'symbol': ['icon-opacity', 'text-opacity'],
        'raster': ['raster-opacity'],
        'fill-extrusion': ['fill-extrusion-opacity']
    }

    /** The non-interactive MapboxGL map object. */
    map;

    /** Marker in this.map displayed if this.config.showMarkers is true. */
    map_marker;

    /** Location on map load. */
    start_location;

    /** The small interactive map on the corner of the window used display the broad area. */
    contextual_map;

    /** Points to the center of the contextual map. */
    contextual_marker;

    /** The actual JSON story. */
    config;

    /** The DOM story. */
    story;

    /** The footer of the story containing the "Follow Me", "Support Me", and "Copyright". */
    footer;

    /**
     * Fetch the JSON-formated story and load the entire interface.
     */
    constructor(book_id, book_dir, book_filename, debug_mode) {
        this.#book_id = book_id;
        this.#book_dir = book_dir;
        this.#book_path = `/books/${book_id}/${book_dir}/`;
        this.#book_filename = book_filename;
        this.#debug_mode = debug_mode;
        this.story = document.getElementById('storytelling-map-story');

        $("#loading-progress-info").text("Downloading story...");

        $.getJSON(this.#book_path + this.#book_filename, (data) => {
            this.config = data;
            this.kickoff();
        });

        $("#map-on-top").change(function() {
            $("#storytelling-map-map").css("z-index", (this.checked) ? 2 : -5); // above or below story
        });
    }

    /**
     * Create a card element.
     * @param record_card {Object} - JSON dictionary.
     * @return {Object} DOM element to be inserted in the chapter.
     */
    create_card(record_card) {
        var card = document.createElement('div');
        card.className += "card-progress";
        card.innerText = record_card.curr + "/" + record_card.last;
        return card;
    }

    /**
     * Create a title element.
     * @param record_title {Object} - JSON dictionary.
     * @return {Object} DOM element to be inserted in the chapter.
     */
    create_title(record_title) {
        var title = document.createElement('h1');
        title.innerText = record_title;
        return title;
    }

    /**
     * Create an image element.
     * @param record_image {Object} - JSON dictionary.
     * @return {Object} DOM element to be inserted in the chapter.
     */
    create_image(record_image) {
        var image = new Image();

        image.setAttribute("data-lazysrc", this.#book_path + record_image);
        image.addEventListener("contextmenu", function(e){
            e.preventDefault();
        }, false);

        var blockImage = document.createElement('div');
        blockImage.className += "image-inside";
        blockImage.appendChild(image);

        return blockImage;
    }

    /**
     * Create a video element.
     * @param record_video {Object} - JSON dictionary.
     * @return {Object} DOM element to be inserted in the chapter.
     */
    create_video(record_video) {
        var video = document.createElement('video');
        video.setAttribute('width', '100%');
        video.setAttribute('controls', '');
        video.setAttribute('preload', 'none');

        var source = document.createElement('source');
        source.src = this.#book_path + record_video;
        source.setAttribute('type', 'video/mp4');

        video.appendChild(source);
        video.appendChild(document.createTextNode("Your browser does not support the video tag."));
        return video;
    }

    /**
     * Create track info.
     * @param record_video {Object} - JSON dictionary.
     * @return {Object} DOM element to be inserted in the chapter.
     */
    create_track_info(record_track_info) {
        var trackInfoTitle = document.createElement('h4');
        trackInfoTitle.innerText = "Track info:";
        
        var trackData = document.createElement('ul');

        if(record_track_info.period) {
            var trackPeriod = document.createElement('li');
            trackPeriod.innerHTML = "Period: " + record_track_info.period + " (<abbr title='Meteorological season'>" + record_track_info.season + "</abbr>)";
            trackData.appendChild(trackPeriod);
        }

        if(record_track_info.duration) {
            var trackDuration = document.createElement('li');
            trackDuration.innerHTML = "Duration: <abbr title='Excluding transport'>" + record_track_info.duration + "</abbr>";
            trackData.appendChild(trackDuration);
        }
        
        if(record_track_info.distance) {
            var trackLength = document.createElement('li');
            trackLength.innerText = "Distance: " + record_track_info.distance + " km";
            trackData.appendChild(trackLength);
        }
        
        if(record_track_info.totalElevation) {
            var trackElevation = document.createElement('li');
            trackElevation.innerHTML = "Total Elevation: <abbr title='Gain+loss, filtered radar data'>"
                + number_with_commas(record_track_info.totalElevation)
                + " m</abbr>";
            trackData.appendChild(trackElevation);
        }
        
        var trackDetails = document.createElement('div');
        trackDetails.className += 'more-info';
        var buttonInfoMap = document.createElement('a');
        buttonInfoMap.setAttribute('href', this.track_path(record_track_info.details));
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
        return groupTrackInfo;
    }

    /**
     * Create a description.
     * @param record_video {Object} - JSON dictionary.
     * @return {Object} DOM element to be inserted in the chapter.
     */
    create_description(record_description) {
        var story = document.createElement('div');
        story.innerHTML = record_description;
        return story;
    }

    /**
     * Create a button pointing to the map viewer.
     * @param record_video {Object} - JSON dictionary.
     * @return {Object} DOM element to be inserted in the chapter.
     */
    create_detailed_track(record_detailed_track) {
        var buttonTopoMap = document.createElement('a');
        buttonTopoMap.className += 'btn btn-success';
        buttonTopoMap.setAttribute('href', this.track_path(record_detailed_track));
        buttonTopoMap.setAttribute('target', '_blank');
        buttonTopoMap.setAttribute('role', 'button');
        buttonTopoMap.setAttribute('title', 'Open map with track and topographic information');
        buttonTopoMap.innerHTML = '<i class="fas fa-map-marked-alt"></i> Detailed track';
        var blockButton = document.createElement('p');
        blockButton.appendChild(buttonTopoMap);
        blockButton.className += 'text-center';
        return blockButton;
    }

    /**
     * Create a div block and populate with the chapter `record`.
     * 
     * @param record {Object} - The JSON chapter.
     * @param idx {Number} - The chapter identifier (first chapter is 0).
     * @return {Object} DOM object of the created chapter to be appended to the story.
     */
    create_chapter(record, idx) {
        var container = document.createElement('div');
        var chapter = document.createElement('div');
        
        if (record.card) {
            chapter.appendChild(this.create_card(record.card));
        }
        
        if (record.title) {
            chapter.appendChild(this.create_title(record.title));
        }
        
        if (record.image) {
            chapter.appendChild(this.create_image(record.image));
        }
        
        if (record.video) {
            chapter.appendChild(this.create_video(record.video));
        }
        
        if (record.trackInfo) {
            chapter.appendChild(this.create_track_info(record.trackInfo));
        }
        
        if (record.description) {
            chapter.appendChild(this.create_description(record.description));
        }
        
        if (record.detailedTrack) {
            chapter.appendChild(this.create_detailed_track(record.detailedTrack));
        }

        container.setAttribute('id', record.id);
        container.classList.add('step');
        if (idx === 0) {
            container.classList.add('active');
        }

        chapter.classList.add(this.config.theme);
        container.appendChild(chapter);
        return container;
    }

    /**
     * Read the JSON story and populate the DOM.
     */
    story_processor() {
        const alignments = {
            'left': 'lefty',
            'center': 'centered',
            'right': 'righty'
        }

        var features = document.createElement('div');
        features.classList.add(alignments[this.config.alignment]);
        features.setAttribute('id', 'storytelling-map-features');

        var header = document.getElementById('storytelling-map-header');

        if (header.innerText.length > 0) {
            header.classList.add(this.config.theme); // overwrite static CSS
        }

        this.config.chapters.forEach((record, idx) => {
            features.appendChild(this.create_chapter(record, idx));
        });

        this.story.appendChild(features);

        this.footer = document.getElementById('storytelling-map-footer');

        if (this.footer.innerText.length > 0) {
            this.footer.classList.add(this.config.theme);
            this.story.appendChild(this.footer);
        }
    }

    /**
     * Initialize the map.
     */
    init_map() {
        mapboxgl.accessToken = this.config.accessToken;

        const scale = new mapboxgl.ScaleControl({
            maxWidth: 300,
            unit: 'metric'
        });

        const compass = new mapboxgl.NavigationControl({
            showZoom: false
        });
        
        this.start_location = this.computeZoom(this.config.chapters[0].location);

        this.map = new mapboxgl.Map({
            container: 'storytelling-map-map',
            style: this.config.style,
            center: this.start_location.center,
            zoom: this.start_location.zoom,
            bearing: this.start_location.bearing,
            pitch: this.start_location.pitch,
            scrollZoom: this.#debug_mode,
            dragPan: this.#debug_mode,
            dragRotate: this.#debug_mode,
            attributionControl: false
        });

        this.map.addControl(scale);
        this.map.addControl(compass, 'bottom-left');

        if (this.config.showMarkers) {
            this.map_marker = new mapboxgl.Marker();
            this.map_marker.setLngLat(this.start_location.center).addTo(this.map);
        }
    }

    /**
     * Initialize the entire interface while updating the loading message.
     */
    kickoff() {
        $("#loading-progress-info").text("Processing story...");
        this.story_processor();
        
        $("#loading-progress-info").text("Initialising interface...");
        this.init_map();
        this.init_contextual_map();

        $("#loading-progress-info").text("Loading map...");
        this.map.on("load", () => {
                this.on_map_load();
        })
        .on("moveend", () => {
            if(this.#debug_mode) {
                this.update_location_helper(this.map);
            }
        });

        // setup resize event
        window.addEventListener('resize', () => {
            scroller.resize();
        });
    }

    /**
     * Setup Scrollama and update the window style, load all images contained in the story.
     */
    on_map_load() {
        var scroller = scrollama();

        this.config.geojsons.forEach((record) => {
            this.map.addSource(record.layer.source, {
                'type': 'geojson',
                'data': this.#book_path + record.data
            });
            this.map.addLayer(record.layer);
            var paintProps = this.#layer_types[record.layer.type];
            paintProps.forEach((prop) => {
                this.map.setPaintProperty(record.layer.id, prop, record.opacity);
            });
        });

        // setup the instance, pass callback functions
        scroller
        .setup({
            step: '.step',
            offset: 0.5,
            progress: true
        })
        .onStepEnter((response) => {
            this.on_step_enter(response);
        })
        .onStepExit((response) => {
            this.on_step_exit(response);
        });

        console.log("Scrollytelling map ready");
        document.getElementById('wait-before-visible').style.display = "none";
        document.getElementById('storytelling-map-map').style.opacity = 1;
        document.getElementsByClassName('mapboxgl-canvas')[0].style.cursor = "default";
        document.getElementById('storytelling-map-features').style.display = "block";
        $("body").removeClass("loading-storytelling-map");
        this.footer.style.display = "block";
        this.load_images();
    }

    /**
     * When the user enter a chapter.
     */
    on_step_enter(response) {
        var chapter = this.config.chapters.find(chap => chap.id === response.element.id);
        this.map.flyTo(this.computeZoom(chapter.location));
        if(chapter.showContext) {
            var was_visible = $("#storytelling-map-context").css("display") != "none";
            $("#storytelling-map-context").show(0, () => {
                if(Array.isArray(chapter.showContext)) {
                    if(was_visible) {
                        this.contextual_map.flyTo({
                            center: chapter.showContext,
                            zoom: 8
                        });
                    }
                    else {
                        this.contextual_map.jumpTo({
                            center: chapter.showContext,
                            zoom: 8
                        });
                    }
                    this.contextual_map.resize();
                    this.contextual_marker.setLngLat(chapter.showContext);
                }
            });
        }
        else {
            $("#storytelling-map-context").hide(0);
        }
        if (this.config.showMarkers) {
            this.map_marker.setLngLat(chapter.location.center);
        }
        if (chapter.onChapterEnter.length > 0) {
            chapter.onChapterEnter.forEach((el) => {
                this.setLayerOpacity(el);
            });
        }
    }

    /**
     * When the user exit a chapter.
     */
    on_step_exit(response) {
        var chapter = this.config.chapters.find(chap => chap.id === response.element.id);
        if (chapter.onChapterExit.length > 0) {
            chapter.onChapterExit.forEach((el) => {
                this.setLayerOpacity(el);
            });
        }
    }

    /**
     * Change the zoom to fit the same map boundary whatever the window width.
     */
    computeZoom(location) {
        var actual_location = Object.assign({}, location); // clone, don't change the config
        const a = (8.81-8)/(1920-948), b = 8.81-a*1920;
        var x = document.getElementById('storytelling-map-map').offsetWidth, z = a*x+b;
        actual_location.zoom *= z/8.81;
        return actual_location;
    }

    /**
     * Change the Mapbox layer (of the map) as specified in the 'opacity' property in this.config.
     */
    setLayerOpacity(layer) {
        var layerType = this.map.getLayer(layer.layer).type;
        var paintProps = this.#layer_types[layerType];
        paintProps.forEach((prop) => {
            this.map.setPaintProperty(layer.layer, prop, layer.opacity);
        });
    }

    /**
     * Update the content of #storytelling-location-helper-info based on the current
     * map position and orientation. It is intended to create the JSON story.
     * The update is on map move.
     */
    update_location_helper() {
        const settings = `"center": [${this.map.getCenter().lng.toFixed(5)}, ${this.map.getCenter().lat.toFixed(5)}],
            "zoom": ${this.map.getZoom().toFixed(2)},
            "pitch": ${this.map.getPitch().toFixed(2)},
            "bearing": ${this.map.getBearing().toFixed(2)}`;
        document.getElementById("storytelling-location-helper-info").innerText = settings;
    }

    /**
     * The external track path.
     * Example: "/map/viewer/1/awesome_story/``track_name``/fr"
     */
    track_path(track_name) {
        return `/map/viewer/${this.#book_id}/${this.#book_dir}/${track_name}/fr`;
    }

    /**
     * Since the images are JS-loaded, using the src attribute would trigger
     * a download. However, it really slows down the map initialisation.
     * Therefore, the data-lazysrc attribute contains the src and this
     * procedure actually set the src of img and source tags.
     */
    load_images() {
        $("img[data-lazysrc], source[data-lazysrc]").each(function() {
            $(this).attr("src", $(this).attr("data-lazysrc"));
        });
    }

    /**
     * Initialise the mini contextual map displayed on the top left corner.
     * That map is movable/scrollable/zoomable. The + and - buttons are displayed
     * but not the compass since the map cannot rotate.
     */
    init_contextual_map() {
        this.contextual_map = new mapboxgl.Map({
            container: 'storytelling-map-context',
            style: 'mapbox://styles/mapbox/streets-v11',
            center: this.start_location.center,
            zoom: this.start_location.zoom,
            attributionControl: false
        });

        this.contextual_map.addControl(new mapboxgl.NavigationControl({
            showCompass: false
        }));

        this.contextual_marker = new mapboxgl.Marker()
        .setLngLat(this.start_location.center)
        .addTo(this.contextual_map);
    }
}

$(function() {
    if($("#storytelling-map").length) {
        storytelling_map = new StorytellingMap(parseInt(BOOK_ID), encodeURIComponent(BOOK_DIR), BOOK_FILENAME, DEBUG_MODE);
    }
});
