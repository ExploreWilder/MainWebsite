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
 * Small devices (landscape phones) width as defined by Bootstrap.
 * Default value is 350 px.
 */
const small_devices_height = 350;

/**
 * Gap in pixels around photos/thumbnails, twice the padding around a thumbnail.
 * Default value is 20 px.
 */
const total_gap_photo = 20;

/**
 * Remember the visitor's decision to accept or deny long-term cookies for a few months.
 * Default value is 3 months.
 */
const offset_months = 3;

/**
 * Duration in ms of the fade out effect when the user clicks on a thumbnail.
 * Default value is 250 ms.
 */
const fade_out_thumbnail = 250;

/**
 * Opacity [0-1] of active thumbnails waiting for the big photo to be displayed.
 * Default value is 0.5.
 */
const opacity_thumbnail = 0.5;

/**
 * Duration in ms of the fade in effect when the progress bar becomes active.
 * Default value is 1000 ms.
 */
const fade_in_download_in_progress = 1000;

/**
 * Duration in ms of the fade in/out effect of the description over the photo.
 * Default value is 300 ms.
 */
const fade_photo_description = 300;

/**
 * Opacity [0-1] of the description displayed over the photo.
 * Default value is 0.8.
 */
const opacity_photo_description = 0.8;

/**
 * The maximum number of column in the gallery.
 * Default value is 3.
 */
const max_column_photos = 3;

/**
 * Number of photos to fetch in a single asynchronous request. Must be > 1.
 * Default value is 9.
 */
const default_total_new_photos = 3 * max_column_photos;

/**
 * URL to which the request for information about the thumbnails/photos is sent.
 * Default value is "/photos", according to `flaskr.visitor_space`.
 */
const url_fetch_photos = "/photos";

/**
 * URL to which the message sent through the contact form is processed.
 * Default value is "/contact", according to `flaskr.visitor_space`.
 */
const url_contact = "/contact";

/**
 * URL to which the password reset would be done.
 * Default value is "/reset_password", according to `flaskr.visitor_space`.
 */
const url_password_reset = "/reset_password";

/**
 * URL to which the message sent through the feedback form is processed.
 * Default value is "/detailed_feedback", according to `flaskr.visitor_space`.
 */
const url_detailed_feedback = "/detailed_feedback";

/**
 * Delay before to display the popup asking "Like" in the story.
 * The same delay is applied to the Newsletter toast.
 * Default value is 1 min.
 */
const delay_popup_like_button_book = 60 * 1000;

/**
 * Delay before a popup message starts to fade in.
 * Default value is 3000 ms.
 */
const message_delay_before_fadein = 3000;

/**
 * Duration of the fade in animation of popup messages.
 * Default value is 1000 ms.
 */
const message_fadein_time = 1000;

/**
 * Delay before the user can send an other request from the same form.
 * Default value is 15000 ms. Double check on the server side as well.
 */
const message_delay_before_resend = 15000;

/**
 * URL to which all photos are located. Last '/' required.
 * Default value is "/photos/", according to `flaskr.__init__`, not the real path.
 */
const dir_photos = "/photos/";

/**
 * URL to which the captcha passcode is generated.
 * Default value is "captcha.png", according to `flaskr.visitor_space`.
 */
const url_captcha = "captcha.png";

/**
 * URL to which the visit is logged.
 * Default value is "/log_visit_photo" according to `flaskr.visitor_space`.
 */
const url_log_visit_photo = "/log_visit_photo";

/**
 * List of emotions accordingly to the buttons next to the big photo.
 * Default value is ["love"].
 */
const emotions = ["love"];

/**
 * URL to which the emotion will be processed for the photo.
 * Default value is "/share_emotion_photo" according to `flaskr.visitor_space`.
 */
const url_share_emotion_photo = "/share_emotion_photo";

/**
 * URL to which the emotion will be processed for the book.
 * Default value is "/share_emotion_book" according to `flaskr.visitor_space`.
 */
const url_share_emotion_book = "/share_emotion_book";

/**
 * URL to which the visitor will be added to the newsletter members list.
 * Default value is "/subscribe_newsletter" according to `flaskr.visitor_space`.
 */
const url_subscribe_newsletter = "/subscribe";

/**
 * Maximum width/height in pixel of the medium photo displayed in the interface.
 * Default value is [1366, 768].
 */
const m_size = [1366, 768];

/**
 * Maximum width/height in pixel of the large photo displayed in the interface.
 * Default value is [2560, 1440].
 */
const l_size = [2560, 1440];

/**
 * True to disable right click on images. False to setup as default.
 * Default value is true, right click enabled.
 */
const right_click_disabled_image = true;

/**
 * True to disable right click on copyrighted text. False to setup as default.
 * Default value is false, right click disabled.
 */
const right_click_disabled_text = false;

/**
 * The thumbnail height defined before it is dynamically guessed with get_thumbnail_height().
 * Default value is 300 px if the screen width > 768 px, otherwise 150 px.
 */
const predefined_thumbnail_height = ($(window).width() > 768) ? 300 : 150;

/**
 * The interval of time before displaying the next photo (if autoplay is enabled).
 * If you change this value, change the CSS one as well (animation-duration).
 * Default value is 5000 ms.
 */
const autoplay_interval = 5000;
