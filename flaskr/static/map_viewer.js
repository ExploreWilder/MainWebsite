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
var default_opacity = 50;

/**
 * Duration of the zoom in/out animation in ms.
 * Default value is 300.
 */
var duration_zoom_animation = 300;

/**
 * URL to the LDS middleware. It can be an external link if a private key is not required.
 * Example: "/map/middleware/lds/" or "https://..."
 */
var middleware_url = {
    "nz": "/map/middleware/lds/",
    "fr": "/map/middleware/ign",
    "topo": "/map/middleware/topo/",
    "satellite": "/map/middleware/satellite/",
    "ca": "/map/middleware/canvec",
    "no": "/map/middleware/topografisk/"
};

/**
 * Minimum padding (in pixels) to be cleared inside the view, around the GPX track.
 * Padding may be excessive due to discret zoom.
 */
var track_padding = 5;

/**
 * Default position when the map is displayed.
 * The position is updated once the track is downloaded.
 */
var default_gps_position = [0, 0];

/**
 * Default zoom when the map is displayed.
 * The zoom is updated once the track is downloaded.
 */
var default_zoom = 7;

/**
 * Minimum zoom of the map.
 * It does not make sense to allow the user to zoom more than the map resolution.
 */
var min_zoom = 1;

/**
 * Maximum zoom of the map.
 * It does not make sense to allow the user to zoom out of the available range.
 */
var max_zoom = 19;

/**
 * Fontawesome icon size.
 * Default is 1em.
 */
var icon_size = "1em";

/**
 * Available resolutions for the IGN tiles.
 * Read the IGN documentation for further information.
 */
var resolutions = [
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
var matrix_ids = ["0","1","2","3","4","5","6","7","8","9","10","11","12","13","14","15","16","17","18","19"];

/**
 * Declared but always set'ed before get'ed.
 */
var book_id = null;

/**
 * Declared but always set'ed before get'ed.
 */
var book_url = null;

/**
 * Declared but always set'ed before get'ed.
 */
var gpx_name = null;

/**
 * Declared but always set'ed before get'ed.
 */
var country_code = null;

/**
 * Declared but always set'ed before get'ed.
 */
var dialog = null;

/**
 * Declared but always set'ed before get'ed.
 */
var gpx_info = null;

/**
 * Declared but always set'ed before get'ed.
 */
var download_gpx = null;

/**
 * Declared but always set'ed before get'ed.
 */
var map = null;

/**
 * Declared but always set'ed before get'ed.
 */
var overlay = null;

/**
 * Declared but always set'ed before get'ed.
 */
var tooltip = null;

/**
 * Returns a formatted link to the tiles.
 */
var get_tiles_link = function(layer) {
    return middleware_url["nz"] + layer + "/{a-d}/{z}/{x}/{y}";
};

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
            url: middleware_url["satellite"] + "{z}/{x}/{y}"
        }),
        opacity: default_opacity / 100.
    }),
    "ca": new ol.layer.Tile({
        source: new ol.source.XYZ({
            url: middleware_url["satellite"] + "{z}/{x}/{y}"
        }),
        opacity: default_opacity / 100.
    }),
    "satellite": new ol.layer.Tile({
        source: new ol.source.XYZ({
            url: "https://api.mapbox.com/v4/mapbox.satellite/{z}/{x}/{y}@2x.jpg90?access_token=" + MAPBOX_PUB_KEY
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
            url: "https://opentopomap.org/{z}/{x}/{y}.png"
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
var refresh_opacity = function() {
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
};

/**
 * If the cursor is over a waypoint, its description is displayed on a tooltip.
 */
var display_tooltip = function(evt) {
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
};

/**
 * Zoom in or out and animate the transition.
 * Maximum and minimum zooms are defined by the map (maxZoom and minZoom).
 */
var zoom = function(zoom_increment) {
    map.getView().animate({
        zoom: map.getView().getZoom() + zoom_increment,
        duration: duration_zoom_animation
    });
};

/**
 * Returns the content of the tooltip used in the elevation chart.
 * @see profile_to_source()
 */
var label_elevation = function(tooltip_item, data) {
    var label = "Elevation: " + tooltip_item.yLabel + " m | ";
    label += "Distance: " + (Math.round(tooltip_item.xLabel * 100) / 100) + " km";
    var el = data.datasets[tooltip_item.datasetIndex].data[tooltip_item.index];
    hiker.getGeometry().setCoordinates([el.lon - 485 + tooltip_item.index * 30, el.lat - 1567]);
    if(!hiker_on_map) {
        var source = track_vector.getSource();
        source.addFeature(hiker);
        hiker_on_map = true;
    }
    return label;
};

/**
 * Create the elevation chart based on the elevation profile of the track.
 */
var create_elevation_chart = function(profile) {
    var ctx = $("#elevation-chart");
    var data = [];
    for(var i = 0; i < profile.length; i++) {
        data[i] = {x: profile[i][1], y: profile[i][0], lon: profile[i][2], lat: profile[i][3]};
    }
    var distance = data[data.length - 1][1];
    var elevation_chart = new Chart.Scatter(ctx, {
        data: {
            datasets: [{
                data: data,
                showLine: true,
                pointRadius: 0,
                borderColor: "black",
                backgroundColor: "#3f3",
                borderWidth: 1,
                label: "Elevation",
                fill: true
            }]
        },
        options: {
            title: {
                display: true,
                text: "Elevation Chart"
            },
            tooltips: {
				mode: "index",
				intersect: false,
                callbacks: {label: label_elevation}
            },
            scales: {
                xAxes: [{
                    type: "linear",
                    position: "bottom",
    				display: true,
    				scaleLabel: {
    					display: true,
    					labelString: "Distance (km)"
    				}
    			}],
    			yAxes: [{
                    type: "linear",
                    position: "left",
    				display: true,
    				scaleLabel: {
    					display: true,
    					labelString: "Elevation (m)"
    				}
    			}]
            },
            legend: {
                display: false
            },
            responsive: true,
            maintainAspectRatio: false
        }
    });
};

/**
 * Returns a string of the number x with commas on thousands.
 * NOTICE: identical to main.js
 */
var number_with_commas = function(x) {
    return x.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
};

/**
 * Update statistics displayed in the track info.
 */
var track_info = function(source) {
    var stats = source["statistics"];
    var ul = $("#gpx-info-list");
    var lis = [
        $('<li></li>').text("Total Length: " + (Math.round(stats["totalLength"] * 10) / 10) + " km"),
        $('<li></li>').text("Minimum Altitude: " + number_with_commas(stats["minimumAltitude"]) + " m"),
        $('<li></li>').text("Maximum Altitude: " + number_with_commas(stats["maximumAltitude"]) + " m"),
        $('<li></li>').html("<abbr title='Filtered radar data'>Total Elevation:</abbr> "
            + number_with_commas(stats["totalElevationGain"] - stats["totalElevationLoss"]) + " m (Gain: "
            + number_with_commas(stats["totalElevationGain"]) + " m, Loss: "
            + number_with_commas(stats["totalElevationLoss"]) + " m)")
        ];
    
    ul.append(lis);
    create_elevation_chart(source["profile"]);
};

/**
 * Read the XHR `data` and save the features into `source`.
 * @see label_elevation()
 * @param {Array} data XHR data, see map.fetch_data().
 * @param {SourceType} source The OpenLayers source.
 */
var profile_to_source = function(data, source) {
    var trk = data["profile"];
    var coords = [];
    var features = [];
    for(var i = 0; i < trk.length; i++) {
        coords.push([trk[i][2] - 485 + i * 30, trk[i][3] - 1567]);
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

    var waypoints = data["waypoints"];
    for(var i = 0; i < waypoints.length; i++) {
        features.push(new ol.Feature({
            geometry: new ol.geom.Point(waypoints[i].slice(2)),
            name: waypoints[i][0],
            sym: waypoints[i][1]
        }));
    }
    source.addFeatures(features);
};

/**
 * Download the data and update the interface.
 */
var fetch_data = function() {
    var oReq = new XMLHttpRequest();
    oReq.open("GET", "/map/profile/" + book_id + "/" + book_url + "/" + gpx_name + "/" + country_code, true);
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
        var source = track_vector.getSource();
        profile_to_source(data, source);

        map.getView().fit(source.getExtent(), {
            size: map.getSize(),
            padding: [track_padding, track_padding, track_padding, track_padding]
        });
        var center = ol.proj.transform(map.getView().getCenter(), "EPSG:3857", "EPSG:4326");
        console.log("Center: " + center);

        track_info(data);

        // display the "Track Info" button only when information are available
        $("#goto-gpx-info").show().button({
            icon: "ui-icon-newwin"
        }).on("click", function() {
            gpx_info.dialog("open");
                $("#goto-gpx-info").hide();
        });
        $("#goto-download-gpx").show().button({
            icon: "ui-icon-newwin"
        }).on("click", function() {
            download_gpx.dialog("open");
                $("#goto-download-gpx").hide();
        });
    };
    oReq.send();
};

/**
 * Blur the close button tooltip when the window is open.
 */
var unfocus_menu = function() {
    $(this).parents(".ui-dialog").attr("tabindex", -1)[0].focus();
};

/**
 * Set layers visibility based on the basemap selection.
 * @see init_basemap_selection()
 */
var select_basemap = function() {
    var is_country_specific = $("#country-specific-layers").is(":checked");
    raster_topo50[country_code].setVisible(is_country_specific);
    raster_topo50["topo"].setVisible(!is_country_specific);
    raster[country_code].setVisible(is_country_specific);
    raster["satellite"].setVisible(!is_country_specific);
    console.log("Layer selection: " + ((is_country_specific) ? "Country specific" : "Worldwide"));
    refresh_opacity();
};

/**
 * Initialise the basemap selection: two radio buttons. The Country Specific
 * basemap is selected by default.
 */
var init_basemap_selection = function() {
    $("input[type=radio]").checkboxradio({
        icon: false
    }).change(select_basemap);
    $("#country-specific-layers").prop("checked", true);
    select_basemap();
    $("input[type=radio]").checkboxradio("refresh");
};

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

    dialog = $("#menu").dialog({
        autoOpen: false,
        width: 600,
        minWidth: 500,
        position: { my: "right top", at: "right-10 top+10"},
        open: unfocus_menu,
        close: function() {
            $("#goto-menu").show();
        }
    });

    gpx_info = $("#gpx-info").dialog({
        autoOpen: false,
        width: 600,
        minWidth: 500,
        position: { my: "left top", at: "left+10 top+10"},
        open: unfocus_menu,
        resize: function(event, ui) {
            $("#elevation-chart-container").height($("#gpx-info").height() - $("#gpx-info-list").height());
            $("#elevation-chart-container").width($("#gpx-info").width());
        },
        close: function() {
            $("#goto-gpx-info").show();
        }
    });

    download_gpx = $("#download-gpx").dialog({
        autoOpen: false,
        width: 600,
        minWidth: 500,
        position: { my: "right bottom", at: "right-10 bottom-10"},
        open: unfocus_menu,
        close: function() {
            $("#goto-download-gpx").show();
        }
    });

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
});
