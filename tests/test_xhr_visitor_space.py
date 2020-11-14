#
# Copyright 2018-2020 Clement
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

import time

import werkzeug.security
from flask import json
from flask import session

from flaskr.db import get_db
from flaskr.visitor_space import subscribe_newsletter


def test_change_password(client, auth, app):
    """ Try to update a user email address. """
    with client, app.app_context() as ctx:
        # Test link generation and update request:
        rv = client.get("/change_email")  # get the form
        assert rv.status_code == 404  # the user is not logged
        auth.login()
        rv = client.get("/change_email")  # get the form
        assert rv.status_code == 200
        assert b"newEmailAddress" in rv.data
        rv = client.post("/change_email", data=dict())
        assert b"Missing data" in rv.data
        rv = client.post("/change_email", data=dict(currentPassword=""))
        assert b"Missing data" in rv.data
        rv = client.post("/change_email", data=dict(newEmailAddress=""))
        assert b"Missing data" in rv.data
        rv = client.post(
            "/change_email", data=dict(currentPassword="", newEmailAddress="")
        )
        assert b"Wrong password" in rv.data
        rv = client.post(
            "/change_email", data=dict(currentPassword="user", newEmailAddress="")
        )
        assert b"Invalid email" in rv.data
        rv = client.post(
            "/change_email",
            data=dict(
                currentPassword="user", newEmailAddress="abc"  # bad email format
            ),
        )
        assert b"Invalid email" in rv.data
        rv = client.post(
            "/change_email",
            data=dict(
                currentPassword="user",
                newEmailAddress=" user@test.com ",  # current email address
            ),
        )
        assert b"The new email has to be new" in rv.data
        rv = client.post(
            "/change_email",
            data=dict(
                currentPassword="user",
                newEmailAddress="news@letter.com",  # an other user email address
            ),
        )
        assert b"Invalid email" in rv.data
        new_email_address = "user@test.co.nz"
        rv = client.post(
            "/change_email",
            data=dict(
                currentPassword="user",
                newEmailAddress=new_email_address,  # a good email address
            ),
        )
        assert b"A link has been sent" in rv.data
        rv = client.post(
            "/change_email",
            data=dict(currentPassword="user", newEmailAddress=new_email_address),
        )
        assert b"Email already sent" in rv.data

        # Test link validation and email update:
        hashed_email = werkzeug.security.pbkdf2_hex(
            new_email_address, ctx.app.config["RANDOM_SALT"], keylen=21
        )
        rv = client.get("/change_email/0/" + hashed_email)
        assert rv.status_code == 404
        rv = client.get("/change_email/" + str(session["member_id"]) + "/NaN")
        assert rv.status_code == 404
        path = "/change_email/" + str(session["member_id"]) + "/" + hashed_email
        auth.logout()
        rv = client.get(path)
        assert rv.status_code == 404  # not logged in
        auth.login()
        rv = client.get(path)
        assert rv.status_code == 200
        assert b"Email address updated" in rv.data
        rv = client.get(path)
        assert rv.status_code == 404  # don't update twice
        assert session["email"] == new_email_address


def test_story_and_share_emotion_book(client):
    """ Test the story opening and logging logic - the `data-add-visit` tag. """
    with client:
        rv = client.get("/stories/42/second_story")
        assert rv.status_code == 404

        rv = client.get("/stories/2/second_story")
        assert b'data-add-visit="True"' in rv.data

        rv = client.post("/share_emotion_book")
        assert b"Emotion required" in rv.data
        rv = client.post("/share_emotion_book", data=dict(emotion="sad"))
        assert b"Invalid emotion" in rv.data
        rv = client.post("/share_emotion_book", data=dict(emotion="neutral"))
        assert b"Bad request, incorrect identifier" in rv.data
        rv = client.post("/share_emotion_book", data=dict(emotion="neutral", book_id=0))
        assert b"Bad request, incorrect identifier" in rv.data
        rv = client.post(
            "/share_emotion_book", data=dict(emotion="neutral", book_id=10000)
        )
        assert b"Bad request, incorrect identifier" in rv.data
        rv = client.post(
            "/share_emotion_book",
            data=dict(emotion="neutral", book_id=1),  # add entry to an other book
        )
        assert b"Thank you" in rv.data

        rv = client.get("/stories/2/second_story")
        assert b'data-add-visit="True"' in rv.data

        rv = client.post(
            "/share_emotion_book",
            data=dict(emotion="neutral", book_id=2),  # add entry to `second_story`
        )
        assert b"Thank you" in rv.data

        rv = client.get("/stories/2/second_story")
        assert b'data-add-visit="False"' in rv.data  # check the effect now


def test_password_creation_and_change(client, auth, app):
    """ Test the password creation process constraints """
    rv = client.post("/create_password", follow_redirects=True)
    assert rv.status_code == 404

    auth.login("root@test.com", "admin")
    rv = client.post("/admin/members/send_password_creation", data=dict(member_id=3))
    assert b"E-mail sent to the member" in rv.data
    with app.app_context():
        cursor = get_db().cursor()
        cursor.execute(
            """SELECT one_time_password
            FROM members
            WHERE member_id={member_id}""".format(
                member_id=3
            )
        )
        data = cursor.fetchone()
        one_time_password = data[0]
        assert one_time_password
    auth.logout()

    rv = client.get(
        "/create_password/1/hTeMHrmJTHm0mLLgUiQzZAxiipk79biElYXn3JeO3uiLH0nRvqg8U4lG1t2O5AJW/"
        + one_time_password,
        follow_redirects=True,
    )
    assert rv.status_code == 404  # bad member ID

    rv = client.get(
        "/create_password/3/hTeMHrmJTHm0mfLgUiQzZAxiipk79biElYXn3JeO3uiLH0nRvqg8U4lG1t2O5AJW/"
        + one_time_password,
        follow_redirects=True,
    )
    assert rv.status_code == 404  # bad newsletter ID

    rv = client.get(
        "/create_password/3/hTeMHrmJTHm0mfLgUiQzZAxiipk79biElYXn3JeO3uiLH0nRvqg8U4lG1t2O5AJW/M"
        + one_time_password,
        follow_redirects=True,
    )
    assert rv.status_code == 404  # bad one time password

    rv = client.get(
        "/create_password/3/hTeMHrmJTHm0mLLgUiQzZAxiipk79biElYXn3JeO3uiLH0nRvqg8U4lG1t2O5AJW/"
        + one_time_password,
        follow_redirects=True,
    )
    assert b"<h1>Create My Password</h1>" in rv.data  # show form

    rv = client.post(
        "/create_password",
        data=dict(
            newPassword="pwd",
            member_id=3,
            newsletter_id="hTeMHrmJTHm0mLLgUiQzZAxiipk79biElYXn3JeO3uiLH0nRvqg8U4lG1t2O5AJW",
            one_time_password=one_time_password,
        ),
        follow_redirects=True,
    )
    assert b"Missing data" in rv.data

    rv = client.post(
        "/create_password",
        data=dict(
            newPassword="pwd",
            passwordCheck="",
            member_id=3,
            newsletter_id="hTeMHrmJTHm0mLLgUiQzZAxiipk79biElYXn3JeO3uiLH0nRvqg8U4lG1t2O5AJW",
            one_time_password=one_time_password,
        ),
        follow_redirects=True,
    )
    assert b"Passwords required" in rv.data

    rv = client.post(
        "/create_password",
        data=dict(
            newPassword="pwd",
            passwordCheck=" pwd",
            member_id=3,
            newsletter_id="hTeMHrmJTHm0mLLgUiQzZAxiipk79biElYXn3JeO3uiLH0nRvqg8U4lG1t2O5AJW",
            one_time_password=one_time_password,
        ),
        follow_redirects=True,
    )
    assert b"Passwords different" in rv.data

    rv = client.post(
        "/create_password",
        data=dict(
            newPassword="pwd",
            passwordCheck=" pwd",
            member_id=3,
            newsletter_id="hTeMHrmJTHm0mLLgUiQzZAxiipk79biElYXn3JeO3uiLH0nRvqg8U4lG1t2O5AJW",
            one_time_password="W",
        ),
        follow_redirects=True,
    )
    assert rv.status_code == 404

    rv = client.post(
        "/create_password",
        data=dict(
            newPassword="pwd",
            passwordCheck="pwd",
            member_id=3,
            newsletter_id="hTeMHrmJTHm0mLLgUiQzZAxiipk79biElYXn3JeO3uiLH0nRvqg8U4lG1t2O5AJW",
            one_time_password=one_time_password,
        ),
        follow_redirects=True,
    )
    assert b"Password successfully created" in rv.data

    rv = client.post(
        "/change_password", data=dict(currentPassword="pwd"), follow_redirects=True
    )
    assert rv.status_code == 404  # member not connected

    rv = auth.login("news@letter.com", "pwd")
    assert b"animated-full-screen" in rv.data

    rv = client.get("/change_password", follow_redirects=True)
    assert b"<h1>Change My Password</h1>" in rv.data

    rv = client.post(
        "/change_password", data=dict(currentPassword="pwd"), follow_redirects=True
    )
    assert b"Missing data" in rv.data

    rv = client.post(
        "/change_password",
        data=dict(currentPassword="", newPassword="pwd", passwordCheck=""),
        follow_redirects=True,
    )
    assert b"Passwords required" in rv.data

    rv = client.post(
        "/change_password",
        data=dict(currentPassword=" pwd", newPassword="pwd", passwordCheck=" pwd"),
        follow_redirects=True,
    )
    assert b"Passwords different" in rv.data

    rv = client.post(
        "/change_password",
        data=dict(currentPassword=" pwd", newPassword="pwd", passwordCheck="pwd"),
        follow_redirects=True,
    )
    assert b"Wrong password" in rv.data

    rv = client.post(
        "/change_password",
        data=dict(
            currentPassword="pwd", newPassword="new pwd", passwordCheck="new pwd"
        ),
        follow_redirects=True,
    )
    assert b"Password successfully changed" in rv.data

    rv = auth.logout()
    rv = auth.login("news@letter.com", "new pwd")
    assert b"animated-full-screen" in rv.data


def test_unsubscribe_from_newsletter(client):
    """ Test the unsubscription. """
    rv = client.get(
        "/unsubscribe/2/hTeMHrmJTHm0mLLgUiQzZAxiipk79biElYXn3JeO3uiLH0nRvqg8U4lG1t2O5AJW",
        follow_redirects=True,
    )
    assert rv.status_code == 404  # bad member ID

    rv = client.get(
        "/unsubscribe/3/hTeMHrmJTHm0mLLgUiQzZAxiipkr9biElYXn3JeO3uiLH0nRvqg8U4lG1t2O5AJW",
        follow_redirects=True,
    )
    assert rv.status_code == 404  # bad newsletter ID

    with client:
        rv = client.get(
            "/unsubscribe/3/hTeMHrmJTHm0mLLgUiQzZAxiipk79biElYXn3JeO3uiLH0nRvqg8U4lG1t2O5AJW",
            follow_redirects=True,
        )
        assert b"You successfully unsubscribed" in rv.data

        cursor = get_db().cursor()
        cursor.execute(
            """SELECT COUNT(*)
            FROM members
            WHERE member_id={member_id}""".format(
                member_id=3
            )
        )
        assert cursor.fetchone()[0] == 0


def test_share_emotion_photo_before_log(client):
    """ Test the emotion interaction before ``/log_visit_photo``. """
    rv = client.post("/share_emotion_photo", data=dict())
    assert b"Emotion required" in rv.data

    rv = client.post("/share_emotion_photo", data=dict(emotion="soso"))
    assert b"Invalid emotion" in rv.data

    rv = client.post("/share_emotion_photo", data=dict(emotion="love"))
    assert b"Illogic request" in rv.data


def test_log_visit_photo(client, auth):
    """ Test the visitor logger and the emotion interaction after ``/log_visit_photo``. """
    with client:
        rv = client.post("/log_visit_photo", data=dict())
        assert b"Bad request" in rv.data

        rv = client.post("/log_visit_photo", data=dict(photo_id=0))
        assert b"Bad request" in rv.data

        rv = client.post("/log_visit_photo", data=dict(photo_id=210))
        assert b"Bad request" in rv.data

        rv = client.post("/log_visit_photo", data=dict(photo_id=2))
        assert rv.data == b""
        assert "last_visit_photo_id" in session
        assert session["last_visit_photo_id"] == 1

        rv = client.post("/log_visit_photo", data=dict(photo_id=3))
        assert b"Bad request" in rv.data  # permission denied

        auth.login()
        rv = client.post("/log_visit_photo", data=dict(photo_id=3))
        assert session["last_visit_photo_id"] == 2

        emotion = "love"
        rv = client.post("/share_emotion_photo", data=dict(emotion=emotion))
        assert b"Thank you" in rv.data
        assert "last_visit_photo_id" not in session
        cursor = get_db().cursor()
        cursor.execute(
            """SELECT element_id
            FROM visits
            WHERE visit_id={visit_id}
            AND emotion='{emotion}'
            AND element_type='gallery'""".format(
                emotion=emotion, visit_id=2
            )
        )
        data = cursor.fetchone()
        assert cursor.rowcount == 1
        assert data[0] == 3


def test_fetch_photos(client, auth):
    """ Try to fetch some photos. Check user access as well. """

    def entries(offset=0, total=6):
        return json.loads(
            client.post("/photos", data=dict(offset=offset, total=total)).data
        )

    # from the visitor's eyes:
    json_data = entries()
    assert len(json_data) == 3
    for row in json_data:
        assert row["description"] == "[undisclosed]"
        assert row["title"] == ""
    assert len(entries(1)) == 2
    assert len(entries(0, 2)) == 2

    # from the member's eyes, more photos including possible descriptions:
    auth.login()
    json_data = entries()
    assert len(json_data) == 4
    disclosed_desc = False
    for row in json_data:
        if row["description"] != "" or row["title"] != "":
            disclosed_desc = True
    assert disclosed_desc
    auth.logout()

    # from a super member's eyes:
    auth.login("root@test.com", "admin")
    assert len(entries()) == 5


def test_subscribe_newsletter(client):
    """ Test the simple newsletter subscription. """
    with client:
        rv = client.post("/subscribe", data=dict())
        assert b"Missing data" in rv.data

        # check format:
        rv = client.post("/subscribe", data=dict(email="user"))
        assert b"Invalid email" in rv.data

        # check insert:
        email = "user+news@example.com"
        rv = client.post("/subscribe", data=dict(email=email))
        assert b"Thank you" in rv.data

        assert "subscribed" in session
        rv = client.post("/subscribe", data=dict(email="b" + email))
        assert b"Thank you" in rv.data

        session.pop("subscribed", None)
        rv = client.post("/subscribe", data=dict(email=email))
        assert b"Thank you" in rv.data
        cursor = get_db().cursor()
        cursor.execute(
            """SELECT COUNT(newsletter_id)
            FROM members
            WHERE email='{email}' OR email='b{email}'""".format(
                email=email
            )
        )
        data = cursor.fetchone()
        assert data[0] == 1  # not 0, not 2, not 3, but only 1 entry!

        # check update:
        session.pop("subscribed", None)
        assert subscribe_newsletter(cursor, session, "root@test.com")
        cursor.execute(
            """SELECT newsletter_id
            FROM members
            WHERE member_id=1"""
        )
        data = cursor.fetchone()
        assert data[0] != "" and data[0] is not None


def test_contact(client):
    """ Test the contact. """

    # all fields are required:
    rv = client.post("/contact", data=dict(name="user"))
    assert b"Something fishy in the request" in rv.data

    # email address must be `valid`:
    rv = client.post(
        "/contact",
        data=dict(
            name="",
            email="user@testcom",
            message="",
            captcha="",
            browser_time="",
            win_res="",
            newsletter_subscription=0,
            privacy_policy=True,
        ),
    )
    assert b"Email required" in rv.data

    # a message must be written:
    rv = client.post(
        "/contact",
        data=dict(
            name="",
            email="user@test.com",
            message="",
            captcha="",
            browser_time="",
            win_res="",
            newsletter_subscription=0,
            privacy_policy=True,
        ),
    )
    assert b"Please write something" in rv.data

    # all good now:
    rv = client.post(
        "/contact",
        data=dict(
            name="",
            email="us er@test.com",  # whitespaces should be removed
            message="Once upon a time...",
            captcha="",  # not needed in testing mode
            browser_time="",  # could be anything (should not be trusted)
            win_res="",  # could be anything (should not be trusted)
            newsletter_subscription=0,
            privacy_policy=True,
        ),
    )
    assert b"Thanks a lot for your message" in rv.data
    assert b"thanks for subscribing to the newsletter" not in rv.data

    # cannot send an other message for a while:
    rv = client.post(
        "/contact",
        data=dict(
            name="",
            email="user@test.com",
            message="Once upon a time...",
            captcha="",
            browser_time="",
            win_res="",
            newsletter_subscription=0,
            privacy_policy=True,
        ),
    )
    assert b"Please wait before sending me another message" in rv.data
    time.sleep(2)

    # can send again and try this time with a specified name:
    with client:
        name = "Mozart"
        rv = client.post(
            "/contact",
            data=dict(
                name=name,
                email="unknown@test.com",
                message="Once upon a time...",
                captcha="",
                browser_time="",
                win_res="",
                newsletter_subscription=1,  # subscribe
                privacy_policy=True,
            ),
        )
        assert ("Thank you " + name).encode("utf-8") in rv.data

        # check the subscription as well:
        assert b"See you soon" in rv.data
        cursor = get_db().cursor()
        cursor.execute("SELECT username FROM members WHERE email='unknown@test.com'")
        data = cursor.fetchone()
        assert cursor.rowcount == 1
        assert data[0] == name

        time.sleep(2)
        # send again with a custom subject:
        data = dict(
            name=name,
            email="unknown@test.com",
            message="I forgot to tell you that...",
            captcha="",
            browser_time="",
            win_res="",
            newsletter_subscription=1,  # subscribe
            privacy_policy=True,
        )
        data["subjects[]"] = ["subject-is-hello", "subject-is-fine-art-print-enquiry"]
        rv = client.post("/contact", data=data)
        assert ("Thank you " + name).encode("utf-8") in rv.data
        # already subscribed but the feedback is the same to avoid guessing the email address book
        assert b"See you soon" not in rv.data  # test multi-subscription blocker


def test_detailed_feedback(client):
    """ Test the detailed feedback form. """
    # create the old_visit_id variable in session:
    rv = client.get("/stories/2/lost_hitchhiker")
    rv = client.post("/share_emotion_book", data=dict(emotion="neutral", book_id=2))

    # generate a good feedback:
    rv = client.post(
        "/detailed_feedback",
        data=dict(
            name="user",
            email="unknown@test.com",
            message="Once upon a time...",
            captcha="",
            browser_time="",
            win_res="",
            newsletter_subscription=0,
            privacy_policy=True,
        ),
    )
    assert b"Thank you user for your message" in rv.data

    # should not be possible to send more than one feedback per visit:
    rv = client.post(
        "/detailed_feedback",
        data=dict(
            name="user",
            email="unknown@test.com",
            message="See you soon!",
            captcha="",
            browser_time="",
            win_res="",
            newsletter_subscription=0,
            privacy_policy=True,
        ),
    )
    assert b"Undefined feedback source" in rv.data


def test_reset_password(client):
    """ Try to reset a user password. """
    rv = client.get("/reset_password")
    assert b"Password Reset" in rv.data

    rv = client.post("/reset_password", data=dict(email=""))
    assert b"Missing data" in rv.data

    rv = client.post("/reset_password", data=dict(email="a", captcha=""))
    assert b"Too many attempts" in rv.data

    time.sleep(2)

    rv = client.post("/reset_password", data=dict(email="a", captcha=""))
    assert b"Bad email address format" in rv.data

    time.sleep(2)

    rv = client.post(
        "/reset_password",
        data=dict(email="abc@def.co", captcha=""),  # unknown email
        follow_redirects=True,
    )
    # default message to avoid guessing the email address book
    assert b"password reset link has been sent" in rv.data

    time.sleep(2)

    rv = client.post(
        "/reset_password",
        data=dict(email="user@test.com", captcha=""),  # known email
        follow_redirects=True,
    )
    assert b"password reset link has been sent" in rv.data
