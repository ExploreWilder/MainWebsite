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
 * Show a big image in the background if the following tag exists in the page:
 * <div id="outer-bg-body" data-bgsrc="/static/images/....jpg"><div id="inner-bg-body"></div></div>
 * The background is CSS-filtered to render in black and white and events may add the missing colors.
 */
class BackgroundAnimation {
    /**
     * Percent of black and white. 100 for completely B&W.
     */
    #current_bw = 100;

    /**
     * The interval in ms between two updates of the opacity animation on background load.
     */
    #opacity_interval_period = 10;

    /**
     * The interval increment to apply on every opacity update. The opacity is between 0 and 1.
     */
    #opacity_interval_inc = 0.01;

    /**
     * Shared interval timer for the coloring effect.
     */
    #bw_interval;

    /**
     * The interval in ms between two updates of the coloring animation.
     */
    #bw_interval_period = 20;

    /**
     * The interval increment to apply on every color update. The B&W color filter is between 0 and 100.
     */
    #bw_interval_inc = 5;

    /**
     * How far from the top of the window to trigger a Scrollama step, between 0 (top) and 1 (bottom).
     */
    #scrollama_offset = 0.3;

    /**
     * The path to the background image.
     */
    #image_src = $("#outer-bg-body").attr("data-bgsrc");

    /**
     * The background image.
     */
    #image = new Image();

    /**
     * Download the background image and show it on load, and setup the color change events.
     */
    constructor() {
        if($("#scroll-about-page").length) { // about page
            this.scroll_config();
        }

        if($(".trigger-bg-colors").length) { // the Patreon and the login buttons in the login page
            this.mouse_events_config();
        }

        // start with B&W (defined here instead of the CSS file to avoid MS Edge bug)
        $("#outer-bg-body").css("filter", "grayscale(100%)");
        $(this.#image).on("load", () => {
            this.display_background();
        });
        this.#image.src = this.#image_src;
    }

    /**
     * Configure the color change events in the about page.
     */
    scroll_config() {
        var scroller_about = scrollama();
        scroller_about
        .setup({
            step: "#scroll-about-page .step",
            offset: this.#scrollama_offset
        })
        .onStepEnter((response) => {
            if($(response.element).attr("data-step") == "contact") {
                this.change_colors(false); // huray! the user may contact, follow, or support me!
            }
        })
        .onStepExit((response) => {
            if($(response.element).attr("data-step") == "contact" && response.direction == "up") {
                this.change_colors(true); // oh no! the user go back to the boring "About Me" text.
            }
        });
        window.addEventListener("resize", scroller_about.resize);
    }

    /**
     * Configure the color change events in the login page.
     */
    mouse_events_config() {
        $(".trigger-bg-colors")
        .mouseenter(() => {
            this.change_colors(false);
        })
        .mouseleave(() => {
            this.change_colors(true);
        });
    }

    /**
     * Change the background colors from/to fully colored to/from B&W.
     * @param colors_to_bw {Boolean} - True to update toward B&W, false to update toward colors.
     */
    change_colors(colors_to_bw) {
        clearInterval(this.#bw_interval);
        this.#bw_interval = setInterval(() => {
            if(colors_to_bw) {
                this.#current_bw += this.#bw_interval_inc;
                $("#outer-bg-body").css("filter", `grayscale(${this.#current_bw}%)`);
                if(this.#current_bw > 100) {
                    this.#current_bw = 100;
                    clearInterval(this.#bw_interval);
                }
            }
            else {
                this.#current_bw -= this.#bw_interval_inc;
                $("#outer-bg-body").css("filter", `grayscale(${this.#current_bw}%)`);
                if(this.#current_bw < 0) {
                    this.#current_bw = 0;
                    clearInterval(this.#bw_interval);
                }
            }
        }, this.#bw_interval_period);
    }
    
    /**
     * Display the downloaded background with a background color transition (white to image).
     */
    display_background() {
        var opacity = 1; // start with a white background
        var opacity_interval = setInterval(() => {
            opacity -= this.#opacity_interval_inc;
            $("#inner-bg-body").css("background-color", `rgba(255, 255, 255, ${opacity})`);
            if(opacity < 0) {
                clearInterval(opacity_interval);
            }
        }, this.#opacity_interval_period);

        $("#outer-bg-body").css({
            "background-image": `url('${this.#image_src}')`
        });
    }
}

$(function() {
    if($("#inner-bg-body").length && $("#outer-bg-body").length) {
        bg = new BackgroundAnimation();
    }
});
