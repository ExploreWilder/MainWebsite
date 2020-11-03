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
 * Common functions used by map_viewer.js (2D) and map_player.js (3D).
 */

/**
 * Current block in focus.
 */
let current_menu_on_focus = "#gpxInfo";

/**
 * Returns the content of the tooltip used in the elevation chart.
 */
function label_elevation(tooltip_item, data) {
    var label = "Elevation: " + tooltip_item.yLabel + " m | ";
    label += "Distance: " + Math.round(tooltip_item.xLabel * 10) / 10 + " km";
    return label;
}

/**
 * Returns a string of the number x with commas on thousands.
 * NOTICE: identical to main.js
 */
function number_with_commas(x) {
    return x.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

/**
 * Update statistics displayed in the track info.
 */
function track_info(source) {
    var stats = source.statistics;
    var ul = $("#gpx-info-list");
    var lis = [
        $("<li></li>").text(
            "Total Length: " + Math.round(stats.length / 10) / 100 + " km"
        ),
        $("<li></li>").text(
            "Minimum Altitude: " + number_with_commas(stats.min) + " m"
        ),
        $("<li></li>").text(
            "Maximum Altitude: " + number_with_commas(stats.max) + " m"
        ),
        $("<li></li>").html(
            "<abbr title='Filtered radar data'>Total Elevation:</abbr> " +
                number_with_commas(stats.gain + stats.loss) +
                " m (Gain: " +
                number_with_commas(stats.gain) +
                " m, Loss: -" +
                number_with_commas(stats.loss) +
                " m)"
        ),
    ];

    ul.append(lis);
    create_elevation_chart(source.points);
}

/**
 * Create the elevation chart based on the elevation profile of the track.
 * NOTE: update_hiker_pos() has to be defined on the specific map viewer.
 */
function create_elevation_chart(profile) {
    var ctx = $("#elevation-chart");
    var data = [];
    for (var i = 0; i < profile.length; i++) {
        data[i] = {
            x: profile[i][2] / 1000,
            y: profile[i][3],
            lon: profile[i][0],
            lat: profile[i][1],
        };
    }
    var distance = data[data.length - 1][1];
    var elevation_chart = new Chart.Scatter(ctx, {
        data: {
            datasets: [
                {
                    data: data,
                    showLine: true,
                    pointRadius: 0,
                    borderColor: "black",
                    backgroundColor: "#3f3",
                    borderWidth: 1,
                    label: "Elevation",
                    fill: true,
                },
            ],
        },
        options: {
            title: {
                display: true,
                text: "Elevation Chart",
            },
            tooltips: {
                mode: "index",
                intersect: false,
                callbacks: {
                    label: (tooltip_item, data) => {
                        update_hiker_pos(tooltip_item, data);
                        return label_elevation(tooltip_item, data);
                    },
                },
            },
            scales: {
                xAxes: [
                    {
                        type: "linear",
                        position: "bottom",
                        display: true,
                        scaleLabel: {
                            display: true,
                            labelString: "Distance (km)",
                        },
                    },
                ],
                yAxes: [
                    {
                        type: "linear",
                        position: "left",
                        display: true,
                        scaleLabel: {
                            display: true,
                            labelString: "Elevation (m)",
                        },
                    },
                ],
            },
            legend: {
                display: false,
            },
            responsive: true,
            maintainAspectRatio: false,
        },
    });
}

/**
 * Returns the path of the WebTrack file.
 */
function get_webtrack_url(book_id, gpx_name) {
    return `/map/webtracks/${book_id}/${gpx_name}.webtrack`;
}

/**
 * Display the buttons only when the track information are available.
 */
function display_gpx_buttons() {
    $("#goto-gpx-info").css("display", "inline-block");
    $("#goto-download-gpx").css("display", "inline-block");
}

/**
 * GPX info OR layer selection but not both menus at the same time.
 */
function manage_subnav_click() {
    $("#subNavbarNav a[aria-controls]").click(function () {
        let new_menu_on_focus = $(this).attr("aria-controls");
        $(".map-viewer-interface .card-menu, #dropdownMenuBoundLayer").hide();
        if (current_menu_on_focus != new_menu_on_focus) {
            current_menu_on_focus = new_menu_on_focus;
            // using $("body").find(node) instead of $(node) prevent XSS attack (source: CodeQL)
            $("body").find(current_menu_on_focus).show();
        } else {
            current_menu_on_focus = null;
        }
        $(this).blur();
        return false;
    });

    $("#goto-download-gpx").click(function () {
        let modal_el = $(this).attr("aria-controls");
        $("body").find(modal_el).modal("show");
        $(this).blur();
        return true;
    });
}
