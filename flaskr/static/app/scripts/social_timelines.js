/*!
 * Copyright 2020 Clement
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
 * Generic class formatting a JSON timeline to display a social feed asynchronously.
 * The goal is to have the same look and feel for all social feeds and well integrated
 * in the website. However, some methods have to be overriden to fit with the
 * specific timeline.
 */
class Timeline {
    /** The social network name in small cap, f.i. "mastodon" */
    social_network;

    /** The media directory path. */
    data_store;

    /** Maximum number of publications to display. */
    max_entries;

    /**
     * Initialize the class attribute and create an AJAX request that would create the timeline on success.
     * 
     * @param social_network {String} - The social network name in small cap, f.i. "mastodon"
     * @param url_stored_timeline {String} - The URL to the JSON file.
     * @param data_store {String} - The media directory path.
     * @param el {Object} - Parent block of the timeline.
     * @param max_entries {Number} - Maximum number of publications to display.
     * @param media_fadein_time {Number} - Time in ms of the fade-in effect on media load.
     */
    constructor(social_network, url_stored_timeline, data_store, el, max_entries = 10, media_fadein_time = 300) {
        this.social_network = social_network;
        this.data_store = data_store;
        this.max_entries = max_entries;
        this.media_fadein_time = media_fadein_time;

        $.ajax({
            url: url_stored_timeline,
            method: "POST",
            async: true,
            dataType: "json",
            success: (result) => {
                this.create_timeline(result, el);
            }
        });
    }

    /**
     * Virtual method to override. That should return a string of the external publication URL.
     */
    publication_url(publication_data) {
        throw new Error('You have to implement the method');
    }

    /**
     * Virtual method to override. That should return a string of the action (tweet, retweet, toot, etc.) and author.
     */
    publication_info(publication_data) {
        throw new Error('You have to implement the method');
    }

    /**
     * Only one profile is displayed in the publication, it could be either me, or the original author.
     * 
     * @param publication_data {Object} - Dictionary containing a single publication.
     * @return {Object} A dictionary containing the profile to display.
     */
    get_profile(publication_data) {
        return {};
    }

    /**
     * Create the entire timeline and show the '.discover-more' element which is
     * a link located at the bottom of the timeline pointing to my profile in
     * the social platform.
     * 
     * @param result {Object} - JSON formated timeline.
     * @param el {Object} - Parent block of the timeline.
     */
    create_timeline(result, el) {
        var timeline = $('<ul></ul>').addClass("list-unstyled");
        var limit = this.max_entries;

        for(var publication_data of result) {
            if(limit-- < 1) {
                break;
            }
            timeline.append(this.create_publication(
                publication_data,
                this.get_profile(publication_data)
            ));
        }

        el.prepend(timeline).find(".discover-more").show();
    }

    /**
     * Create a block containing images. It's just 'img' tags inside a 'div' block.
     * 
     * @param images {Array} - A list of images. An image is a dictionary containing at least 'url'.
     * @return {Object} The jQuery object of the gallery.
     */
    create_gallery(images) {
        var gallery = $('<div></div>').addClass("images");

        for(image_data of images) {
            image = new Image();
            $(image)
            .addClass("rounded-lg")
            .hide()
            .appendTo(gallery)
            .on("load", function() {
                $(this).hide().fadeIn(this.media_fadein_time);
            });
            image.src = `${this.data_store}${image_data.origin}/${image_data.filename}`;
        }

        return gallery;
    }

    /**
     * Create the profile image.
     * 
     * @param profile {Object} - A dictionary containing the profile.
     * @return {Object} The jQuery object of image.
     */
    create_profile_image(profile) {
        var profile_image = new Image();

        $(profile_image).addClass("rounded-lg").hide().on("load", function() {
            $(this).hide().fadeIn(this.media_fadein_time);
        });
        profile_image.src = `${this.data_store}${profile.profile_image_origin}/${profile.profile_image_filename}`;

        return $(profile_image);
    }

    /**
     * Find out the number of days between now and `old_time`. The value is ceiled.
     * 
     * @param old_time {String} - Publication date, f.i. 'Thu, 30 Jul 2020 17:59:32 +0000'
     * @return {String} The number of days plus 'days ago' or just 'yesterday' or 'today'.
     */
    days_ago(old_time) {
        const one_day_ms = 1000 * 60 * 60 * 24;
        const delta_days = Math.ceil((Date.now() - Date.parse(old_time)) / one_day_ms);

        if(delta_days == 1) {
            return "today";
        }
        else if(delta_days == 2) {
            return "yesterday";
        }
        else {
            return delta_days + " days ago";
        }
    }

    /**
     * Create a publication to be added to the timeline. This method does not have
     * to be overriden since the publication style and JSON format should be the
     * same for all feeds.
     * 
     * @param publication_data {Object} - Dictionary containing a single publication.
     * @param profile {Object} - A dictionary containing the profile.
     * @return {Object} The jQuery object of the publication.
     */
    create_publication(publication_data, profile) {
        var publication_a = $('<a></a>')
        .addClass("media rounded-lg p-2 animate-shadow")
        .attr({
            "href": this.publication_url(publication_data),
            "target": "_blank",
            "title": "See on " + cap_first_letter(this.social_network)
        });

        if("profile_image_filename" in profile) {
            publication_a.append(this.create_profile_image(profile));
        }

        var media_body = $('<div></div>').addClass("media-body");

        // publication content:
        $('<h5></h5>')
        .text(publication_data.text)
        .appendTo(media_body);

        // publication information (author, date):
        $('<span></span>')
        .addClass("text-muted publication-info")
        .text(this.publication_info(publication_data) + ", " + this.days_ago(publication_data.created_at))
        .appendTo(media_body);

        if("images" in publication_data) {
            media_body.append(this.create_gallery(publication_data.images));
        }

        publication_a.append(media_body);
        return $('<li></li>').append(publication_a);
    }
}

 /**
  * Display the Twitter timeline.
  */
class TwitterTimeline extends Timeline {
    /** Timeline configuration. */
    constructor() {
        super(
            "twitter",
            url_my_twitter_timeline,
            url_twitter_media,
            $("#my-twitter-timeline")
        );
    }

    /** Returns true for retweet, false for tweet. */
    is_retweet(tweet_data) {
        return "retweeted_status" in tweet_data;
    }

    /** Returns my profile if it's a tweet, or the original profile if it's a retweet. */
    get_profile(tweet_data) {
        if(this.is_retweet(tweet_data)) {
            return tweet_data.retweeted_status.user;
        }
        else {
            return tweet_data.user;
        }
    }

    /** URL to the Twitter status. */
    publication_url(tweet_data) {
        return `https://twitter.com/${tweet_data.user.screen_name}/status/${tweet_data.id_str}`;
    }

    /** Returns 'Retweeted from {original source}' or ' Tweeted by {me}' */
    publication_info(tweet_data) {
        var is_retweet = this.is_retweet(tweet_data);
        var profile_name = this.get_profile(tweet_data).name;
        return ((is_retweet) ? "Retweeted from " : "Tweeted by ") + profile_name;
    }
}

/**
 * Display the Mastodon timeline.
 */
class MastodonTimeline extends Timeline {
    /** Timeline configuration. */
    constructor() {
        super(
            "mastodon",
            url_my_mastodon_timeline,
            url_mastodon_media,
            $("#my-mastodon-timeline")
        );
    }

    /** Returns the Mastodon link to the toot. */
    publication_url(toot_data) {
        return toot_data.guid;
    }

    /** Returns 'Tooted by {me}' */
    publication_info(toot_data) {
        return `Tooted by ${mastodon_name}`;
    }
}

$(function() {
    // check if the timeline block exist before the JS initialization which will make an AJAX request
    if($("#my-twitter-timeline").length) {
        twitter_timeline = new TwitterTimeline();
    }
    if($("#my-mastodon-timeline").length) {
        mastodon_timeline = new MastodonTimeline();
    }
});
