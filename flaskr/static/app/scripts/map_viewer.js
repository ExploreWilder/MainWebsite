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
 * Available resolutions for the IGN tiles.
 * Read the IGN documentation for further information.
 */
const resolutions = [
    156543.03392804103,
    78271.5169640205,
    39135.75848201024,
    19567.879241005125,
    9783.939620502562,
    4891.969810251281,
    2445.9849051256406,
    1222.9924525628203,
    611.4962262814101,
    305.74811314070485,
    152.87405657035254,
    76.43702828517625,
    38.218514142588134,
    19.109257071294063,
    9.554628535647034,
    4.777314267823517,
    2.3886571339117584,
    1.1943285669558792,
    0.5971642834779396,
    0.29858214173896974,
    0.14929107086948493,
    0.07464553543474241
];

/**
 * Matrix IDs.
 * Read the IGN documentation for further information.
 */
const matrix_ids = ["0","1","2","3","4","5","6","7","8","9","10","11","12","13","14","15","16","17","18","19"];

/**
 * Returns a formatted link to the tiles.
 */
function get_tiles_link(layer) {
    return middleware_url["nz"] + layer + "/{a-d}/{z}/{x}/{y}";
}

/**
 * Aerial Imagery tiles with a dynamic opacity. Those tiles are in the foreground.
 */
var raster = {
    "nz": new ol.layer.Tile({
        source: new ol.source.XYZ({
            url: get_tiles_link("set=2")
        }),
        opacity: default_opacity / 100.
    }),
    "fr": new ol.layer.Tile({
        source : new ol.source.WMTS({
            url: middleware_url["fr"],
            layer: "ORTHOIMAGERY.ORTHOPHOTOS",
            matrixSet: "PM",
            format: "image/jpeg",
            style: "normal",
            tileGrid : new ol.tilegrid.WMTS({
                origin: [-20037508,20037508],
                resolutions: resolutions,
                matrixIds: matrix_ids
            })
        }),
        opacity: default_opacity / 100.
    }),
    "no": new ol.layer.Tile({
        source : new ol.source.XYZ({
            url: middleware_url["satellite"]
        }),
        opacity: default_opacity / 100.
    }),
    "ca": new ol.layer.Tile({
        source: new ol.source.XYZ({
            url: middleware_url["satellite"]
        }),
        opacity: default_opacity / 100.
    }),
    "satellite": new ol.layer.Tile({
        source: new ol.source.XYZ({
            url: middleware_url["satellite"]
        }),
        opacity: default_opacity / 100.
    })
};

/**
 * Topo50 tiles. Those tiles are in the background, behind the aerial view.
 */
var raster_topo50 = {
    "nz": new ol.layer.Tile({
        source: new ol.source.XYZ({
            url: get_tiles_link("layer=767")
        })
    }),
    "fr": new ol.layer.Tile({
        source : new ol.source.WMTS({
            url: middleware_url["fr"],
            layer: "GEOGRAPHICALGRIDSYSTEMS.MAPS",
            matrixSet: "PM",
            format: "image/jpeg",
            style: "normal",
            tileGrid : new ol.tilegrid.WMTS({
                origin: [-20037508,20037508],
                resolutions: resolutions,
                matrixIds: matrix_ids
            })
        })
    }),
    "ca": new ol.layer.Tile({
        source : new ol.source.TileWMS({
            url: middleware_url["ca"],
            params: {
                LAYERS: "canvec",
                TRANSPARENT: "false"
            }
        })
    }),
    "no": new ol.layer.Tile({
        source: new ol.source.XYZ({
            url: middleware_url["no"] + "{z}/{x}/{y}"
        })
    }),
    "topo": new ol.layer.Tile({
        source: new ol.source.XYZ({
            url: middleware_url["topo"]
        })
    })
};

/**
 * Style of the track. Define all used types (waypoint, line, and multi line).
 */
var track_style = {
    // default waypoint
    "Point": new ol.style.Style({
        image: new ol.style.Circle({
            fill: new ol.style.Fill({
                color: "rgba(255, 255, 0, 0.8)"
            }),
            radius: 5,
            stroke: new ol.style.Stroke({
                color: "rgba(0, 0, 255, 0.8)",
                width: 3
            })
        })
    }),
    // Viking sym: Campground
    "PointCampground": new ol.style.Style({
        text: new ol.style.Text({
            text: '\uf6bb', // fas fa-campground
            font: '900 ' + icon_size + ' "Font Awesome 5 Free"',
            textBaseline: 'middle',
            fill: new ol.style.Fill({
                color: "rgba(255, 255, 0, 0.8)"
            }),
            stroke: new ol.style.Stroke({
                color: "rgba(0, 0, 255, 0.8)",
                width: 3
            })
        })
    }),
    // Viking sym: Fishing Hot Spot Facility used as hut
    "PointFishingHotSpotFacility": new ol.style.Style({
        text: new ol.style.Text({
            text: '\uf015', // fas fa-home
            font: '900 ' + icon_size + ' "Font Awesome 5 Free"',
            textBaseline: 'middle',
            fill: new ol.style.Fill({
                color: "rgba(255, 255, 0, 0.8)"
            }),
            stroke: new ol.style.Stroke({
                color: "rgba(0, 0, 255, 0.8)",
                width: 3
            })
        })
    }),
    // Start point
    "PointStart": new ol.style.Style({
        text: new ol.style.Text({
            text: '\uf3c5', // fas fa-map-marker-alt
            font: '900 ' + icon_size + ' "Font Awesome 5 Free"',
            textBaseline: 'middle',
            fill: new ol.style.Fill({
                color: "rgba(255, 255, 0, 0.8)"
            }),
            stroke: new ol.style.Stroke({
                color: "rgba(0, 0, 255, 0.8)",
                width: 3
            })
        })
    }),
    // Progress
    "PointHiker": new ol.style.Style({
        text: new ol.style.Text({
            text: '\uf6ec', // fas fa-hiking
            font: '900 ' + icon_size + ' "Font Awesome 5 Free"',
            textBaseline: 'middle',
            fill: new ol.style.Fill({
                color: "rgba(255, 255, 0, 0.8)"
            }),
            stroke: new ol.style.Stroke({
                color: "rgba(0, 0, 255, 0.8)",
                width: 3
            })
        })
    }),
    // Start point
    "PointEnd": new ol.style.Style({
        text: new ol.style.Text({
            text: '\uf787', // fas fa-carrot
            font: '900 ' + icon_size + ' "Font Awesome 5 Free"',
            textBaseline: 'middle',
            fill: new ol.style.Fill({
                color: "rgba(255, 255, 0, 0.8)"
            }),
            stroke: new ol.style.Stroke({
                color: "rgba(0, 0, 255, 0.8)",
                width: 3
            })
        })
    }),
    // route
    "LineString": new ol.style.Style({
        stroke: new ol.style.Stroke({
            color: "rgba(0, 0, 255, 0.7)",
            width: 3
        })
    }),
    // track
    "MultiLineString": new ol.style.Style({
        stroke: new ol.style.Stroke({
            color: "rgba(255, 0, 0, 0.7)",
            width: 3
        })
    })
};

/**
 * The moving feature on the map when the user moves on the elevation profile.
 */
var hiker = new ol.Feature({
    geometry: new ol.geom.Point([0,0]),
    name: "Progress",
    sym: "Hiker"
});

/**
 * False if the hiker is not on map yet. True if the hiker is hiking.
 * Don't display the hiker before to know the first position.
 * @see label_elevation()
 */
var hiker_on_map = false;

/**
 * The actual track. Apply style to each feature. If a feature is a waypoint,
 * then the Viking sym name may be used.
 */
var track_vector = new ol.layer.Vector({
    source: new ol.source.Vector({}),
    style: function(feature) {
        if(feature.getGeometry().getType() == "Point") {
            return track_style[feature.getGeometry().getType() + feature.get("sym").replace(/\s+/g, "")];
        }
        return track_style[feature.getGeometry().getType()];
    }
});

/**
 * Refresh the opacity of the aerial view according to the slider.
 */
function refresh_opacity() {
    var opacity = Number($("#opacity-slider").slider("value"));

    if(opacity > 100) {
        opacity = 100;
    }
    else if(opacity < 0) {
        opacity = 0;
    }

    $("#opacity-slider-value").html(opacity);
    raster[country_code].setOpacity(opacity / 100.);
    raster["satellite"].setOpacity(opacity / 100.);
}

/**
 * If the cursor is over a waypoint, its description is displayed on a tooltip.
 */
function display_tooltip(evt) {
    var pixel = evt.pixel;
    tooltip = $("#tooltip-waypoint").tooltip();
    var feature = map.forEachFeatureAtPixel(pixel, function(feature) {
        return feature;
    });
    if(feature && feature.getGeometry().getType() == "Point") {
        overlay.setPosition(evt.coordinate);
        tooltip.prop("title", feature.get("name"));
        tooltip.tooltip("open");
    }
    else {
        tooltip.tooltip("close");
    }
}

/**
 * Zoom in or out and animate the transition.
 * Maximum and minimum zooms are defined by the map (maxZoom and minZoom).
 */
function zoom(zoom_increment) {
    map.getView().animate({
        zoom: map.getView().getZoom() + zoom_increment,
        duration: duration_zoom_animation
    });
}

/**
 * Add or move the position pointed by the user on the map along the track.
 */
function update_hiker_pos(tooltip_item, data) {
    var el = data.datasets[tooltip_item.datasetIndex].data[tooltip_item.index];
    hiker.getGeometry().setCoordinates([el.lon, el.lat]);
    if(!hiker_on_map) {
        var source = track_vector.getSource();
        source.addFeature(hiker);
        hiker_on_map = true;
    }
}

/**
 * Read the `webtrack` and save the features into `source`.
 * @see label_elevation()
 * @param {Dict} data See map_viewer.fetch_data().
 * @param {SourceType} source The OpenLayers source.
 */
function webtrack_to_source(data, source) {
    var trk = data.points;
    var coords = [];
    var features = [];
    for(var i = 0; i < trk.length; i++) {
        coords.push([trk[i][0], trk[i][1]]);
    }
    var trk_feature = new ol.Feature({
        geometry: new ol.geom.MultiLineString([coords], 'XY')
    });
    features.push(trk_feature);

    var starting_point = new ol.Feature({
        geometry: new ol.geom.Point(coords[0]),
        name: "Start",
        sym: "Start"
    });
    features.push(starting_point);
    var ending_point = new ol.Feature({
        geometry: new ol.geom.Point(coords[coords.length - 1]),
        name: "End",
        sym: "End"
    });
    features.push(ending_point);

    var waypoints = data.waypoints;
    for(var i = 0; i < waypoints.length; i++) {
        features.push(new ol.Feature({
            geometry: new ol.geom.Point([waypoints[i].lon, waypoints[i].lat]),
            name: waypoints[i].name,
            sym: waypoints[i].sym
        }));
    }
    source.addFeatures(features);
}

/**
 * Download the data and update the interface.
 */
function fetch_data() {
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
        var source = track_vector.getSource();
        let data = {
            statistics: webtrack.getTrackInfo(),
            points: webtrack.getTrack()[0].points,
            waypoints: webtrack.getWaypoints()
        }
        webtrack_to_source(data, source);

        map.getView().fit(source.getExtent(), {
            size: map.getSize(),
            padding: [track_padding, track_padding, track_padding, track_padding]
        });
        var center = ol.proj.transform(map.getView().getCenter(), "EPSG:3857", "EPSG:4326");
        console.log("Center: " + center);

        track_info(data);

        // display the "Track Info" button only when information are available
        $("#goto-gpx-info").show();
        $("#goto-download-gpx").show();
    };
    oReq.send();
}

/**
 * Set layers visibility based on the basemap selection.
 * @see init_basemap_selection()
 */
function select_basemap() {
    var is_country_specific = $("#country-specific-layers").is(":checked");
    raster_topo50[country_code].setVisible(is_country_specific);
    raster_topo50["topo"].setVisible(!is_country_specific);
    raster[country_code].setVisible(is_country_specific);
    raster["satellite"].setVisible(!is_country_specific);
    console.log("Layer selection: " + ((is_country_specific) ? "Country specific" : "Worldwide"));
    refresh_opacity();
}

/**
 * Initialise the basemap selection: two radio buttons. The Country Specific
 * basemap is selected by default.
 */
function init_basemap_selection() {
    $("input[type=radio]").checkboxradio({
        icon: false
    }).change(select_basemap);
    $("#country-specific-layers").prop("checked", true);
    select_basemap();
    $("input[type=radio]").checkboxradio("refresh");
}

/**
 * When the DOM is loaded and ready to be manipulated:
 *
 * * Create menu buttons.
 * * Display the map at a default position with a scale.
 * * Download the track and its profile.
 *
 */
$(function() {
    var url = new RegExp("/([^/]*)/([^/]*)/([^/]*)/([^/]*)$", "g").exec(window.location.href);

    if(url == null) {
        return;
    }

    book_id = url[1];
    book_url = url[2].toLowerCase();
    gpx_name = url[3];
    country_code = url[4].toLowerCase();
    offset_top = parseInt($("#goto-menu").offset().top);

    dialog = $("#menu").dialog({
        autoOpen: false,
        width: 600,
        minWidth: 500,
        position: { my: "right top", at: "right-10 top+" + offset_top},
        open: unfocus_menu,
        close: function() {
            $("#goto-menu").show();
        }
    });

    gpx_info = create_gpx_info_dialog();
    download_gpx = create_download_gpx_dialog();

    map = new ol.Map({
        target: document.getElementById("map"),
        layers: [
            raster_topo50[country_code],
            raster_topo50["topo"],
            raster[country_code],
            raster["satellite"],
            track_vector
        ],
        controls: [],
        view: new ol.View({
            center: ol.proj.transform(default_gps_position, "EPSG:4326", "EPSG:3857"),
            zoom: default_zoom,
            minZoom: min_zoom,
            maxZoom: max_zoom
        })
    });

    overlay = new ol.Overlay({
        element: document.getElementById("tooltip-waypoint"),
        offset: [10, 0],
        positioning: "bottom-left"
    });

    map.addOverlay(overlay);
    map.on("pointermove", display_tooltip);
    map.addControl(new ol.control.ScaleLine());
    
    fetch_data();

    $("#goto-menu").button({
        icon: "ui-icon-newwin"
    }).on("click", function() {
        dialog.dialog("open");
        $("#goto-menu").hide();
    });

    $("#opacity-slider").slider({
        max: 100,
        value: default_opacity,
        change: refresh_opacity,
        slide: refresh_opacity
    });

    $("#zoom-in").button({
        icon: "ui-icon-zoomin",
        showLabel: false
    }).on("click", function() {
        zoom(1);
    });

    $("#zoom-out").button({
        icon: "ui-icon-zoomout",
        showLabel: false
    }).on("click", function() {
        zoom(-1);
    });

    $(document).tooltip();
    init_basemap_selection();

    fit_breadcrumb();
});

$(window).resize(function() {
    fit_breadcrumb();
});
