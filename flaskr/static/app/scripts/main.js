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
 * Number of photos to fetch in a single asynchronous request. Must be > 1.
 * Default value is 9 and changed at default_total_new_photos() call.
 */
var total_new_photos = default_total_new_photos;

/**
 * Id (from 0) of the current or the latest loaded big photo.
 * Default value is -1 (no one photo already loaded).
 */
var last_loaded_photo = -1;

/**
 * Information about the thumbnails/photos fetched asynchronously.
 * Default value is [], nothing is fetched at the beginning.
 */
var gallery = [];

/**
 * True when the number of photos received asynchronously is less than asked.
 * Default value is false in order to try to load at least one photo.
 */
var no_more_photos = false;

/**
 * True if the user is in auto play mode.
 * Default value is false.
 */
var is_autoplay = false;

/**
 * Used by the onscroll event.
 */
var scroll_ticking = false;

if(typeof(String.prototype.trim) === "undefined") {
    /**
     * Remove spaces after and before the string.
     */
    String.prototype.trim = function() {
        return String(this).replace(/^\s+|\s+$/g, "");
    };
}

/**
 * Example of use: $.urlParam('param'); returns 'value' or null.
 * @param name Parameter name.
 */
$.urlParam = function(name) {
    var results = new RegExp('[\?&]' + name + '=([^&#]*)').exec(window.location.href);
    return (results == null) ? null : (results[1] || 0);
};

/**
 * Increase the amount of thumbnails to load so that even high screen has a scrollbar.
 * Indeed, the user cannot load more thumbnails if he doesn't scroll down
 * and he may want to load more thumbnails simultaneously to fill the large screen.
 */
function adapt_amount_thumbnails_to_fetch() {
    var overflow = (max_column_photos * $(window).height() / get_thumbnail_height()) - total_new_photos;
    
    if(overflow > 0) {
        total_new_photos = default_total_new_photos + max_column_photos * parseInt(overflow);
    }
}

/**
 * Wrap the ``text`` with the HTML <p> tag and replace double new lines by a new
 * HTML paragraph and new lines by the <br /> tag.
 * @param text {String} - Raw text.
 * @return {String} Text with <p>s, </p>s and <br />s.
 */
function text_to_html(text) {
    text = text.trim().replace(/\n\n/g, "</p><p>").replace(/\n/g, "<br />");
    return "<p>" + text + "</p>";
}

/**
 * Update the padding on top of the page so that the content stays below the navbar.
 */
function move_body() {
    // the fixed navbar will not overlay the gallery
    $("body").css("padding-top", get_header_height());
}

/**
 * Get the height of the navbar plus a margin.
 * @see move_body()
 * @return {Number} Minimum gap from top where blocks should be displayed.
 */
function get_header_height() {
    return ($("#header").css("display") != "none") ? ($("#header").height() + 16) : 0;
}

/**
 * Hide/show the main window and disable/enable the scroll bar.
 * The scroll position is restored when the main window is re-visible.
 * @see main_is_active()
 * @param is_active {Number} - true to display the main window and the scroll bar.
 */
function main_active(is_active) {
    if(is_active) {
        $("body").css("overflow", "auto");
        $("#main").css("visibility", "visible");
    }
    else {
        $("#main").css("visibility", "hidden");
        $("body").css("overflow", "hidden");
    }
}

/**
 * Check if the main window - gallery - is visible.
 * @see main_active()
 * @return {Boolean} true if visible.
 */
function main_is_active() {
    return $("#main").css("visibility") == "visible";
}

/**
 * Hide the big photo and show the main window.
 * @see main_active()
 */
function close_photo() {
    last_loaded_photo = -1; // unset the last loaded photo - see preload_photo() and load_photo()
    disable_autoplay();
    $("#full-screen").hide();
    enable_header(true);
    main_active(true);
    return false;
}

/**
 * Returns a string of the number x with commas on thousands.
 * NOTICE: identical to map_viewer.js
 */
function number_with_commas(x) {
    return x.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

/**
 * Just close the big photo if the user click on the "Gallery" when the big photo
 * is loaded.
 * @param a DOM element of the link.
 * @return {Boolean} False if the big photo was loaded - to disable the page reload. True otherwise.
 */
function close_large_photo(a) {
    if(!main_is_active()) {
        close_photo();
        $(a).blur();
        return false;
    }
    return true;
}

/**
 * Update the interface mode into downloading mode when a big photo is displayed.
 * The procedure calls load_photo() so the interface will be updated again when
 * the new big photo is ready to be displayed.
 * @see load_photo()
 * @return {Boolean} Always false (in order to disable the html link.)
 */
function prev_next_buttons_onclick(index) {
    $('#animated-description abbr[data-toggle="tooltip"]').tooltip("dispose");
    $("#button-next").css("visibility", "hidden");
    $("#button-auto").css("visibility", "hidden");
    $("#button-prev").css("visibility", "hidden");
    $("#animated-download").hide().fadeIn(fade_in_download_in_progress);
    load_photo(index);
    return false;
}

/**
 * Update the auto play mode (button and global var).
 * @return {Boolean} - Always false (in order to disable the html link.)
 */
function autoplay_button() {
    is_autoplay = !is_autoplay;
    
    $("#button-auto").blur();
    
    if(is_autoplay) {
        $("#button-auto").find(".fa-play-circle")
                         .removeClass("fa-play-circle")
                         .addClass("fa-pause-circle");
        
        reset_timer_autoplay();
        
        console.log("Autoplay mode: enabled");
    }
    else {
        $("#button-auto").find(".fa-pause-circle")
                         .removeClass("fa-pause-circle")
                         .addClass("fa-play-circle");
        
        clearInterval(timer_autoplay);
        timer_autoplay = 0;
        
        console.log("Autoplay mode: disabled");
    }
    return false;
}

/**
 * Start the timer or restart it if already running. That way the timeout
 * is reset (when the user clicks on next in auto play mode).
 */
function reset_timer_autoplay() {
    if(typeof timer_autoplay != "undefined") {
        clearInterval(timer_autoplay);
        timer_autoplay = null;
    }
    timer_autoplay = setInterval(function() {
        prev_next_buttons_onclick(last_loaded_photo +1);
    }, autoplay_interval);
}

/**
 * Disable the auto play mode if enabled.
 */
function disable_autoplay() {
    if(is_autoplay)
    {
        autoplay_button();
    }
}

/**
 * Called when a new photo is loaded in order to:
 *
 * * fetch new photos if ``index`` refers to one of the last 3 photos.
 * * hide the next/prev button if the next/prev photo is out of range.
 * * update the onclick events of the prev/next buttons.
 * 
 * Notice: the auto play mode is disabled when the user loads the previous
 * picture and the timer is reset when the user loads the next one to avoid
 * fast jump.
 *
 * @see fetch_thumbnails()
 * @param index {Number} - Id (from 0) of the new big photo.
 */
function update_prev_next_buttons(index) {
    if(typeof index != "number") {
        return;
    }

    if((index +3) >= gallery.length) {
        if(!no_more_photos) {
            fetch_thumbnails(total_new_photos);
        }
    }

    if((index +1) >= gallery.length) {
        $("#button-next").css("visibility", "hidden");
        $("#button-auto").css("visibility", "hidden");
        disable_autoplay();
    }
    else {
        $("#button-next").css("visibility", "visible");
        $("#button-next").unbind("click");
        $("#button-next").click(function() {
            $("#button-next").blur();
            if(is_autoplay) {
                reset_timer_autoplay();
            }
            return prev_next_buttons_onclick(index +1);
        });
        
        $("#button-auto").css("visibility", "visible");
        $("#button-auto").unbind("click");
        $("#button-auto").click(autoplay_button);
    }

    if(index <= 0) {
        $("#button-prev").css("visibility", "hidden");
    }
    else {
        $("#button-prev").css("visibility", "visible");
        $("#button-prev").unbind("click");
        $("#button-prev").click(function() {
            $("#button-prev").blur();
            disable_autoplay();
            return prev_next_buttons_onclick(index -1);
        });
    }
}

/**
 * If ``is_bind`` is true, then the emoji buttons are visible and binded so that
 * the emotion is shared.
 * @param is_bind {Boolean} - True to show and bind, false to hide and unbind.
 */
function bind_emotions(is_bind) {
    for(var i = 0; i < emotions.length; i++) {
        var emotion = emotions[i];
        var a = $("#button-" + emotion).parent("a");
        a.css("visibility", (is_bind) ? "visible" : "hidden");
        a.unbind("click");
        if(is_bind) {
            a.click((function() {
                var current_emotion = emotion;
                return function() {
                    return share_emotion(current_emotion);
                };
            })());
        }
    }
}

/**
 * Update the emotion of the last viewed big photo in the database, hide the
 * buttons and display a modal window. The auto play mode is disabled.
 * @see bind_emotions()
 * @param emotion {String} - Element of the 'emotions' list.
 * @return {Boolean} False.
 */
function share_emotion(emotion) {
    bind_emotions(false); // hide the buttons to avoid multi-request
    disable_autoplay();
    $.ajax({
        url: url_share_emotion_photo,
        async: true,
        method: "POST",
        data: {emotion: emotion},
        dataType: "json",
        success: function(result) {
            if(result.success) {
                reset_feedback_form();
                $("#modal-feedback").modal();
                console.log("Emotion shared: " + emotion);
            }
        }
    });
    return false;
}

/**
 * Log the visitor/member visit since he has just viewed a big photo. Disable
 * the `emotion` buttons until the visit has been logged since the log is
 * required to share the emotion.
 * @see display_photo()
 * @see bind_emotions()
 */
function log_visit() {
    bind_emotions(false);
    $.ajax({
        url: url_log_visit_photo,
        async: true,
        method: "POST",
        data: {photo_id: gallery[last_loaded_photo].id},
        success: function() {
            bind_emotions(true);
        }
    });
}

/**
 * Check if the photo is a panorama according to its ratio.
 * @param width {Number} - Photo width.
 * @param height {Number} - Photo height.
 * @return {Boolean} True if the width is at least three times the height.
 */
function is_panorama(width, height) {
    return width > 3 * height;
}

/**
 * Hide or show the navbar.
 * @param enable {Boolean} - True to show, false to hide the navbar.
 */
function enable_header(enable) {
    if(enable) {
        $("#header").css("display", "fixed");
        $("#header").show();
    }
    else {
        $("#header").hide();
        $("#header").css("display", "none");
    }
}

/**
 * Display a big photo or update its size. Update the interface as well. If
 * ``photo`` is an image, it will replace the current one. Otherwise the current photo
 * will stay active and would be resized. If there is no argument given and no
 * active photo either, then nothing is changed. Check the log in case of trouble.
 * @see update_prev_next_buttons()
 * @see log_visit()
 * @param photo {Image} - The cached new big photo or keep the current one or do nothing.
 * @param index {Number} - Id (from 0) of the new big photo.
 */
function display_photo(photo, index) {
    var src_photo;
    var new_photo = false;

    if(typeof photo == "object") {
        src_photo = $(photo).attr("src");
        if(photo.naturalWidth === 0 || typeof photo.naturalWidth == "undefined") {
            console.log("ERROR: Full screen photo '" + src_photo + "' could not be loaded.");
            return;
        }
        console.log("Full screen photo ready.");

        main_active(false); // remove the scroll bar before to get the window size
        new_photo = true;
    }
    else if (main_is_active()) { // don't re-display if the photo hasn't been loaded
        return;
    }
    else { // don't change the source
        src_photo = $("#full-screen-photo").attr("src");
        photo = new Image();
        photo.src = src_photo;
    }

    // hide the navbar on small devices to enlarge the photo
    enable_header($(window).height() > small_devices_height);

    var photo_width = photo.naturalWidth;
    var photo_height = photo.naturalHeight;
    var ratio = photo_height / photo_width;
    var navbar_height = get_header_height();
    var box_height = $(window).height() - navbar_height - total_gap_photo * 2;
    var box_width = $(window).width() - total_gap_photo * 2;
    
    // square button, all the same size defined by what is currently visible
    var button_size = $("#button-close").width() || $("#onclick-scroll-down i").height();
    photo_is_panorama = is_panorama(photo_width, photo_height);

    // resize the photo to fit the buttons and the photo in the box
    if(box_height < photo_height) {
        photo_height = box_height;
        photo_width = photo_height / ratio;
    }
    if((!photo_is_panorama) && box_width < photo_width + total_gap_photo + button_size) {
        photo_width = box_width - total_gap_photo - button_size;
        photo_height = photo_width * ratio;
    }
    
    // Change the max-width tag since changing the image width creates a
    // short lag when the old pictures is resized but the new one is not
    // displayed yet, so if the new picture has a different size, the old
    // picture would look weird for a few miliseconds.
    $("#full-screen-photo").css("max-width", photo_width);
    
    if(new_photo) {
        $("#full-screen-photo").attr("src", src_photo);
        var info = "";
        if(gallery[index].title != "") {
            info = "<h1>" + gallery[index].title + "</h1>";
        }
        if(gallery[index].description == "[undisclosed]") {
            info += $("#why-undisclosed").html();
        }
        else if(gallery[index].description != "") {
            info += text_to_html(gallery[index].description);
        }
        var exif = [];
        if(gallery[index].focal_length_35mm != null) {
            exif.push('<abbr data-toggle="tooltip" title="35 mm equivalent focal length">'
                + gallery[index].focal_length_35mm + ' mm</abbr>');
        }
        if(gallery[index].exposure_time != null) {
            exif.push('<abbr data-toggle="tooltip" title="Exposure time in seconds">'
                + gallery[index].exposure_time + ' s</abbr>');
        }
        if(gallery[index].f_number != null) {
            exif.push('<abbr data-toggle="tooltip" title="Focal ratio">f/'
                + gallery[index].f_number + '</abbr>');
        }
        if(gallery[index].iso != null) {
            exif.push('<abbr data-toggle="tooltip" title="Film speed">ISO '
                + gallery[index].iso + '</abbr>');
        }
        if(gallery[index].time != null) {
            info += '<p class="desc-field-time">Photo took ' + gallery[index].time + '.</p>';
        }
        if(exif.length) {
            var separator = ' <span class="pipe">|</span> ';
            info += '<p class="desc-field-conf">Camera configuration:<br />' + exif.join(separator) + '</p>';
        }
        $("#photo-description").html(info);
        last_loaded_photo = index;
    }
    else {
        console.log("Full screen photo resized.");
    }

    // update interface
    if($("#animated-description:hover").length != 0) {
        fade_in_description();
    }

    update_prev_next_buttons(index);
    var gap_on_right_side = (box_width - photo_width) / 2;
    var offset_photo_left = total_gap_photo;
    var offset_y = navbar_height + total_gap_photo;

    if(gap_on_right_side >= total_gap_photo + button_size) {
        offset_photo_left += gap_on_right_side;
    }
    
    if(photo_is_panorama) {
        var container_width = box_width - total_gap_photo - button_size;
        $("#animated-description").css("max-width", container_width);
        $("#animated-description").mousemove(function(evt) {
            var ratio = container_width / photo_width;
            var hscroll_width = container_width * ratio;
            var pos_half_scroll = evt.pageX - total_gap_photo - hscroll_width / 2;
            $(this).scrollLeft(pos_half_scroll / ratio).css("cursor", "ew-resize");
        });
    }
    else {
        $("#animated-description").off("mousemove").css("cursor", "default");
    }

    $("#full-screen").css("left", offset_photo_left);
    $("#full-screen").css("top", navbar_height + total_gap_photo);
    var button = ["close", "love", "next", "prev", "auto"];
    for(var i = 0; i < button.length; i++) {
        $("#button-" + button[i]).css("right", total_gap_photo);
        $("#button-" + button[i]).css("top", offset_y + i * (button_size + total_gap_photo));
    }
    $("#full-screen").css("top", navbar_height + total_gap_photo);
    $("#animated-download").css("top", navbar_height + 3);
    $("#animated-download").stop(); // stop any asynchronous animation before to hide
    $("#animated-download").hide();

    // show the buttons if not visible
    $("#full-screen").show();

    if(new_photo) {
        // show the photo, its description, and the prev/next buttons
        $("#animated-full-screen").show();

        log_visit();
    }
}

/**
 * Called to make the animation on the clicked thumbnail, waiting for the big
 * photo to be loaded. If the main window is active, the thumbnail fade in and
 * the spinner fade out. Otherwise the animation is stopped and the spinner is
 * removed.
 * @see load_photo()
 * @param thumbnail {Image} - Reference to the thumbnail.
 */
function load_on_thumbnail(thumbnail) {
    if(main_is_active()) {
        thumbnail.fadeTo(fade_out_thumbnail, opacity_thumbnail);
        var img_spinner = $('<i></i>');
        img_spinner.addClass('far fa-compass fa-2x fa-spin thumbnail-spin');
        var spinner = $('<span></span>');
        spinner.addClass("around-spin");
        spinner.append(img_spinner);
        spinner.css("animation-duration", (fade_out_thumbnail / 1000) + "s");
        thumbnail.after(spinner);
    }
    else {
        thumbnail.stop(); // stop the fadeTo animation
        thumbnail.css("opacity", 1);
        thumbnail.next().remove(); // remove the spinner
    }
}

/**
 * Find out the optimal photo size according to the screen resolution. If the
 * image is a panorama, then the large size is chosen.
 * @see is_panorama()
 * @see load_photo()
 * @param photo {Struct} - Element of the gallery.
 * @return {String} Filename of the optimal photo.
 */
function optimal_photo(photo) {
    if($(window).width() > m_size[0] || $(window).height() > m_size[1]) {
        console.log("Optimal photo size is large.");
        return photo.photo_l;
    }
    else if(is_panorama(photo.photo_l_w, photo.photo_l_h)) {
        console.log("Panorama => load large.");
        return photo.photo_l;
    }
    else {
        console.log("Optimal photo size is medium.");
        return photo.photo_m;
    }
}

/**
 * Load a photo in the cache. The Image object is only used for caching
 * and a new one will be used by load_photo() with the cached file.
 * @param index {Number} - Id (from 0) of the photo.
 */
function preload_photo(index) {
    if(index < 0 || index >= gallery.length) {
        return; // out of range
    }
    var photo_name = optimal_photo(gallery[index]);
    var src_photo = dir_photos + gallery[index].id + "/" + photo_name;
    console.log("Caching '" + src_photo + "'...");
    var photo = new Image();
    $(photo).on("load", function() {
        console.log("Photo '" + photo_name + "' now in cache");
    });
    $(photo).on("error", function() {
        console.log("ERROR: failed to cache image " + photo_name);
    });
    photo.src = src_photo;
}

/**
 * Load gallery[``index``] in cache. Animate the thumbnail in download mode if visible.
 * Load the next/previous photo if an error occured and print out error on console.
 * The next (or previous) photo is cached after the successful photo update.
 * @param index {Number} - Id (from 0) of the new big photo.
 */
function load_photo(index) {
    var img = $("#gallery a").eq(index).find("img");
    var photo_name = optimal_photo(gallery[index]);
    var src_photo = dir_photos + gallery[index].id + "/" + photo_name;
    var next_photo = (last_loaded_photo > 0) ? (2 * index - last_loaded_photo) : (index +1);
    console.log("Open '" + src_photo + "'.");

    // loading effect
    load_on_thumbnail(img);

    var photo = new Image();
    $(photo).on("load", function() {
        display_photo(this, index);
        load_on_thumbnail(img);
        preload_photo(next_photo);
    });

    $(photo).on("error", function() {
        // skip the photo and load the next/previous one
        console.log("ERROR: loading image " + photo_name + " failed => jump over!");
        load_photo(next_photo);
    });

    // fetch the photo
    photo.src = src_photo;

    return false;
}

/**
 * Create a JQuery image with the source ``src`` and the identifier ``id`` and
 * append to ``a`` if the image has successfully been loaded, i.e. asynchronously.
 * The message in the console is for example:
 *
 * * "Thumbnail [148] loaded." if the image has successfully been loaded.
 * * "ERROR loading thumbnail [144]: /photos/14/wavr4ysu4r8m6f1tg7vc.jpg" if loading failed.
 *
 * @param src {String} - Source file of the image.
 * @param id {Number} - Identifier of the image.
 * @param a {Object} - JQuery link already appended in the gallery.
 * @see fetch_thumbnails()
 */
function img_thumbnail(src, id, a) {
    $("<img />")
    .attr("src", src)
    .addClass("animate-shadow")
    .on("error", function(event) {
        console.log("ERROR loading thumbnail " + id + ": " + src);
    })
    .on("load", function(event) {
        console.log("Thumbnail " + id + " loaded.");
        $(this).appendTo(a);
    });
}

/**
 * Fetch ``total`` thumbnails. Only metadata are downloaded and thumbnails are
 * cached and displayed. Any call to this function before the successful process
 * of the last call is ignored. In other words, the function waits for the last
 * XHR to send back the information before to ask more. That is to avoid race
 * condition and server overload, and it is still asynchronous in a way that
 * other functions can proceed.
 * @param total {Number} - Number of thumbnail/photo to fetch.
 */
var fetch_thumbnails = (function(total) {
    var in_progress = false;
    return function(total) {
        if(in_progress) {
            return;
        }
        in_progress = true;
        var thumbnails = $("#gallery");

        // fetch @p total thumbnails/photos if possible
        $.ajax({
            url: url_fetch_photos,
            async: true,
            method: "POST",
            data: {offset: gallery.length, total: total},
            dataType: "json",
            success: function(result) {
                in_progress = false;
                for(var i = 0; i < result.length; i++) {
                    gallery.push(result[i]);
                    var a = $("<a></a>")
                        .attr("href", "#")
                        .appendTo(thumbnails) // append `a` to the gallery in a specific order
                        .click((function() {
                            var curr_index = gallery.length -1;
                            return function() {
                                return load_photo(curr_index);
                            }
                        })());
                    var img_src = dir_photos + result[i].id + "/" + result[i].thumbnail;
                    // append `img` to the `a` only when the image has been loaded, i.e. out of order
                    img_thumbnail(img_src, result[i].id, a);
                }
                if(result.length < total) {
                    no_more_photos = true;
                }
            }
        });
    };
})();

/**
 * Show the photo description on top of the big photo.
 */
function fade_in_description() {
    if($("#photo-description").html() == "") {
        // do not show an empty description
        $("#photo-description").css("visibility", "hidden");
        return;
    }
    $("#photo-description").css("visibility", "visible");
    $("#photo-description").css("opacity", 0);
    $("#photo-description").fadeTo(fade_photo_description, opacity_photo_description);
    $('#animated-description abbr[data-toggle="tooltip"]').tooltip({
        placement: "bottom",
        offset: "0,2px",
        container: "#animated-description",
        trigger: "hover",
        boundary: "body" // the tooltip is located outside its parent
    });
    return false;
}

/**
 * Manage the event related to the photo description on top of the big photo.
 * The description is displayed on mouseenter or on click if the picture
 * is a panoramic so that the user can scroll the picture without displaying
 * the overwhelming description.
 */
function trigger_description(evt) {
    if(typeof evt !== "undefined" && evt.relatedTarget === null) {
        return; // tooltip on mouseleave triggers a mouseenter which should be dismissed
    }
    
    if(photo_is_panorama) {
        $(this).one("click", fade_in_description);
    }
    else {
        fade_in_description();
    }
}

/**
 * Show/hide the photo description on top of the big photo on mouse over events.
 * Nothing happens if the description is empty.
 */
function create_photo_description_animation() {
    $("#animated-description")
    .mouseenter(trigger_description)
    .mouseleave(function() {
        $("#photo-description").css("visibility", "hidden");
    });
}

/**
 * Most people don't know how to bypass the right click, and most people don't
 * care about copyright. So the right click is disabled on all img elements.
 */
function disable_right_click() {
    if(!right_click_disabled_image) {
        return;
    }
    $("img").on("contextmenu", function() {
        return false;
    });
}

/**
 * Change the submit button. From the clickable paper plane to the unclickable
 * animated spinner if ``clickable`` is false, otherwise the other way: from the
 * unclickable spinner to the plane. By setting ``clickable`` to true, the button
 * looks immediatly like a paper plane but a delay can be set to keep the button
 * unclickable for ``delay`` ms. That avoids duplicated requests or spams. If
 * ``ref`` is undefined, all submit button of the page will change.
 * @param clickable {Boolean} - False to explain to the user to wait a while.
 * @param delay {Number} - Duration in ms before reset. Default: 0.
 * @param ref {String} - Reference to the form. Default: all.
 */
function refresh_submit_button(clickable, delay, ref) {
    if(typeof ref === "undefined") {
        ref = "body";
    }
    
    var submit_button = $(ref).find("button[type=submit]");
    submit_button.find("i").remove();
    var style = "";

    if(typeof delay === "undefined") {
        delay = 0;
    }

    if(clickable) {
        submit_button.delay(delay).queue(function() {
            $(this).removeAttr("disabled");
            $(this).dequeue();
        });
        style = "far fa-paper-plane";
    }
    else {
        submit_button.attr("disabled", "disabled");
        style = "fas fa-spinner fa-pulse";
    }

    style += ' fa-2x';
    var img_button = $('<i></i>');
    img_button.addClass(style);
    submit_button.append(img_button);
}

/**
 * Add a temporary alert message at the end of the ``form``.
 * @param result {String} - JSON string: '{"success":true/false,"info":"Details"}'
 * @param form {String} - Reference to the form, f.i. "#contact-form".
 * @param stay_on {Boolean} - True to keep the info visible, false to fadeout after a few seconds.
 */
function append_info(result, selector, stay_on) {
    if(typeof stay_on === "undefined") {
        stay_on = false;
    }
    var alert_type = (result.success) ? "alert-success" : "alert-danger";
    var popup = $('<div></div>')
        .addClass("alert " + alert_type)
        .attr('role', 'alert');
    popup.append($("<strong></strong>").text(result.info));
    if(!stay_on) {
        popup
        .delay(message_delay_before_fadein)
        .fadeOut(message_fadein_time, function() {
            $(this).remove();
        });
    }
    $(selector).append(popup);
}

/**
 * Manage custom error messages for each field of the login form.
 */
function init_login_form() {
    $("#login-form").submit(function(e) {
        if(this.checkValidity() === false) {
            e.preventDefault();
            e.stopPropagation();
            this.classList.add("was-validated");
        }
    });
}

/**
 * Event binder. Send the form when the submit button is clicked. "#contact-form"
 * must exists. Once clicked, the button won't be clickable for a while.
 */
function init_contact_form() {
    init_dropdown_subject();
    
    $("#contact-form").submit(function(e) {
        if(this.checkValidity() === false) {
            e.preventDefault();
            e.stopPropagation();
            this.classList.add("was-validated");
            return;
        }

        refresh_submit_button(false, message_delay_before_resend);
        $.ajax({
            url: url_contact,
            async: true,
            method: "POST",
            data: {
                name: $("#name").val(),
                email: $("#email").val(),
                subjects: ckeckboxes_to_list(),
                message: $("#message").val(),
                captcha: $("#captcha").val(),
                browser_time: new Date(),
                win_res: $(window).width() + "x" + $(window).height() + "px",
                newsletter_subscription: $("#newsletter-subscription").prop("checked") ? 1 : 0,
                privacy_policy: $("#privacy-policy").val()
            },
            dataType: "json",
            success: function(result) {
                if(result.success) {
                    $("#contact-form").css("display", "none");
                    append_info(result, "#show-after-success", true);
                }
                else {
                    append_info(result, "#contact-form");
                    refresh_submit_button(true, message_delay_before_resend);
                    reload_captcha(); // reset the outdated captcha
                    $("#captcha").val("");
                }
            }
        })
        e.preventDefault();
    });
}

/**
 * The feedback form may be used multiple time without reloading the page.
 * The message and the captcha are reset, the other fields are not changed.
 * The form should be reset even if used for the first time.
 * @see share_emotion()
 * @see like_this_book()
 */
function reset_feedback_form() {
    $(".checkbox-menu-subject input[type='checkbox']").prop("checked", false);
    $(".checkbox-menu-subject li").toggleClass("active", false);
    $(".checkbox-menu-subject input[type='checkbox']:first").prop("checked", true);
    $(".checkbox-menu-subject li:first").toggleClass("active", true);
    
    $("#message").val("");
    $("#hide-after-success").css("display", "block");
    $("#feedback-form").css("display", "block");
    $("#hiden-form-group").css("display", "none");
    $("#engage-more-group").css("display", $("#engage-more-decision").prop("checked") ? "block" : "none");
    $("#newsletter-subscription").prop("checked", false);
    $("#ask-subscription").css("display", "none");
    reload_captcha();
    $("#captcha").val("");
    refresh_submit_button(true, message_delay_before_resend, "#feedback-form");
    console.log("Feedback form is reset.");
}

/**
 * Get the list of the selected subjects.
 */
function ckeckboxes_to_list() {
    return $('.checkbox-menu-subject input:checked').map(function () {
        return this.name;
    }).get();
}

/**
 * Event binder. Hide/show part of the form and submit it. "#feedback-form"
 * must exists.
 */
function init_feedback_form() {
    $("#message").focus(function() {
        $("#hiden-form-group").css("display", "block");
    });
    
    $("#engage-more-decision").change(function() {
        $("#engage-more-group").css("display", $(this).prop("checked") ? "block" : "none");
    });
    
    $("#email").focus(function() {
        $("#ask-subscription").css("display", "block");
    });
    
    init_dropdown_subject();
    
    $("#feedback-form").submit(function(e) {
        if(this.checkValidity() === false) {
            e.preventDefault();
            e.stopPropagation();
            this.classList.add("was-validated");
            return;
        }

        refresh_submit_button(false, message_delay_before_resend, "#feedback-form");
        $.ajax({
            url: url_detailed_feedback,
            async: true,
            method: "POST",
            data: {
                name: $("#name").val(),
                email: $("#email").val(),
                subjects: ckeckboxes_to_list(),
                message: $("#message").val(),
                captcha: $("#captcha").val(),
                browser_time: new Date(),
                win_res: $(window).width() + "x" + $(window).height() + "px",
                newsletter_subscription: $("#newsletter-subscription").prop("checked") ? 1 : 0,
                privacy_policy: $("#privacy-policy").val()
            },
            dataType: "json",
            success: function(result) {
                if(result.success) {
                    $("#hide-after-success").css("display", "none");
                    append_info(result, "#show-after-success");
                }
                else {
                    append_info(result, "#feedback-form");
                    refresh_submit_button(true, message_delay_before_resend, "#feedback-form");
                    reload_captcha(); // reset the outdated captcha
                    $("#captcha").val("");
                }
            }
        })
        e.preventDefault();
    });
}

/**
 * Load another captcha.
 */
function reload_captcha() {
    if(!$("#captcha-passcode").length) {
        return false;
    }
    var date = new Date();
    $("#captcha-passcode").attr("src", "/captcha.png?" + date.getTime());
    return false;
}

/**
 * Load a captcha if the data-autoload attribute is defined in the img tag.
 */
function load_captcha() {
    if(!$("#captcha-passcode").length) {
        return false;
    }
    if($("#captcha-passcode").attr("data-autoload")) {
        reload_captcha("#captcha-passcode");
    }
}

/**
 * Return the height of a thumbnail (they are all the same size).
 * @return {Number} Image height in pixel.
 */
function get_thumbnail_height() {
    return $("#gallery a img").first().height() || predefined_thumbnail_height;
}

/**
 * Scroll one row of thumbnails down.
 */
function scroll_down() {
    $("html, body").animate({
        scrollTop: $(window).scrollTop() + get_thumbnail_height() + total_gap_photo
    }, {
        duration: 400
    });
    return false;
}

/**
 * Check if ``elem`` is visible on the screen. Check the position, not the style.
 * In other words, a hidden block in the middle of the screen is considered on
 * screen.
 * @param elem {Object} - Element.
 * @return {Boolean} True if on screen. Otherwise False.
 */
function is_on_screen(elem) {
    var docViewTop = $(window).scrollTop();
    var docViewBottom = docViewTop + $(window).height();
    var elemTop = $(elem).offset().top;
    var elemBottom = elemTop + $(elem).height();
    return (elemBottom <= docViewBottom) && (elemTop >= docViewTop);
}

/**
 * Replace title in img with a Bootstrap tooltip, displayed on the left side for
 * medium screen or on the bottom for smaller screen.
 * NOTICE: the placement does not change when the window is resized.
 * @see book_zoom_images()
 */
function book_tooltip() {
    $("#content-book p:not(.can-zoom-in)").tooltip({
        animation: true,
        container: "#content-book",
        placement: "bottom",
        trigger: "hover"
    });
    $("#content-book p.can-zoom-in").tooltip({
        animation: true,
        container: "#content-book",
        placement: "bottom",
        trigger: "manual" // triggered by book_zoom_images()
    });
    $("sup a").tooltip({
        animation: true,
        container: "#content-book",
        offset: "0,10px",
        placement: "top",
        trigger: "hover"
    });
}

/**
 * Button opacity when the user mouse over the map.
 */
function book_static_map_effects() {
    var el = ".above-static-map";
    $(".static-map")
    .hover(function() {
        $(this).find(el).css("opacity", 1);
    },
    function() {
        $(this).find(el).css("opacity", 0.7);
    })
    .find(el).css("opacity", 0.7);
}

/**
 * Zoom-in images in the book with the Jack Moore's MIT-licensed plugin.
 * https://github.com/jackmoore/zoom/
 */
function book_zoom_images() {
    $(".can-zoom-in")
    .css("cursor", "grab")
    .hover(function() {
        $(this).tooltip("show");
    },
    function() {
        $(this).tooltip("hide");
    })
    .zoom({
        on: "grab",
        onZoomIn: function() {
            $(this).css("cursor", "grabbing");
        },
        onZoomOut: function() {
            $(this).css("cursor", "grab");
        }
    });
}

/**
 * Open the copyright notice.
 */
function open_modal_copyright() {
    $("#modal-copyright").modal("show");
    return false;
}

/**
 * Open the privacy policy.
 */
function open_modal_privacy_policy() {
    $("#modal-privacy-policy").modal("show");
    return false;
}

/**
 * Setup the "Amazon Affiliate Links" modal and show it.
 */
function amazon_affiliate_links_selection() {
    var links = JSON.parse(this.dataset.amazonAffiliateLinks.replace(/'/g, '"'));
    var product_name = this.dataset.amazonProductName;
    console.log("Open 'Amazon Affiliate Links' modal for this product: " + product_name);
    $(".amazon-product-name").empty().append(product_name);
    $("#list-amazon-affiliate-links").empty();
    for(var i = 0; i < links.length; i++) {
        var link = links[i];
        var title = "See this product in " + link["website"] + " (Amazon in " + link["marketplace"] + ")";
        var a = $("<a></a>")
            .attr("href", link["link"])
            .attr("rel", "nofollow")
            .attr("title", title)
            .attr("target", "_blank")
            .addClass("flag-" + link["flagId"] + " animate-shadow")
            .tooltip({
                animation: true,
                placement: "bottom",
                container: "#modal-amazon-affiliate-links",
                trigger: "hover"
            });
        var li = $("<li></li>").append(a);
        $("#list-amazon-affiliate-links").append(li);
    }
    $("#modal-amazon-affiliate-links").modal("show");
    return false;
}

/**
 * Apply the visitor's decision. will be remembered for ``offset_months`` months.
 */
function cookie_policy_decision(decision) {
    var later_on = new Date();
    var curr_month = later_on.getUTCMonth();
    if(curr_month == 12 - offset_months) { // December to January
        later_on.setUTCFullYear(later_on.getUTCFullYear() + 1);
        later_on.setUTCMonth(offset_months - 1);
    }
    else {
        later_on.setUTCMonth(curr_month + offset_months);
    }
    console.log("Accept long-term cookies? " + decision);
    var cookie_settings = "; expires=" + later_on.toUTCString() + "; path=/";

    // do not show the toat anymore
    document.cookie = "cookies_toast=true" + cookie_settings;
    // remember the visitor's decision
    document.cookie = "cookies_forever=" + decision + cookie_settings;
}

/**
 * Manage the Cookie Policy Consent toast and Do Not Track settings.
 * The "Newsletter" toast is displayed (if included in the page by Jinja)
 * a few seconds after the cookie policy decision.
 */
function cookie_policy_consent() {
    var dnt = navigator.doNotTrack;
    if(dnt == "1" || dnt == "yes") {
        console.log("Do Not Track preference took into account.");
        cookie_policy_decision("false");
        show_subscribe_newsletter_toast();
    }
    else if(document.cookie.indexOf("cookies_toast=true") < 0) {
        $("#cookie-policy-consent").show();
        $("#cookie-policy-consent .toast").toast("show");
        $("#cookie-policy-consent button").click(function () {
            $("#cookie-policy-consent .toast").toast("hide");
            cookie_policy_decision(this.dataset.accept);
            show_subscribe_newsletter_toast();
        });
    }
    else {
        show_subscribe_newsletter_toast();
    }
}

/**
 * Capital the first letter of `word`.
 */
function cap_first_letter(word) {
    return word[0].toUpperCase() + word.substr(1);
}

/**
 * Show the "Newsletter" toast after a delay. Notice that the toast may
 * not be included in the page (Jinja condition).
 */
function show_subscribe_newsletter_toast() {
    window.setTimeout(function() {
        $("#subscribe-newsletter").show();
        $("#subscribe-newsletter .toast").toast("show");
    }, delay_popup_like_button_book);
}

/**
 * Handle the Newsletter toast form. The toast is displayed after the
 * cookie policy consent toast (if included in the page by Jinja).
 * @see cookie_policy_consent()
 */
function subscribe_newsletter() {
    $("#subscribe-newsletter form").submit(function(e) {
        if(this.checkValidity() === false) {
            e.preventDefault();
            e.stopPropagation();
            this.classList.add("was-validated");
            return;
        }

        refresh_submit_button(false, 0, "#subscribe-newsletter");
        $.ajax({
            url: url_subscribe_newsletter,
            async: true,
            method: "POST",
            data: {
                email: $("#email-newsletter").val()
            },
            dataType: "json",
            success: function(result) {
                if(result.success) {
                    $("#subscribe-newsletter form").css("display", "none");
                    append_info(result, "#subscribe-newsletter .info-newsletter", true);
                }
                else {
                    append_info(result, "#subscribe-newsletter .info-newsletter");
                    refresh_submit_button(false, 0, "#subscribe-newsletter");
                }
            }
        })
        e.preventDefault();
    });
}

/**
 * Add a visit entry with emotion when the visitor clicks on the "Like" button of the book.
 */
function like_this_book() {
    if($("#popup-like-book").length) {
        $("#popup-like-book .toast").toast("dispose");
    }
    $(this).css("visibility", "hidden");
    $(this).unbind("click");
    var emotion = "like";
    $.ajax({
        url: url_share_emotion_book,
        async: true,
        method: "POST",
        data: {book_id: this.dataset.bookId, emotion: emotion},
        dataType: "json",
        success: function(result) {
            if(result.success) {
                reset_feedback_form();
                $("#modal-feedback").modal();
                console.log("Emotion shared: " + emotion);
            }
        }
    });
    return false;
}

/**
 * Put this.href as url anchor.
 */
function url_anchor_to_this_id() {
    window.history.replaceState(window.location.pathname, "", window.location.pathname + $(this).attr("href"));
}

/**
 * Add a visit entry when the visitor clicks on the read/download button of the book.
 */
function open_this_book() {
    $(this).addClass("disabled");
    $(this).unbind("click");
    var emotion = "neutral";
    $.ajax({
        url: url_share_emotion_book,
        async: false,
        method: "POST",
        data: {book_id: this.dataset.bookId, emotion: emotion},
        dataType: "json",
        success: function(result) {
        }
    });
    return true;
}

/**
 * Event listener on the dropdown menu of the contact/feedback form.
 * https://stackoverflow.com/questions/25016848/bootstrap-putting-checkbox-in-a-dropdown
 */
function init_dropdown_subject() {
    $(".checkbox-menu-subject").on("change", "input[type='checkbox']", function() {
        $(this).closest("li").toggleClass("active", this.checked);
    });

    $(document).on('click', '.allow-focus', function (e) {
        e.stopPropagation();
    });
}

/**
 * Change the login form into a password reset form.
 */
function login_to_password_reset_form() {
    window.history.replaceState(window.location.pathname, "", url_password_reset);
    $(".hidden-for-password-reset").remove();
    $("#content-form")
    .find("h1")
    .text("Password Reset");
    $("#login-form")
    .attr("action", url_password_reset)
    .find("button[type=submit]")
    .attr("title", "Reset my password")
    .find("i")
    .removeClass("fa-unlock-alt")
    .addClass("fa-envelope-open-text");
}

/**
 * Show a popup to warn the visitor about a non-HTTPS website redirection.
 */
function alert_insecure_website() {
    $("#non-https-website").text(this.href.split("/",3).join("/"));
    $("#non-https-website-url").attr("href", this.href);
    $('#nonHttpsWarning').modal('show');
    return false;
}

/** Management of the table of content. */
class toc {
    /**
     * Initialiser.
     */
    constructor() {
        /** Current anchor on focus (section where the reader probably is). Unset after update. */
        this.id_on_focus = undefined;

        /** Used for scroll event throttling. */
        this.scroll_timeout = undefined;
        
        // move the section id into a created div that will become the anchor
        $("#content-book .section").prepend(function() {
            var id = $(this).attr("id");
            $(this).removeAttr("id");
            return $("<div></div>").attr("id", id).addClass("title-anchor");
        });
    }

    /**
     * Find out the visible anchor on the screen.
     * @see animate()
     * @param elem {Object} - An anchor.
     * @return {Boolean} False at the first visible anchor to stop looping.
     */
    get_elem(elem) {
        if(is_on_screen(elem)) {
            this.id_on_focus = elem.attr("id");
            return false; // stop looping through anchors
        }
        return true;
    }

    /**
     * Loop through all anchors and update the URL accordingly to the reading progress.
     */
    actual_animate() {
        if(typeof this.id_on_focus === "string") {
            window.history.replaceState(window.location.pathname, "", window.location.pathname + "#" + this.id_on_focus);
            this.id_on_focus = undefined;
        }
    }

    /**
     * Find the current anchor. The actual refresh is throttled with setTimeout()
     * in order to avoid a Safari security error which is:
     * "SecurityError: Attempt to use history.replaceState() more than 100 times per 30 seconds"
     * More info about the scroll event in the MDN doc:
     * https://developer.mozilla.org/en-US/docs/Web/API/Element/scroll_event
     */
    animate() {
        var my_toc = this;
        $("#content-book .title-anchor").each(function() {
            return my_toc.get_elem($(this));
        });
        if(typeof this.scroll_timeout !== "number") {
            this.actual_animate();
            this.scroll_timeout = window.setTimeout(function() {
                my_toc.actual_animate(); // move end
                my_toc.scroll_timeout = undefined;
            }, 400); // 400 ms is less than 100 times per 30 seconds
        }
    }
}

/**
 * When the window is resized: move the padding top accordingly to the new navbar
 * height and resize the big photo if needed.
 */
$(window).resize(function() {
    if($("#main").length) {
        adapt_amount_thumbnails_to_fetch();
        move_body();
        display_photo();
    }
    if($("#content-book").length) {
        book_tooltip();
    }
});

/**
 * When the user scrolls the web page: fetch new thumbnails one row in advance.
 * But not too often as detailed in the MDN web doc:
 * https://developer.mozilla.org/en-US/docs/Web/API/Element/scroll_event
 */
$(window).scroll(function() {
    let last_known_scroll_position = $(window).scrollTop();
    let scroll_timeout = undefined;
    if(!scroll_ticking) {
        window.requestAnimationFrame(function() {
            if($("#main").length) {
                $("#onclick-scroll-down").show();
                if((last_known_scroll_position + $(window).height() + get_thumbnail_height()) >= $(document).height()) {
                    if(!no_more_photos) {
                        fetch_thumbnails(total_new_photos);
                    }
                    else {
                        $("#onclick-scroll-down").hide();
                    }
                }
            }

            if($("#content-book").length) {
                toc.animate();
            }

            scroll_ticking = false;
        });
        scroll_ticking = true;
    }
});

/**
 * When the user presses the Next/Prev (arrow) key on his keyboard: do as if he
 * has just clicked on the next/prev button.
 * @see prev_next_buttons_onclick()
 * @param e {Object} - Event.
 */
$(window).keydown(function(e) {
    if(!$("#main").length) {
        return;
    }
    if(main_is_active()) {
        return;
    }

    // Next (arrow) key pressed
    if(e.which == 39 && (last_loaded_photo + 1) < gallery.length) {
        disable_autoplay();
        prev_next_buttons_onclick(last_loaded_photo +1);
    }
    // Previous (arrow) key pressed
    else if(e.which == 37 && last_loaded_photo > 0) {
        disable_autoplay();
        prev_next_buttons_onclick(last_loaded_photo -1);
    }
});

/**
 * When the DOM is loaded and ready to be manipulated:
 *
 * * Fetch the first thumbnails and photos metadata.
 * * Initialise the interface.
 *
 */
$(function() {
    var csrf_token = $("meta[name=csrf-token]").attr("content");
    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", csrf_token);
            }
        }
    });
    
    // https://stackoverflow.com/questions/36460538/scrolling-issues-with-multiple-bootstrap-modals
    $("body").on("hidden.bs.modal", function (e) { 
        if ($('.modal:visible').length) { 
            $('body').addClass('modal-open');
        }
    });

    if($("#main").length) { // main page
        move_body();
        adapt_amount_thumbnails_to_fetch();
        fetch_thumbnails(total_new_photos);
        create_photo_description_animation();
        disable_right_click();
    }
    if($("#contact-form").length) { // contact page
        init_contact_form();
    }
    $('.tooltip-networks[data-toggle="tooltip"]').tooltip({
        offset: "0,3px",
        placement: "bottom",
        trigger: "hover"
    });
    $('.tooltip-support[data-toggle="tooltip"]').tooltip({
        offset: "0,3px",
        placement: "bottom",
        html: true,
        trigger: "hover"
    });
    $('.carbon-tooltip').tooltip({
        offset: "left: 5px",
        placement: "right",
        html: true,
        trigger: "hover"
    });

    load_captcha();
    
    if($("#content-book").length) { // story page
        if(right_click_disabled_text) {
            $("#content-book").bind("selectstart dragstart", function(e) {
                e.preventDefault();
                return false;
            });
            $("#content-book").css("cursor", "default"); // the user cannot select text
        }
        toc = new toc();
        if($("#visible-when-loaded").attr("data-add-visit") == "True") {
            $.ajax({
                url: url_share_emotion_book,
                async: true,
                method: "POST",
                data: {book_id: $("#visible-when-loaded").attr("data-book-id"), emotion: "neutral"},
                dataType: "json",
                success: function(result) {
                }
            });
        }
        $("#wait-before-visible").hide();
        $("#visible-when-loaded").show();
        book_tooltip();
        book_zoom_images();
        book_static_map_effects();
        
        // scroll down if an anchor is defined, it isn't automatic because the content has been dynamically loaded
        if(location.hash && $(location.hash).length) {
            $([document.documentElement, document.body]).scrollTop($(location.hash).offset().top);
        }
    }
    
    if($("#popup-like-book").length) {
        window.setTimeout(function() {
            $("#popup-like-book").show();
            $("#popup-like-book .toast").toast("show");
        }, delay_popup_like_button_book);
    }
    
    if($("#login-form").length) { // login page
        init_login_form();
    }
    
    if($("#feedback-form").length) { // feedback modal
        init_feedback_form();
    }

    // xs screen is a smartphone with no useful onmouseover to display a tooltip
    if (window.matchMedia("(min-width: 768px)").matches) {
        $('#header [data-toggle="tooltip"], #subNavbarNav [data-toggle="tooltip"]').tooltip({
            animation: true,
            placement: "bottom",
            delay: { "show": 100, "hide": 0 },
            container: "#header",
            trigger: "hover"
        });
        $('#full-screen [data-toggle="tooltip"], #subNavbarNav [data-toggle="tooltip"]').tooltip({
            animation: true,
            placement: "left",
            delay: { "show": 100, "hide": 0 },
            trigger: "hover"
        });
    }
    
    $('.tweetable a[data-toggle="tooltip"]').tooltip({
        animation: true,
        placement: "right",
        trigger: "hover"
    });
    
    $('.crowdfunding-progress[data-toggle="tooltip"]').tooltip({
        animation: true,
        placement: "right",
        html: true,
        trigger: "hover"
    });
    
    $('.card-text a.dropdown-item[data-toggle="tooltip"]').tooltip({
        animation: true,
        placement: "right",
        trigger: "hover"
    });

    $('.card-text a.btn[data-toggle="tooltip"]').tooltip({
        animation: true,
        offset: "top: 5px",
        placement: "bottom",
        trigger: "hover"
    });
    
    $('.tweetable-button').each(function() {
        // by button event to not propagate the change to other buttons
        $(this).click(function() {
            var url = encodeURIComponent(window.location.href);
            $(this).attr("href", $(this).attr("href")
                .replace("url=%23", "url=" + url)
                .replace("+-+%23", "+-+" + url));
            return true;
        });
    });

    $("#onclick-close-large-photo").click(close_large_photo);
    $("#onclick-reload-captcha").click(reload_captcha);
    $(".onclick-open-modal-copyright").click(open_modal_copyright);
    $(".onclick-open-modal-privacy-policy").click(open_modal_privacy_policy);
    $("#onclick-scroll-down").click(scroll_down);
    $("#onclick-close-photo").click(close_photo);
    $(".onclick-like-this-book").click(like_this_book);
    $(".onclick-open-this-book").click(open_this_book);
    $('#pills-tab li.nav-item a[data-toggle="pill"]').click(url_anchor_to_this_id);
    $("#onclick-password-reset").click(login_to_password_reset_form);
    $('body').on('click', 'a.amazon-affiliate-link', amazon_affiliate_links_selection); // also apply to dynamically added elements
    cookie_policy_consent();
    subscribe_newsletter();
    
    $('body').on('click', 'a[href^="http://"]:not(\'.bypass-non-https-warning\')', alert_insecure_website);
    
    // blur up
    $("img.hidden-card")
    .on("load", function(event) {
        $(this).removeClass("hidden-card");
        $(this).siblings(".preview-card").addClass("hidden-card");
    })
    .attr("src", function() {
        return $(this).attr("data-src");
    }); // set the attribute after the event listener
});
