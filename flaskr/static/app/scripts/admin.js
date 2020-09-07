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

/** URL prefix of the Blueprint registration. */
var url_prefix = "/admin";

/** URL to which the submitted new photo and its information are processed. */
var url_add_photo = url_prefix + "/photos/add/request";

/** URL to which the submitted new book and its information are processed. */
var url_add_book = url_prefix + "/books/add/request";

/** URL to which the submitted change of access level is processed. */
var url_change_access_level = url_prefix + "/members/change_access_level";

/** URL to which the desired member is revoked. */
var url_revoke_member = url_prefix + "/members/revoke";

/** URL to which the desired member is deleted. */
var url_delete_member = url_prefix + "/members/delete";

/** URL to which the new title and description about a photo are processed. */
var url_save_photo_metadata = url_prefix + "/photos/metadata";

/** URL to which the updated book metadata are processed. */
var url_save_book_metadata = url_prefix + "/books/metadata";

/** URL to which the desired photo is deleted, including its metadata. */
var url_delete = url_prefix + "/photos/delete";

/** URL to which the desired book is deleted, including its metadata. */
var url_delete_book = url_prefix + "/books/delete";

/** URL to which the dragged and dropped photo is moved in the database. */
var url_move_photo = url_prefix + "/photos/move";

/** URL to which the dragged and dropped book is moved in the database. */
var url_move_book = url_prefix + "/books/move";

/** URL to which the email will be created and sent to create a password. */
var url_send_password_creation = url_prefix + "/members/send_password_creation";

/** URL to which the file is actually moved. */
var url_move_photo_to_wastebasket = url_prefix + "/photos/move_into_wastebasket";

/** URL to which the newsletter will be sent. */
var url_send_newsletter = url_prefix + "/members/send_newsletter";

/**
 * Read the @p input file for the photo preview. Supported extensions are:
 * tiff, tif, jpg, peg, png
 * Inspired by: https://rfvallina.com/blog/2015/08/22/preview-tiff-and-pdf-files-using-html5-file-api.html
 * Dependencies: FileReader and https://github.com/seikichi/tiff.js/tree/master
 * @param input {Object} - Input field of file type.
 */
var read_upload_photo = function(input) {
    var tgt = input.target || window.event.srcElement;
    var files = tgt.files;

    if (FileReader && files && files.length) {
        var fr = new FileReader();
        var file_types_tif = ['tiff', 'tif'];
        var file_types_web = ['jpg', 'jpeg', 'png'];
        var extension = files[0].name.split('.').pop().toLowerCase();
        var file_size = files[0].size;
        var max_file_size = 200 * 1024 * 1024; // 200 MiB
        var read_as;
        
        if(file_size > max_file_size) {
            console.log("Warning: file is considered too big to be managed on the client-side.");
            return;
        }
        
        if(file_types_tif.indexOf(extension) > -1) {
            fr.readAsArrayBuffer(files[0]);
            read_as = "tif";
        }
        else if(file_types_web.indexOf(extension) > -1) {
            fr.readAsDataURL(files[0]);
            read_as = "web";
        }
        
        fr.onload = function(e) {            
            if (read_as == "tif") {
                console.debug("Parsing TIFF image...");
                Tiff.initialize({
                    TOTAL_MEMORY: max_file_size
                });
                var tiff = new Tiff({
                    buffer: e.target.result
                });
                var tiffCanvas = tiff.toCanvas();
                $(tiffCanvas).addClass("preview");
                $("#photo-preview").empty().append(tiffCanvas);
            }
            if (read_as == "web") {
                $("#photo-preview").empty().append('<img src="' + e.target.result + '" class="preview"/>');
            }
        }
        fr.onloadend = function(e) {
            console.debug("Load End");
        }
    }
};

/**
 * Update the filename in the input field.
 * @param input {Object} - Input field of file type.
 */
var update_filename = function(input) {
    var full_path = input.value;
    
    if(full_path) {
        var start_index = (full_path.indexOf('\\') >= 0 ? full_path.lastIndexOf('\\') : full_path.lastIndexOf('/'));
        var filename = full_path.substring(start_index);
        
        if (filename.indexOf('\\') === 0 || filename.indexOf('/') === 0) {
            filename = filename.substring(1);
        }
        
        $("label[for*='add-photo-file']").text(filename);
    }
};

/**
 * Update the modal window used to change the access level of any member listed in the table.
 */
var update_modal_change_access_level = function() {
    var td = $(this).parents("td");
    var username = td.prevAll(".username").text();
    var email = td.prevAll(".email").text();
    var access_level = parseInt($(this).text().trim());
    var member_id = parseInt(this.dataset.memberId);

    $("#modal-username").text((username == "") ? "?" : username);
    $("#modal-email").text((email == "") ? "?" : email);
    $("#modal-member-id").val(member_id);
    $("#change-member-access-level").val(access_level);
    refresh_access();
    $("#modal-change-access-level").modal("show");
    return false;
};

/**
 * Save the change on the access level of the selected member.
 */
var save_access_level = function() {
    var new_access_level = $("#change-member-access-level").val() || 0;
    var member_id = $("#modal-member-id").val() || 0;
    $.ajax({
        url: url_change_access_level,
        async: true,
        type: "POST",
        data: {
            member_id: member_id,
            new_access_level: new_access_level
        },
        dataType: "json",
        success: function(result) {
            var a = $("#members-list .access-level a[data-member-id='" + member_id + "']");
            a.text(new_access_level);
            if(new_access_level == 0) {
                $("#members-list .td-action a.onclick-admin-revoke-member[data-member-id='" + member_id + "']")
                .remove();
            }
            else if(new_access_level == 255) { // remove link
                var parent = a.parents("td");
                a.remove();
                parent.text(new_access_level);
            }
            alert(((result.success) ? "SUCCESS" : "ERROR") + ": " + result.info);
            $("#modal-change-access-level").modal("hide");
        }
    });
};

/**
 * Send an e-mail to the member and update the interface.
 */
var admin_send_password_creation = function() {
    var a = this;
    $.ajax({
        url: url_send_password_creation,
        async: true,
        type: "POST",
        data: {member_id: a.dataset.memberId},
        dataType: "json",
        success: function(result) {
            $(a).remove();
            alert(((result.success) ? "SUCCESS" : "ERROR") + ": " + result.info);
        }
    });
    return false;
};

/**
 * Connect the submit button of "#admin-add-member" form so that a new member is
 * added. The "#members-list" list is updated. The new member would be at the top.
 */
var init_admin_members = function() {
    if($("#members-list").length == 0) {
        return;
    }

    $("#change-member-access-level")
    .on("propertychange input", refresh_access);

    $(".onclick-admin-send-password-creation")
    .click(admin_send_password_creation);

    $(".onclick-admin-revoke-member")
    .click(admin_revoke_member);

    $(".onclick-admin-delete-member")
    .click(admin_delete_member);

    $("#members-list .access-level a")
    .click(update_modal_change_access_level);

    $("#save-changes")
    .click(save_access_level);
    
    init_newsletter_form();
};

/**
 * Update the progress bar @p el with the @p value in percent and the @p text.
 * @see init_admin_add_photo()
 * @param el {Object} - Bootstrap progress-bar.
 * @param value {Number} - Percent between 0 and 100.
 * @param text {String} - Text displayed in the progress bar.
 */
var update_progress_bar = function(el, value, text) {
    el.width(value.toString() + "%");
    el.attr("aria-valuenow", value);
    el.text(text);
};

/**
 * Update the progress bar. To be used as xhr in the JQuery ajax context.
 * @see init_admin_add_photo()
 */
var xhr_progress_bar = function() {
    var xhr = new window.XMLHttpRequest();
    update_progress_bar($("#photo-progress").show(), 0, "Uploading...");

    xhr.upload.addEventListener("progress", function(evt) {
        if(evt.lengthComputable) {
            var percent_complete = evt.loaded / evt.total;
            percent_complete = parseInt(percent_complete * 100);
            update_progress_bar($("#photo-progress"), percent_complete, "Uploading...");

            if (percent_complete === 100) {
                update_progress_bar($("#photo-progress"), 100, "Processing...");
            }
        }
    }, false);
    return xhr;
};

/**
 * Add a code in the text area.
 * @param input Text area.
 * @param start Text to add before the selection or the cursor.
 * @param end Text to add after the selection or the cursor.
 */
var md_short_tag = function(input, start, end) {
    input.focus();

    // Internet Explorer
    if(typeof document.selection != "undefined") {
        var range = document.selection.createRange();
        var inbetween_text = range.text;
        range.text = start + inbetween_text + end;
        range = document.selection.createRange();

        if (inbetween_text.length == 0) {
            range.move("character", -end.length);
        }
        else {
            range.moveStart("character", start.length + inbetween_text.length + end.length);
        }

        range.select();
    }

    // most other browsers
    else if(typeof input.selectionStart != "undefined") {
        var start_selection = input.selectionStart;
        var end_selection = input.selectionEnd;
        var pos;
        var inbetween_text = input.value.substring(start_selection, end_selection);

        input.value = input.value.substr(0, start_selection)
                      + start + inbetween_text + end
                      + input.value.substr(end_selection);

        if(inbetween_text.length == 0) {
            pos = start_selection + start.length;
        }
        else {
            pos = start_selection + start.length + inbetween_text.length + end.length;
        }

        input.selectionStart = pos;
        input.selectionEnd = pos;
    }
};

/**
 * Add a complex code in the text area.
 * @param input Text area.
 * @param start Text to add before the selection or the cursor.
 * @param middle Text to add between the two attributes.
 * @param end Text to add after the selection or the cursor.
 * @param prompt_value Message to show in order to get the first attribute.
 * @param prompt_text Message to show in order to get the second attribute.
 */
var md_long_tag = function(input, start, middle, end, prompt_value, prompt_text) {
    input.focus();
    var value = prompt(prompt_value);
    var text = prompt(prompt_text);

    if (value == "") {
        value = "null";
    }
    if (text == "") {
        text = "null";
    }

    if(typeof document.selection != "undefined") {
        var range = document.selection.createRange();
        var inbetween_text = range.text;
        range.text = inbetween_text + start + value + middle + text + end;
        range = document.selection.createRange();

        if (inbetween_text.length == 0) {
            range.move("character", -end.length);
        }
        else {
            range.moveStart("character", inbetween_text.length + start.length
                                         + value.length + middle.length
                                         + text.length + end.length);
        }
        range.select();
    }
    else if(typeof input.selectionStart != "undefined") {
        var start_selection = input.selectionStart;
        var end_selection = input.selectionEnd;
        var inbetween_text = input.value.substring(start_selection, end_selection);

        input.value = input.value.substr(0, start_selection)
                      + inbetween_text + start + text + middle + value + end
                      + input.value.substr(end_selection);

        var pos = start_selection + inbetween_text.length + start.length
                  + value.length+ middle.length + text.length + end.length;

        input.selectionStart = pos;
        input.selectionEnd = pos;
    }
}

/**
 * Generate markdown.
 */
var update_newsletter_preview = function() {
    var text = "Hello!\n\n" + $("#news").val() + "\n\nCheers,  \nClement";
    $("#preview").html(marked(text));
};

/**
 * Event binder. Send the form when the submit button is clicked. "#newsletter-form"
 * must exists. Once clicked, the button won't be clickable for a while.
 */
var init_newsletter_form = function() {
    $("#news").on("change keyup paste", update_newsletter_preview);
    
    $(".md-format-button").click(function() {
        if(this.dataset.mdType == "short") {
            md_short_tag(document.getElementById("news"),
                         this.dataset.mdStart,
                         this.dataset.mdEnd);
        }
        else {
            md_long_tag(document.getElementById("news"),
                        this.dataset.mdStart,
                        this.dataset.mdMiddle,
                        this.dataset.mdEnd,
                        this.dataset.mdPromptValue,
                        this.dataset.mdPromptText);
        }
        update_newsletter_preview();
    });
    
    $("#newsletter-form").submit(function(e) {
        if(this.checkValidity() === false) {
            e.preventDefault();
            e.stopPropagation();
            this.classList.add("was-validated");
            return;
        }
        $("#newsletter-form input").attr("readonly", "readonly");
        $("#newsletter-form textarea").attr("readonly", "readonly");
        $("#newsletter-form button").remove();

        $.ajax({
            url: url_send_newsletter,
            async: true,
            method: "POST",
            data: {
                subject: $("#subject").val(),
                news: $("#news").val()
            },
            dataType: "json",
            success: function(result) {
                append_info(result, "#newsletter-form");
            }
        })
        e.preventDefault();
    });
};

/**
 * Define the event when the "#admin-add" form is submitted. A temporary popup
 * message is displayed at the XHR response.
 */
var init_admin_add_photo = function() {
    if($("#admin-add").length == 0) {
        return;
    }
    $("#admin-add").submit(function(e) {
        refresh_submit_button(false, 0, "#admin-add");
        $.ajax({
            xhr: xhr_progress_bar,
            url: url_add_photo,
            async: true,
            method: "POST",
            data: new FormData(this),
            processData: false, // required when transferring FormData
            contentType: false, // required when transferring FormData
            dataType: "json",
            success: function(result) {
                append_info(result, "#admin-add");
                refresh_submit_button(true, 0, "#admin-add");
                update_progress_bar($("#photo-progress").hide(), 0, "Uploading...");
            }
        });
        e.preventDefault();
    });
    $("#add-photo-file").change(function() {
        update_filename(this);
        read_upload_photo(this);
    });
};

/**
 * Define the event when the "#admin-add-book" form is submitted. A temporary popup
 * message is displayed at the XHR response.
 */
var init_admin_add_book = function() {
    if($("#admin-add-book").length == 0) {
        return;
    }
    $("#admin-add-book").submit(function(e) {
        refresh_submit_button(false, 0, "#admin-add-book");
        $.ajax({
            url: url_add_book,
            async: true,
            method: "POST",
            data: new FormData(this),
            processData: false, // required when transferring FormData
            contentType: false, // required when transferring FormData
            dataType: "json",
            success: function(result) {
                append_info(result, "#admin-add-book");
                refresh_submit_button(true, 0, "#admin-add-book");
            }
        });
        e.preventDefault();
    });
};

/**
 * Update the interface and the database if the member can be revoked.
 */
var admin_revoke_member = function() {
    var a = this;
    $.ajax({
        url: url_revoke_member,
        async: true,
        type: "POST",
        data: {member_id: a.dataset.memberId},
        dataType: "json",
        success: function(result) {
            $(a).parents("td").prevAll(".access-level").find("a").text("0");
            $(a).remove();
            alert(((result.success) ? "SUCCESS" : "ERROR") + ": " + result.info);
        }
    });
    return false;
};

/**
 * Update the interface and the database if the member can be deleted.
 */
var admin_delete_member = function() {
    var a = this;
    $.ajax({
        url: url_delete_member,
        async: true,
        type: "POST",
        data: {member_id: a.dataset.memberId},
        dataType: "json",
        success: function(result) {
            $(a).parents("tr").remove();
            alert(((result.success) ? "SUCCESS" : "ERROR") + ": " + result.info);
        }
    });
    return false;
};

/**
 * Swap from read/write mode to read only and save the changes. There is a kind
 * of asynchronous cross-recursivity with admin_edit_text()
 * @see admin_edit_photo_metadata()
 * @param a {Object} - A link to the icon, which will be updated (icon & event).
 */
var admin_save_photo_metadata = function(a) {
    var inputs = $(a).parents("form").find(".readonly");
    inputs.prop("disabled", true);
    $(a).children("svg").remove();
    $(a).children("i").remove();
    $(a).off("click.save");
    $(a).append('<i class="fas fa-pen-square fa-2x"></i>');
    $(a).on("click.edit", function() {
        admin_edit_photo_metadata(a);
        return false;
    });
    $.ajax({
        url: url_save_photo_metadata,
        async: true,
        method: "POST",
        data: {
            photo_id: a.dataset.photoId,
            title: $(inputs[0]).val(),
            focal_length: $(inputs[1]).val(),
            exposure_numerator: $(inputs[2]).val(),
            exposure_denominator: $(inputs[3]).val(),
            f: $(inputs[4]).val(),
            iso: $(inputs[5]).val(),
            access_level: $(inputs[6]).val(),
            local_date_taken: $(inputs[7]).val(),
            description: $(inputs[8]).val()
        },
        dataType: "json",
        success: function(result) {
            alert(((result.success) ? "SUCCESS" : "ERROR") + ": " + result.info);
        }
    });
    return false;
};

/**
 * Ask for a confirmation then delete asynchronously the photo.
 * An other popup appears to confirm the successful or failed deletion.
 * @param a {Object} - A link in the table row so that the row can be deleted.
 */
var admin_delete_photo = function(a) {
    if(confirm("Do you really want to permanently delete this photo?")) {
        $(a).closest("form").remove();
        $.ajax({
            url: url_delete,
            async: true,
            method: "POST",
            data: {photo_id: a.dataset.photoId},
            dataType: "json",
            success: function(result) {
                alert(((result.success) ? "SUCCESS" : "ERROR") + ": " + result.info);
            }
        });
    }
    return false;
};

/**
 * Ask for a confirmation then delete asynchronously the book.
 * An other popup appears to confirm the successful or failed deletion.
 * @param a {Object} - A link in the table row so that the row can be deleted.
 */
var admin_delete_book = function(a) {
    if(confirm("Do you really want to permanently delete this book?")) {
        $(a).closest("form").remove();
        $.ajax({
            url: url_delete_book,
            async: true,
            method: "POST",
            data: {book_id: a.dataset.bookId, book_url: a.dataset.bookUrl},
            dataType: "json",
            success: function(result) {
                alert(((result.success) ? "SUCCESS" : "ERROR") + ": " + result.info);
            }
        });
    }
    return false;
};

/**
 * Swap from read only to read/write mode so that the admin can edit the title,
 * the description and the access level of a listed photo. There is a kind of
 * asynchronous cross-recursivity with admin_save_text()
 * @see admin_save_photo_metadata()
 * @param a {Object} - A link to the icon, which will be updated (icon & event).
 */
var admin_edit_photo_metadata = function(a) {
    $(a).parents("form").find(".readonly").removeAttr("disabled");
    $(a).children("svg").remove();
    $(a).children("i").remove();
    $(a).off("click.edit"); // remove the event created in admin_save_text()
    $(a).append('<i class="fas fa-save fa-2x"></i>');
    $(a).on("click.save", function() {
        return admin_save_photo_metadata(a);
    });
    return false;
};


/**
 * Swap from read only to read/write mode so that the admin can edit the metadata
 * of a listed photo. There is a kind of asynchronous cross-recursivity with
 * admin_save_book_metadata()
 * @see admin_save_book_metadata()
 * @param a {Object} - A link to the icon, which will be updated (icon & event).
 */
var admin_edit_book_metadata = function(a) {
    $(a).parents("form").find(".readonly").removeAttr("disabled");
    $(a).children("svg").remove();
    $(a).children("i").remove();
    $(a).off("click.edit"); // remove the event created in admin_save_book_metadata()
    $(a).append('<i class="fas fa-save fa-2x"></i>');
    $(a).on("click.save", function() {
        return admin_save_book_metadata(a);
    });
    return false;
};

/**
 * Swap from read/write mode to read only and save the changes. There is a kind
 * of asynchronous cross-recursivity with admin_edit_book_metadata()
 * @see admin_edit_book_metadata()
 * @param a {Object} - A link to the icon, which will be updated (icon & event).
 */
var admin_save_book_metadata = function(a) {
    // get all fields before they are disabled
    var form_data = new FormData($(a).parents("form").get(0));

    var inputs = $(a).parents("form").find(".readonly");
    inputs.prop("disabled", true);
    $(a).children("svg").remove();
    $(a).children("i").remove();
    $(a).off("click.save");
    $(a).append('<i class="fas fa-pen-square fa-2x"></i>');
    $(a).on("click.edit", function() {
        admin_edit_book_metadata(a);
        return false;
    });
    $.ajax({
        url: url_save_book_metadata,
        async: true,
        method: "POST",
        data: form_data,
        processData: false, // required when transferring FormData
        contentType: false, // required when transferring FormData
        dataType: "json",
        success: function(result) {
            alert(((result.success) ? "SUCCESS" : "ERROR") + ": " + result.info);
        }
    });
    return false;
};

/**
 * Move the photo identified ``dropped_id`` below ``id_above_drop`` and above
 * ``id_below_drop``.
 * @param dropped_id {Number} - ID of the dragged and dropped photo.
 * The ID refers to the database, not the DOM.
 * @param id_above_drop {Number} - ID of the photo located above, after the drop.
 * -1 if no photo is found (top of the page).
 * @param id_below_drop {Number} - ID of the photo located below, after the drop.
 * -1 if no photo is found (bottom of the page).
 */
var admin_move_photo = function(dropped_id, id_above_drop, id_below_drop) {
    $.ajax({
        url: url_move_photo,
        async: true,
        method: "POST",
        data: {
            dropped_id: dropped_id,
            id_above_drop: id_above_drop,
            id_below_drop: id_below_drop
        },
        dataType: "json",
        success: function(result) {
            alert(((result.success) ? "SUCCESS" : "ERROR") + ": " + result.info);
        }
    });
};

/**
 * Move the book identified ``dropped_id`` below ``id_above_drop`` and above
 * ``id_below_drop``.
 * @param dropped_id {Number} - ID of the dragged and dropped book.
 * The ID refers to the database, not the DOM.
 * @param id_above_drop {Number} - ID of the book located above, after the drop.
 * -1 if no book is found (top of the page).
 * @param id_below_drop {Number} - ID of the book located below, after the drop.
 * -1 if no book is found (bottom of the page).
 */
var admin_move_book = function(dropped_id, id_above_drop, id_below_drop) {
    console.log("dropped_id=" + dropped_id);
    console.log("id_above_drop=" + id_above_drop);
    console.log("id_below_drop=" + id_below_drop);
    $.ajax({
        url: url_move_book,
        async: true,
        method: "POST",
        data: {
            dropped_id: dropped_id,
            id_above_drop: id_above_drop,
            id_below_drop: id_below_drop
        },
        dataType: "json",
        success: function(result) {
            alert(((result.success) ? "SUCCESS" : "ERROR") + ": " + result.info);
        }
    });
};

/**
 * Configuration switch according to the user's ordering choice.
 * @param enable_ordering {Boolean} - True to enable ordering. If not set, the choice depends on the URL parameter.
 */
var update_ordering = function(list, enable_ordering) {
    var ordering_is_selected = (typeof enable_ordering == "undefined") ? ($.urlParam("ordering") == "enabled") : enable_ordering;
    if($("#order-by").length != 0) {
        $("#order-by").prop("disabled", ordering_is_selected ? "disabled" : false);
    }
    $(list).sortable("option", "disabled", !ordering_is_selected);
    $("#orderingSwitch").prop("checked", ordering_is_selected);
};

/**
 * Make the photos sortable and the 'photos per page' selector dynamic.
 */
var init_admin_list_of_photos = function() {
    if($("#admin-photos").length == 0) {
        return;
    }
    
    var get_selected_param = function(param, el) {
        var selected_param = $.urlParam(param);
        if(!selected_param) {
            selected_param = $(el).find(":selected").text();
        }
        return selected_param;
    };

    $(".onclick-admin-edit-text")
    .on("click.edit", function() {
        return admin_edit_photo_metadata(this);
    });

    $(".onclick-admin-delete-photo")
    .click(function() {
        return admin_delete_photo(this);
    });
    
    // the switch can enable/disable the drag & drop feature in order to avoid intempestive actions
    $("#orderingSwitch")
    .click(function() {
        update_ordering("#admin-photos", this.checked);
        if(this.checked && $("#order-by option:selected").text() != "position") {
            $(location).attr("href", "?photos=" + get_selected_param("photos", "#photos-per-page") + "&ordering=enabled");
        }
    });

    $("#admin-photos").sortable({
        disabled: true,
        cursor: "move",
        cursorAt: { top: 150, left: 0 },
        scrollSpeed: 80,
        scrollSensitivity: 50,
        axis: "y",
        opacity: 0.7,
        stop: function(event, ui) {
            var thumbnails = $("#admin-photos img.thumbnail-photo");
            var current_dragged_id = $(thumbnails).get(ui.item.index()).dataset.id;
            var id_above_drop =
                ui.item.index() == 0
                ? -1
                : $(thumbnails)[ui.item.index() - 1].dataset.id;
            var id_below_drop =
                (ui.item.index() + 1) == thumbnails.length
                ? -1
                : $(thumbnails)[ui.item.index() + 1].dataset.id;
            admin_move_photo(current_dragged_id, id_above_drop, id_below_drop);
        },
        items: ".sortable-item",
        placeholder: "row border rounded bg-warning shadow my-3 placeholder-item",
        helper: function(event, ui) {
            var img = '<img src="' + $(ui[0]).find("img.thumbnail-photo:first").attr("src") + '" alt="" />';
            return $('<div>' + img + '</div>' );
        }
    });
    update_ordering("#admin-photos");

    $("#photos-per-page").change(function() {
        $(location).attr("href", "?photos=" + $(this).find(":selected").text()
            + "&orderby=" + get_selected_param("orderby", "#order-by"));
    });
    $("#order-by").change(function() {
        $(location).attr("href", "?photos=" + get_selected_param("photos", "#photos-per-page")
            + "&orderby=" + $(this).find(":selected").text());
    });
};

/**
 * Make the books sortable and the 'books per page' selector dynamic.
 */
var init_admin_list_of_books = function() {
    if($("#admin-books").length == 0) {
        return;
    }

    $("#admin-books .onclick-admin-edit-book-metadata")
    .on("click.edit", function() {
        return admin_edit_book_metadata(this);
    });

    $("#admin-books .onclick-admin-delete-book")
    .click(function() {
        return admin_delete_book(this);
    });
    
    $("#orderingSwitch")
    .click(function() {
        update_ordering("#admin-books", this.checked);
    });

    $("#admin-books").sortable({
        cursor: "move",
        cursorAt: { top: 150, left: 0 },
        scrollSpeed: 80,
        scrollSensitivity: 50,
        axis: "y",
        opacity: 0.7,
        stop: function(event, ui) {
            var thumbnails = $("#admin-books img.thumbnail-book");
            var current_dragged_id = $(thumbnails).get(ui.item.index()).dataset.bookId;
            var id_above_drop =
                ui.item.index() == 0
                ? -1
                : $(thumbnails)[ui.item.index() - 1].dataset.bookId;
            var id_below_drop =
                (ui.item.index() + 1) == thumbnails.length
                ? -1
                : $(thumbnails)[ui.item.index() + 1].dataset.bookId;
            admin_move_book(current_dragged_id, id_above_drop, id_below_drop);
        },
        items: ".sortable-item",
        placeholder: "row border rounded bg-warning shadow my-3 placeholder-item",
        helper: function(event, ui) {
            var img = '<img src="' + $(ui[0]).find("img.thumbnail-book:first").attr("src") + '" alt="" style="max-height: 300px" />';
            return $('<div>' + img + '</div>' );
        }
    });
    update_ordering("#admin-books");
    
    var rel_height = (parseInt($("#admin-books .sortable-item").css("height")) - 60) + "px";
    $("#admin-books .table-resources").css("max-height", rel_height).css("display", "block");

    $("#books-per-page").change(function() {
        var books_per_page = $(this).find(":selected").text();
        var current_page = $.urlParam("page");
        if(!current_page) {
            current_page = 1;
        }
        $(location).attr("href", "?page=" + current_page + "&books=" + books_per_page);
    });
};

/**
 * Compute the number of months between ``d1`` and ``d2``.
 * @param d1 {Date} - The oldest of the two dates.
 * @param d2 {Date} - The most recent of the two dates.
 * @return {Number} The difference in months or 0.
 */
var month_diff = function(d1, d2) {
    var months;
    months = (d2.getFullYear() - d1.getFullYear()) * 12;
    months -= d1.getMonth();
    months += d2.getMonth();
    return months <= 0 ? 0 : months;
};

/**
 * Format ``date`` to string, f.i. "February, 2020"
 * @param date {Date} - The date to format.
 * @return {String} The formatted date.
 */
var format_date = function(date) {
    var month_name = new Intl.DateTimeFormat("en-US", {month: "long"}).format(date);
    return month_name + ", " + date.getFullYear();
};

/**
 * Return the month number. January = 01, February = 02, etc.
 * @param date {Date} - The date.
 * @return {String} The month number in two digits/characters.
 */
var two_digit_month = function(date) {
    var month = date.getMonth() + 1; // Remember that January is 0 in JS!
    return (month < 10) ? "0" + month : "" + month;
};

/**
 * Move the photo into the wastebasket.
 * @see admin_save_photo_metadata()
 * @param a {Object} - A link to the trash icon.
 */
var admin_move_photo_to_wastebasket = function(a) {
    if(confirm("Do you really want to permanently move this photo to the wastebasket?")) {
        $(a).closest("tr").remove();
        $.ajax({
            url: url_move_photo_to_wastebasket,
            async: true,
            method: "POST",
            data: {photo_filename: a.dataset.photoFilename},
            dataType: "json",
            success: function(result) {
                alert(((result.success) ? "SUCCESS" : "ERROR") + ": " + result.info);
            }
        });
    }
    return false;
};

/**
 * Initialize the page managing lost+found photos.
 */
var init_lost_photos = function() {
    if($("#lost-photos-in-database").length == 0) {
        return;
    }
    
    $('#lost-photos-in-database a.preview-tooltip[data-toggle="tooltip"]').tooltip({
        animation: true,
        placement: "right",
        html: true,
        trigger: "hover"
    });
    $('#lost-photos-in-database a.onclick-admin-move-photo-to-wastebasket[data-toggle="tooltip"]').tooltip({
        animation: true,
        placement: "left",
        trigger: "hover"
    });
    
    $(".onclick-admin-move-photo-to-wastebasket")
    .click(function() {
        return admin_move_photo_to_wastebasket(this);
    });
};

/**
 * Create charts.
 */
var init_admin_statistics = function() {
    if($(".chart-monthly-visits").length == 0) {
        return;
    }

    $(".chart-monthly-visits").each(function(i, obj) {
        var canvas = this;
        var ctx_chart = canvas.getContext("2d");
        var data_stats = JSON.parse(canvas.getAttribute("data-stats")); // more than one year
        var last_month = "" + data_stats[data_stats.length - 1][0]; // f.i. "202002"
        var last_date = new Date(parseInt(last_month.slice(0, 4)), parseInt(last_month.slice(4, 6)) - 1);
        var first_date = new Date(last_date);
        first_date.setFullYear(first_date.getFullYear() - 1); // one year earlier
        var first_month = "" + first_date.getFullYear() + two_digit_month(first_date);
        var total_months = month_diff(first_date, last_date) + 1; // 12 + 1 if diff is one year
        var label_months = new Array(total_months);
        var data_months = {"visits": new Array(total_months), "unique_visits": new Array(total_months)};
        var pos_data_stats = 0;
        var current_date = first_date;

        for(var i = 0; i < total_months; i++) { // correct offset to start looping only one year earlier
            if(parseInt(data_stats[pos_data_stats][0]) < parseInt(first_month)) {
                pos_data_stats++;
            }
            else {
                break;
            }
        }

        for(var i = 0; i < total_months; i++) {
            label_months[i] = format_date(current_date);
            if(data_stats[pos_data_stats][0] == ("" + current_date.getFullYear() + two_digit_month(current_date))) {
                data_months.visits[i] = data_stats[pos_data_stats][1];
                data_months.unique_visits[i] = data_stats[pos_data_stats][2];
                pos_data_stats++;
            }
            else {
                data_months[i] = 0;
            }
            current_date.setMonth(current_date.getMonth() + 1);
        }

        var chart = new Chart(ctx_chart, {
            type: "bar",
            data: {
                labels: label_months,
                datasets: [{
                    label: "Total visits this month",
                    backgroundColor: "rgb(0, 255, 0, 0.2)",
                    borderColor: "rgb(0, 0, 255)",
                    borderWidth: 1,
                    yAxisID: 'y-axis-visits',
                    data: data_months.visits
                }, {
                    label: "Total unique visits this month",
                    backgroundColor: "rgb(255, 255, 0, 0.2)",
                    borderColor: "rgb(255, 0, 0)",
                    borderWidth: 1,
                    yAxisID: 'y-axis-unique-visits',
                    data: data_months.unique_visits
                }]
            },
            options: {
                legend: {
                    display: false
                },
                scales: {
                    yAxes: [{
                        type: "linear",
                        display: true,
                        position: "left",
                        id: "y-axis-visits"
                    }, {
                        type: "linear",
                        display: true,
                        position: "right",
                        id: "y-axis-unique-visits",
                        gridLines: {
                            drawOnChartArea: false
                        }
                    }]
                }
            }
        });
    });
};

/**
 * Refresh the ``list`` of granted/denied sections of the website.
 * @param input {Object} - Input element (number).
 */
var refresh_access = function() {
    var selection = $("#change-member-access-level").val() || 0;
    $("#current-access-level").text(selection);
    $("#access").find("li[data-limit]").each(function() {
        if(Number(selection) >= Number(this.dataset.limit)) {
            $(this).removeClass("denied");
            $(this).addClass("granted");
        }
        else {
            $(this).removeClass("granted");
            $(this).addClass("denied");
        }
    });
};

/**
 * When the DOM is loaded and ready to be manipulated: Initialise the interface.
 */
$(function() {
    init_admin_add_photo();
    init_admin_add_book();
    init_admin_members();
    init_admin_list_of_photos();
    init_admin_list_of_books();
    init_admin_statistics();
    init_lost_photos();
});
