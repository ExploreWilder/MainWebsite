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
Email sender with extra-security.
"""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate

import dkim

from .utils import *


class SecureEmail:
    """ Handle the SMTP connection and send DKIM-signed emails. """

    #: The *From* field of the email as ``self.user``@``self.domain``. String-type.
    mail_from: str

    #: The username of the *From* field. String-type.
    user: str

    #: The domain name of the *From* field. String-type.
    domain: str

    #: The DKIM private ASCII key as Bytes.
    dkim_private_key: bytes

    #: The DKIM selector as Bytes.
    dkim_selector: bytes

    #: The SMTP socket. Open with ``__init__()`` and closed with ``__del__()``.
    socket: smtplib.SMTP

    def __init__(self, app) -> None:
        """
        Configure the email account and open an SMTP connection.
        The SMTP host is `localhost`.
        More information: https://docs.python.org/3/library/smtplib.html#smtplib.SMTP

        Args:
            app: Contains the configuration with the following fields:
                * EMAIL_USER (str): The username of the *From* field, f.i. `hello` in `hello@example.com`.
                * EMAIL_DOMAIN (str): The domain name of the *From* field, f.i. `example.com` in `hello@example.com`.
                * DKIM_PATH_PRIVATE_KEY (str): Path to the DKIM private ASCII key.
                * DKIM_SELECTOR (str): The DKIM selector.
                * DEBUG or TESTING (bool): Write the message in stdout instead of sending the e-mail.

        Raises:
            smtplib exception.
        """
        self.debug = app.config["DEBUG"] or app.config["TESTING"]
        self.user = app.config["EMAIL_USER"]
        self.domain = app.config["EMAIL_DOMAIN"]
        self.mail_from = self.user + "@" + self.domain
        self.dkim_private_key = (
            open(app.config["DKIM_PATH_PRIVATE_KEY"]).read().encode()
        )
        self.dkim_selector = app.config["DKIM_SELECTOR"].encode()
        if not self.debug:  # pragma: no cover
            self.socket = smtplib.SMTP("localhost")

    def get_mail_from(self) -> str:
        """ Returns the webmaster email according to the configuration. """
        return self.mail_from

    def send(
        self, mailto: str, subject: str, text: str, html: str
    ) -> Optional[MIMEMultipart]:
        """
        Create and send a text/HTML email. Multiple calls use the same SMTP session.
        A `Message-ID`, `Date`, and `DKIM-Signature` fields are added to the email.

        Args:
            mailto (str): The email address of the receiver.
            subject (str): The email subject.
            text (str): The email content in plain text format.
            html (str): The email content in HTML format.

        Raises:
            smtplib exception.

        Returns:
            Dict: The created message if in debug or testing mode. None otherwise.
        """
        message = MIMEMultipart("alternative")
        message["From"] = self.mail_from
        message["To"] = mailto
        message["Date"] = formatdate()  # better ranking on SpamAssassin
        message["Message-ID"] = (
            "<" + str(time()) + "-" + random_text(15) + "@" + self.domain + ">"
        )
        message["Subject"] = subject
        message.attach(MIMEText(text, "plain"))
        message.attach(MIMEText(html, "html"))
        headers = [b"from", b"to", b"subject", b"message-id"]
        sig = dkim.sign(
            message.as_bytes(),
            self.dkim_selector,
            self.domain.encode(),
            self.dkim_private_key,
            include_headers=headers,
        )
        sig = sig.decode()
        message["DKIM-Signature"] = sig[len("DKIM-Signature: ") :]
        if not self.debug:  # pragma: no cover
            self.socket.sendmail(message["From"], message["To"], message.as_string())
            return None
        return message

    def __del__(self) -> None:
        """
        Terminate the SMTP session and close the connection.
        """
        if not self.debug:  # pragma: no cover
            self.socket.quit()
