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
 * Register a handler to be called when Ajax requests complete with an error
 * or the Ajax requests prematurely stopped before completion (status code 0).
 * This is an Ajax Event. Actions are:
 * * Print a message in the console;
 * * Send a message to Sentry.
 * @param event {Event} - Event object.
 * @param jq_xhr {jqXHR} - The JQuery XHR object.
 * @param settings {PlainObject} - Settings object that was used in the creation of the request.
 * @param thrown_error {String} - Textual HTTP status, such as "Not Found" or "Internal Server Error."
 */
$(document).ajaxError(function (event, jq_xhr, settings, thrown_error) {
    info =
        "Error XHR to '" +
        settings.url +
        "' status " +
        jq_xhr.status +
        ": " +
        thrown_error;
    console.log(info);
    Sentry.captureMessage(thrown_error || jq_xhr.statusText, {
        extra: {
            type: settings.type,
            url: settings.url,
            data: settings.data,
            status: jq_xhr.status,
            error: thrown_error || jq_xhr.statusText,
            response:
                typeof jq_xhr.responseText === "undefined"
                    ? typeof jq_xhr.responseXML === "undefined"
                        ? ""
                        : jq_xhr.responseXML.substring(0, 100)
                    : jq_xhr.responseText.substring(0, 100),
        },
    });
});
