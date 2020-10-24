#
# Copyright 2020 Clement
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its contributors
#    may be used to endorse or promote products derived from this software
#    without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#

"""
Webhook for Ko-fi.com.
"""

from .db import get_db
from .utils import *

kofi_app = Blueprint("kofi_app", __name__)
mysql = LocalProxy(get_db)


@kofi_app.route("/webhook", methods=("POST",))
def kofi_webhook() -> FlaskResponse:
    """
    Webhook for Ko-fi.com, the idea is to receive data (f.i. on donation
    success) and save it to offer commissioned content in the website.

    API according to https://ko-fi.com/manage/webhooks:
        Here's an example of the data that will be sent when a payment
        is fully completed. If you don't have a server set up to receive
        webhooks but want to test the example, we suggest using a service
        like RequestBin to inspect the requests we send.

        data: {
        "message_id":"3a1fac0c-f960-4506-a60e-824979a74e74",
        "timestamp":"2017-08-21T13:04:30.7296166Z",
        "type":"Donation","from_name":"Ko-fi Team",
        "message":"Good luck with the integration!",
        "amount":"3.00",
        "url":"https://ko-fi.com"}

    Note:
        Selling commissions on Ko-fi is possible, it cost 5% fee for Free
        account, and 0% fee for Gold account. More information:
        https://ko-fi.com/manage/commissionssettings
    """
    try:
        data = json.loads(
            unquote_plus(request.get_data().decode("utf-8"))[len("data=") :]
        )
    except Exception:
        return basic_json(False, "Cannot decode data!")
    try:
        kofi_time = strptime(
            data.get("timestamp").split(".", 1)[0], "%Y-%m-%dT%H:%M:%S"
        )
        db_kofi_time = strftime("%Y-%m-%d %H:%M:%S", kofi_time)
    except Exception:
        return basic_json(False, "Cannot decode timestamp!")
    cursor = mysql.cursor()
    cursor.execute(
        """INSERT INTO webhook(message_id, data_timestamp,
        type, from_name, message, amount, url, ip)
        VALUES ('{message_id}', '{data_timestamp}', '{kofi_type}',
        '{from_name}', '{message}', {amount}, '{url}', INET6_ATON('{ip}'))""".format(
            message_id=escape(data.get("message_id")),
            data_timestamp=db_kofi_time,
            kofi_type=escape(data.get("type")),
            from_name=escape(data.get("from_name")),
            message=escape(data.get("message")),
            amount=float(data.get("amount")),
            url=escape(data.get("url")),
            ip=request.remote_addr,
        )
    )
    mysql.commit()
    return basic_json(True, "Thank you!")
