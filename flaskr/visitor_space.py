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

"""
Main interfaces with the visitor.
"""

from .book_processor import BookProcessor
from .cache import cache
from .captcha import Captcha
from .db import get_db
from .secure_email import SecureEmail
from .utils import *

visitor_app = Blueprint("visitor_app", __name__)
mysql = LocalProxy(get_db)


def subscribe_newsletter(
    cursor: MySQLCursor, current_session: Dict, email: str, name: str = ""
) -> bool:
    """
    Subscribe `email` to the newsletter.

    Returns:
        bool: True if the database has been updated, false if `email`
              already have a newsletter_id or the visitor already
              subscribed during the current session.
    """
    if "subscribed" in current_session:
        return False

    cursor.execute(
        """SELECT newsletter_id
        FROM members
        WHERE email='{email}'""".format(
            email=email
        )
    )
    member_data = cursor.fetchone()
    new_subscription = False

    if cursor.rowcount == 0 or not member_data:  # new member
        cursor.execute(
            """INSERT INTO members(username, email, newsletter_id)
            VALUES ({username}, '{email}', '{newsletter_id}')""".format(
                username=("'" + name.title() + "'") if name else "NULL",
                email=email,
                newsletter_id=generate_newsletter_id(),
            )
        )
        new_subscription = True

    # existing member but new in the newsletter list:
    elif not member_data[0]:  # type: ignore[index]
        cursor.execute(
            """UPDATE members
            SET newsletter_id='{newsletter_id}'
            WHERE email='{email}'""".format(
                newsletter_id=generate_newsletter_id(), email=email
            )
        )
        new_subscription = True

    current_session["subscribed"] = True
    return new_subscription


def add_audit_log(
    member_id: int, ip_addr: str, event_description: str = "logged_in"
) -> None:
    """
    Add an entry to the audit log.

    Args:
        member_id (int): The member ID (refer to the `members` table).
        ip_addr (str): Full IP address.
        event_description (str): The event type such as:
            * logged_in (default): The member successfully logged in,
            * password_changed: The member successfully changed his password,
            * password_reset: The member successfully reset or created his password,
            * email_changed: The member successfully changed his email address,
            * app_token_generated: The member successfully generated an app token (QMapShack),
            * app_token_deleted: The member successfully deleted an app token (QMapShack),
            * app_token_used: The member successfully checked an app token and generated a UUID (QMapShack),
            * 2fa_enabled: The member successfully enabled the 2-factor authentication,
            * 2fa_disabled: The member successfully disabled the 2-factor authentication.
    """
    cursor = mysql.cursor()
    cursor.execute(
        """INSERT INTO members_audit_log(member_id, event_description, ip)
        VALUES ({member_id}, '{event_description}', INET6_ATON('{ip}'))""".format(
            member_id=member_id, event_description=event_description, ip=ip_addr
        )
    )
    mysql.commit()


def fetch_audit_log(member_id: int, event_description: str = "") -> Union[Tuple, None]:
    """
    Get the full list of (time, IP address) tuple from last to first.

    Args:
        member_id (int): The member ID (refer to the `members` table).
        event_description (str): The event type or None to select types.

    Returns:
        A tuple of tuple or None if the user has never logged in.
    """
    cursor = mysql.cursor()
    cursor.execute(
        """SELECT time, INET6_NTOA(ip) AS ip_asc, event_description
        FROM members_audit_log
        WHERE member_id={member_id} {events}
        ORDER BY members_audit_log_id
        DESC""".format(
            member_id=member_id,
            events="AND event_description='" + event_description + "'"
            if event_description
            else "",
        )
    )
    return cursor.fetchall() or None


@visitor_app.route("/photos/<int:photo_id>/<string:filename>")
def photo_dir(photo_id: int, filename: str) -> FlaskResponse:
    """
    Make photo files reachable by the user.
    Check a few things before to send the picture:

    * The photo is in the database,
    * The user is allowed to see the photo,
    * Only the thumbnail is reachable by external requests.

    """
    filename = secure_filename(escape(filename))
    cursor = mysql.cursor()
    cursor.execute(
        """SELECT access_level, thumbnail_src
        FROM gallery
        WHERE photo_id={id} AND (
        thumbnail_src='{filename}'
        OR photo_m_src='{filename}'
        OR photo_l_src='{filename}'
        OR raw_src='{filename}')""".format(
            id=photo_id, filename=filename
        )
    )
    data = cursor.fetchone()
    if cursor.rowcount == 0 or actual_access_level() < data[0]:
        abort(404)
    if (
        data[1] != filename
        and (not is_same_site())
        and (not current_app.config["TESTING"])
    ):
        abort(404)  # pragma: no cover
    return send_from_directory(current_app.config["GALLERY_FOLDER"], filename)


@visitor_app.route("/stories/locked.jpg")
@same_site
def image_of_locked_books() -> FlaskResponse:
    """
    Image of the locked book(s).
    """
    return send_from_directory(
        current_app.config["SHELF_FOLDER"], "locked.jpg", as_attachment=False
    )


@visitor_app.route("/stories/<int:book_id>/<string:filename>.<string:ext>")
def book_dir(book_id: int, filename: str, ext: str) -> FlaskResponse:
    """
    Make documents of a book reachable by the user. PDF file is sent as attachment.
    The extension is separated from the filename in order to identify this route
    with the story book defined with story().
    Check a few things before to send the file:
    * The book is in the database,
    * The user is allowed to access the book.
    """
    ext = escape(ext)
    filename = secure_filename(escape(filename)) + "." + ext
    cursor = mysql.cursor()
    cursor.execute(
        """SELECT access_level, url
        FROM shelf
        WHERE book_id={id}""".format(
            id=book_id
        )
    )
    data = cursor.fetchone()
    if cursor.rowcount == 0 or actual_access_level() < data[0]:
        abort(404)
    if (
        ext == "gpx"
        and actual_access_level() < current_app.config["ACCESS_LEVEL_DOWNLOAD_GPX"]
    ):
        abort(404)
    return send_from_directory(
        os.path.join(current_app.config["SHELF_FOLDER"], data[1]),
        filename,
        as_attachment=ext in ("gpx", "pdf"),
    )


@visitor_app.route("/sitemap.xml")
@cache.cached()
def sitemap() -> Any:
    """
    Generate sitemap.xml. Makes a list of urls and date modified.
    The sitemap only includes the main public pages and released and
    public stories.
    """
    pages = []
    ten_days_ago = (
        (datetime.datetime.now() - datetime.timedelta(days=7)).date().isoformat()
    )
    static_links = ["", "stories", "about", "contact"]
    cursor = mysql.cursor()
    cursor.execute(
        "SELECT book_id, url FROM shelf WHERE access_level=0 AND status='released'"
    )
    open_books = cursor.fetchall()
    dynamic_links = (
        ["stories/" + str(book[0]) + "/" + book[1] for book in open_books]
        if cursor.rowcount
        else []
    )
    for link in static_links + dynamic_links:
        pages.append([request.url_root + link, ten_days_ago])
    sitemap_xml = render_template("sitemap.xml", pages=pages)
    response = make_response(sitemap_xml)
    response.headers["Content-Type"] = "application/xml"
    return response


@visitor_app.route("/audit_log")
def audit_log() -> Any:
    """
    List all events related to the connected member.
    """
    if "member_id" not in session:
        abort(404)
    return render_template(
        "audit_log.html",
        full_audit_log=fetch_audit_log(session["member_id"]),
    )


@visitor_app.route("/stories")
def shelf() -> Any:
    """
    List my stories and e-books.
    The listing is ordered by `shelf`.`position` DESC and takes into account the
    user's access level before returning the data, i.e. metadata of restricted books
    are not returned. `ext` is the file name of the book in order to adapt the
    interface accordingly.
    """
    access_level = actual_access_level()
    cursor = mysql.cursor()
    cursor.execute(
        """SELECT s.url, s.file_name,
        SUBSTRING_INDEX(s.file_name,'.',-1) AS ext, s.title, s.period,
        s.description_html, s.status, s.book_id,
        IFNULL(FLOOR(100*SUM(w.amount)/s.crowdfunding_goal),0) AS total_raised_percent,
        preview_card
        FROM shelf s
        LEFT JOIN webhook w
        ON w.curr_timestamp > s.date_added
        WHERE s.access_level <= {access_level}
        GROUP BY s.book_id
        ORDER BY s.position DESC""".format(
            access_level=access_level
        )
    )
    data_shelf = cursor.fetchall()
    formatted_shelf = []
    for book in data_shelf:  # put the JPEG preview into a blurred SVG
        book_list = list(book)
        try:
            card_size = get_image_size(
                os.path.join(current_app.config["SHELF_FOLDER"], book[0], "card.jpg")
            )
        except FileNotFoundError:
            book_list[9] = ""
        else:
            # trick: https://css-tricks.com/the-blur-up-technique-for-loading-background-images/
            book_list[9] = "data:image/svg+xml;charset=utf-8," + quote(
                render_template(
                    "preview.svg",
                    image_width=card_size[0],
                    image_height=card_size[1],
                    data_jpeg=book[9],
                )
            )
        formatted_shelf.append(tuple(book_list))
    return render_template(
        "shelf.html",
        shelf=formatted_shelf,
        default_name=session["username"] if "username" in session else "",
        default_email=session["email"] if "email" in session else "",
        is_logged="access_level" in session,
        total_subscribers=total_subscribers(cursor),
        current_year=current_year(),
    )


@visitor_app.route("/stories/<int:book_id>/<string:story_url>")
def story(book_id: int, story_url: str) -> Any:
    """
    Print one story. The story is printed only if the visitor's access level is
    okay and if the book file is Markdown. The story can be a draft, so you can
    share the URL or change the access level to avoid disclosure.
    Check if not draft if the user access level == 0: exclusive member access to draft!

    Args:
        book_id (int): Book ID according to the `shelf` table.
        story_url (str): Book URL according to the table (case insensitive).
    """
    story_url = escape(story_url).lower()
    access_level = actual_access_level()
    cursor = mysql.cursor()
    cursor.execute(
        """SELECT book_id, title, period, status, file_name,
        description_md, description_html, SUBSTRING_INDEX(file_name,'.',-1) AS file_ext
        FROM shelf
        WHERE access_level <= {access_level} {cond_and_draft}
        AND book_id={id}
        AND url='{url}'
        AND (SUBSTRING_INDEX(file_name,'.',-1)='md'
            OR SUBSTRING_INDEX(file_name,'.',-1)='json')""".format(
            id=book_id,
            access_level=access_level,
            cond_and_draft="" if access_level > 0 else "AND status='released'",
            url=story_url,
        )
    )
    data = cursor.fetchone()
    if cursor.rowcount == 0:
        abort(404)
    add_visit = True
    if "last_visited_book_id" in session:
        if session["last_visited_book_id"] == book_id:
            add_visit = False
    book_ext = data[7]
    if book_ext == "md":
        try:
            print(request.url_rule)
            book_processor = BookProcessor(
                current_app, request.url, book_id, story_url, data[4]
            )
            book_content = book_processor.print_book()
        except FileNotFoundError:
            current_app.logger.exception("Failed to process Markdown file")
    else:
        book_content = BookProcessor.get_empty_book()
    book = {
        "id": book_id,
        "title": data[1],
        "url": story_url,
        "description": {"md": data[5], "html": data[6]},
        "period": data[2],
        "status": data[3],
        "ext": book_ext,
        "filename": data[4],
        "content": book_content,
    }
    thumbnail_networks = (
        request.url_root + "books/" + str(book_id) + "/" + story_url + "/card.jpg"
    )
    return render_template(
        "story.html" if book_ext == "md" else "storytelling_map.html",
        book=book,
        add_visit=add_visit,
        default_name=session["username"] if "username" in session else "",
        default_email=session["email"] if "email" in session else "",
        total_subscribers=total_subscribers(cursor),
        thumbnail_networks=thumbnail_networks,
    )


@visitor_app.route("/about")
def about() -> Any:
    """ The about page with the contact form. """
    return render_template(
        "about.html",
        default_name=session["username"] if "username" in session else "",
        default_email=session["email"] if "email" in session else "",
        total_subscribers=total_subscribers(mysql.cursor()),
        current_year=current_year(),
    )


@visitor_app.route("/detailed_feedback", methods=("POST",))
@visitor_app.route("/contact", methods=("POST",))
def send_mail() -> FlaskResponse:
    """
    The XHR procedure, check all fields and send the email.
    The email includes system information for security and debug purposes.
    The email is sent only in production mode and its content is HTML only.
    The visitor can subscribe to the newsletter from the same interface.
    He is added to the list of members only if he subscribes to the
    newsletter, indeed any member not accepting news from the website is
    a kind of meaningless ghost.
    """
    is_detailed_feedback = "detailed_feedback" in str(request.url_rule)
    if is_detailed_feedback and "old_visit_id" not in session:
        return basic_json(False, "Undefined feedback source!")
    if not all(
        x in request.form
        for x in [
            "name",
            "email",
            "message",
            "captcha",
            "browser_time",
            "win_res",
            "privacy_policy",
            "newsletter_subscription",
        ]
    ):
        return basic_json(False, "Something fishy in the request!")
    if "last_message" in session and (
        int(session["last_message"]) + current_app.config["REQUIRED_TIME_GAP"]
    ) > int(time()):
        return basic_json(False, "Please wait before sending me another message!")
    email = remove_whitespaces(escape(request.form["email"]))
    if not is_detailed_feedback and not email_is_valid(email):
        return basic_json(False, "Email required!")
    message = new_line_to_br(escape(request.form["message"].strip()))
    if message == "":
        return basic_json(False, "Please write something!")
    if not Captcha(current_app).check(
        escape(request.form["captcha"])
    ):  # pragma: no cover
        return basic_json(False, "Invalid CAPTCHA, try again!")
    name = escape(request.form["name"].strip())
    if name == "":
        printable_name = "Unknown"
        answer = "Thanks a lot for your message!"
        # sender = email
    else:
        printable_name = name
        answer = "Thank you " + name + " for your message!"
        # sender = name + " <" + email + ">"

    if request.form.getlist("subjects[]"):
        dic = {
            "subject-is-hello": "Hello Clement!",
            "subject-is-friendly-feedback": "Friendly Feedback",
            "subject-is-love-letter-or-poem": "Love Letter or Poem",
            "subject-is-partnership-or-sponsorship": "Partnership or Sponsorship",
            "subject-is-fine-art-print-enquiry": "Fine Art Print Enquiry",
            "subject-is-ebook-or-hard-copy-enquiry": "eBook or Hard Copy Enquiry",
            "subject-is-technical-feedback-or-bug-report": "Technical Feedback or Bug Report",
        }

        selected_subjects = [dic.get(n, "") for n in request.form.getlist("subjects[]")]
        li_elements = "</li><li>".join(selected_subjects)
        subject = "<p>Subjects:</p><ul><li>" + li_elements + "</li></ul>"
    else:
        subject = "<p>No subject selected!</p>"

    subscribe_me = int(request.form["newsletter_subscription"]) == 1

    cursor = mysql.cursor()
    if is_detailed_feedback:
        # find out the element (book or photo) of the feedback:
        cursor.execute(
            """SELECT element_type, element_id
            FROM visits
            WHERE visit_id={visit_id}""".format(
                visit_id=int(session["old_visit_id"])
            )
        )
        data_from_visits = cursor.fetchone()
        if cursor.rowcount == 0:
            return basic_json(False, "Invalid feedback source!")
        element_type = "photo" if data_from_visits[0] == "gallery" else "book"

        # find out the information about the element:
        cursor.execute(
            """SELECT {col_element_src}, title
            FROM {table}
            WHERE {col_element_id}={element_id}""".format(
                col_element_src="photo_l_src"
                if data_from_visits[0] == "gallery"
                else "url",
                table=data_from_visits[0],
                col_element_id=element_type + "_id",
                element_id=data_from_visits[1],
            )
        )
        data_from_element = cursor.fetchone()
        if cursor.rowcount == 0:
            return basic_json(False, "Broken link with the log!")
        if data_from_visits[0] == "gallery":
            element_abs_src = "admin/photos/open/" + data_from_element[0]
        else:
            element_abs_src = (
                "stories/" + str(data_from_visits[1]) + "/" + data_from_element[0]
            )

        feedback_source = """
        <p>
        <strong>Feedback from the following {element_type}: <a href="{element_abs_src}">{element_title}</a></strong>
        </p>
        <hr />
        """.format(
            element_type=element_type,
            element_abs_src=request.host_url + element_abs_src,
            element_title=data_from_element[1],
        )
    else:
        feedback_source = ""

    mailto = current_app.config["EMAIL_USER"] + "@" + current_app.config["EMAIL_DOMAIN"]
    content = """
    {subject}
    <hr />
    {feedback_source}
    <p>{message}</p>
    <hr />
    <ul style="font-size: 80%;">
    <li>Name: {name}</li>
    <li>Email: {email}</li>
    <li>IP: {ip}</li>
    <li>Browser: {browser} version {version}</li>
    <li>Browser Time: {browser_time}</li>
    <li>Server Time: {server_time}</li>
    <li>Platform: {platform}</li>
    <li>Window Resolution: {win_res}</li>
    <li>Subscription: {subscription}</li>
    </ul>
    """.format(
        subject=subject,
        feedback_source=feedback_source,
        message=message,
        name=printable_name,
        email=email,
        ip=request.remote_addr,
        platform=request.user_agent.platform  # type: ignore[attr-defined]
        if hasattr(request.user_agent, "platform")
        else "?",
        browser=request.user_agent.browser  # type: ignore[attr-defined]
        if hasattr(request.user_agent, "browser")
        else "?",
        version=request.user_agent.version  # type: ignore[attr-defined]
        if hasattr(request.user_agent, "version")
        else "?",
        browser_time=escape(request.form["browser_time"]),
        win_res=escape(request.form["win_res"]),
        subscription="Yes" if subscribe_me else "No",
        server_time=strftime("%a %B %d %Y %H:%M:%S GMT+0000", gmtime()),
    )
    secure_email = SecureEmail(current_app)
    secure_email.send(mailto, "Contact Form", "", content)
    session["last_message"] = int(time())

    if subscribe_me:
        if subscribe_newsletter(cursor, session, email, name):
            answer += " See you soon."
            mysql.commit()

    if is_detailed_feedback:
        session.pop("old_visit_id", None)
    return basic_json(True, answer)


@visitor_app.route("/create_password", methods=("POST",))
@visitor_app.route(
    "/create_password/<int:member_id>/<string:newsletter_id>/<string:one_time_password>",
    methods=("GET",),
)
def create_password(
    member_id: int = 0, newsletter_id: str = "", one_time_password: str = ""
) -> Any:
    """
    Create a password by visiting the URL (sent via e-mail by the administrator).
    The URL looks like ``/create_password/3/umA...V59I/Dscx...QaZ6WM` and the page is
    a form with ``member_id``, ``newsletter_id`` and ``one_time_password``
    in hidden fields so that the POST request is simply `/create_password`
    and everything is in the `request.form` dictionary.

    Raises:
        404: if the user is logged, or if ``member_id`` is not in the
            database or the couple ``newsletter_id`` and ``one_time_password``
            is incorrect.

    Args:
        member_id (int): Member ID according to the `members` table.
        newsletter_id (str): Newsletter ID according to the table.
        one_time_password (str): One time password temporary saved in the table.
    """
    if "access_level" in session:
        abort(404)
    if not member_id or not newsletter_id or not one_time_password:  # not in the URL
        # probably in the form
        try:
            member_id = int(request.form["member_id"])
            newsletter_id = escape(request.form["newsletter_id"])
            one_time_password = escape(request.form["one_time_password"])
        except KeyError:
            abort(404)

    cursor = mysql.cursor()
    cursor.execute(
        """SELECT member_id
        FROM members
        WHERE member_id={member_id}
        AND newsletter_id='{newsletter_id}'
        AND one_time_password='{one_time_password}'""".format(
            member_id=member_id,
            newsletter_id=newsletter_id,
            one_time_password=one_time_password,
        )
    )
    member_data = cursor.fetchone()  # pylint: disable=unused-variable
    if cursor.rowcount == 0:
        abort(404)
    if request.method == "POST":
        if not all(x in request.form for x in ["newPassword", "passwordCheck"]):
            flash("Missing data!", "danger")
            return render_template(
                "create_password.html",
                show_form=True,
                member_id=member_id,
                newsletter_id=newsletter_id,
                one_time_password=one_time_password,
            )
        new_password = escape(request.form["newPassword"])
        password_check = escape(request.form["passwordCheck"])
        if new_password == "" or password_check == "":
            flash("Passwords required!", "danger")
            return render_template(
                "create_password.html",
                show_form=True,
                member_id=member_id,
                newsletter_id=newsletter_id,
                one_time_password=one_time_password,
            )
        if new_password != password_check:
            flash("Passwords different!", "danger")
            return render_template(
                "create_password.html",
                show_form=True,
                member_id=member_id,
                newsletter_id=newsletter_id,
                one_time_password=one_time_password,
            )
        add_audit_log(member_id, request.remote_addr, "password_reset")
        password = werkzeug.security.generate_password_hash(
            new_password, "pbkdf2:sha512:50000"
        )
        cursor.execute(
            """UPDATE members
            SET password='{password}', one_time_password=NULL
            WHERE member_id={member_id}""".format(
                password=password, member_id=member_id
            )
        )
        mysql.commit()
        flash("Password successfully created!", "success")
        return render_template(
            "create_password.html",
            show_form=False,
        )
    return render_template(
        "create_password.html",
        show_form=True,
        member_id=member_id,
        newsletter_id=newsletter_id,
        one_time_password=one_time_password,
    )


@visitor_app.route("/change_email", methods=("POST", "GET"))
@visitor_app.route(
    "/change_email/<int:member_id>/<string:hashed_url_email>", methods=("GET",)
)
def change_email(member_id: int = 0, hashed_url_email: str = "") -> Any:
    """
    The steps to update a user email address are:

    1) The user fills in the form with his password and his new email address,
    2) Once submitted, fields as well as the member ID are checked,
    3) If the new email address does not exist in the database an email is sent to it,
    4) The user checks his new mailbox and follow the special link,
    5) Loading that link will actually update the user email address and the session data.

    Notes:
        * The email contains the old email address in order to disclose the user to the new mailbox,
        * The special link includes the member ID and the new email address (hashed and salted),
        * The user can sign in with his old email address until the new one is approved,
        * The user has to be connected during the process,
        * The process does not disconnect the user and finally update the session data,
        * The email won't be sent multiple times during the process.

    Raises:
        404: if the member is not logged or if the special link is bad.

    Args:
        member_id (int): Member ID according to the `members` table.
        hashed_url_email (str): The new email address hashed and salted with a
                                secret key so no one could guess.
    """
    if "member_id" not in session:
        abort(404)
    if request.method == "POST":
        if not all(x in request.form for x in ["currentPassword", "newEmailAddress"]):
            flash("Missing data!", "danger")
            return render_template(
                "change_email_address.html",
                show_form=True,
            )
        current_password = escape(request.form["currentPassword"])
        new_email_address = remove_whitespaces(escape(request.form["newEmailAddress"]))
        member_id = int(session["member_id"])

        # check credentials:
        cursor = mysql.cursor()
        cursor.execute(
            """SELECT password, email, username, future_email
            FROM members
            WHERE member_id={member_id}""".format(
                member_id=member_id
            )
        )
        data = cursor.fetchone()
        if cursor.rowcount == 0:
            flash("Invalid request!", "danger")
            return render_template(
                "change_email_address.html",
                show_form=True,
            )
        if data[3] == new_email_address:
            flash("Email already sent to the new email address!", "danger")
            return render_template(
                "change_email_address.html",
                show_form=True,
            )
        if not werkzeug.security.check_password_hash(data[0], current_password):
            flash("Wrong password!", "danger")
            return render_template(
                "change_email_address.html",
                show_form=True,
            )

        # check if the new email address is valid and not already in the database:
        username = data[2]
        old_email_address = data[1]
        if old_email_address == new_email_address:
            flash("The new email has to be new!", "danger")
            return render_template(
                "change_email_address.html",
                show_form=True,
            )
        cursor.execute(
            """SELECT email
            FROM members
            WHERE email='{email}'""".format(
                email=new_email_address
            )
        )
        data = cursor.fetchone()
        if (not email_is_valid(new_email_address)) or cursor.rowcount > 0:
            flash("Invalid email!", "danger")
            return render_template(
                "change_email_address.html",
                show_form=True,
            )

        # send the special link to the new email address:
        welcome = "Hi" + ((" " + username + "!") if username else "!")
        hashed_email = werkzeug.security.pbkdf2_hex(
            new_email_address, current_app.config["RANDOM_SALT"], keylen=21
        )
        url_update_email_address = (
            request.host_url + "change_email/" + str(member_id) + "/" + hashed_email
        )
        secure_email = SecureEmail(current_app)
        text = render_template(
            "email_update_email_address.txt",
            welcome=welcome,
            old_email_address=old_email_address,
            new_email_address=new_email_address,
            url_update_email_address=url_update_email_address,
        )
        html = render_template(
            "email_update_email_address.html",
            welcome=welcome,
            old_email_address=old_email_address,
            new_email_address=new_email_address,
            url_update_email_address=url_update_email_address,
        )
        secure_email.send(new_email_address, "Update Your Email Address", text, html)

        # set the new email address without changing the current one:
        cursor.execute(
            """UPDATE members SET future_email='{email}'
            WHERE member_id={member_id}""".format(
                email=new_email_address, member_id=member_id
            )
        )
        mysql.commit()
        flash(
            "A link has been sent to your new email address to confirm the update.",
            "success",
        )
        return render_template(
            "change_email_address.html",
            show_form=False,
        )
    if hashed_url_email:  # try changing the email address:
        if session["member_id"] != member_id:  # bad member connected or bad link
            abort(404)
        hashed_url_email = escape(hashed_url_email)
        cursor = mysql.cursor()
        cursor.execute(
            """SELECT future_email
            FROM members
            WHERE member_id={member_id}""".format(
                member_id=member_id
            )
        )
        data = cursor.fetchone()
        if cursor.rowcount == 0:  # bad link
            abort(404)
        db_email = data[0]
        if not db_email:
            abort(404)
        hashed_db_email = werkzeug.security.pbkdf2_hex(
            db_email, current_app.config["RANDOM_SALT"], keylen=21
        )
        if hashed_db_email != hashed_url_email:  # bad link
            abort(404)
        add_audit_log(member_id, request.remote_addr, "email_changed")
        cursor.execute(
            """UPDATE members SET email='{email}', future_email=NULL
            WHERE member_id={member_id}""".format(
                email=db_email, member_id=member_id
            )
        )
        mysql.commit()
        session["email"] = db_email
        flash(
            "Email address updated! Please use your new email address the next time you sign in.",
            "success",
        )
        return render_template(
            "change_email_address.html",
            show_form=False,
        )
    return render_template(
        "change_email_address.html",
        show_form=True,
    )


@visitor_app.route("/change_password", methods=("POST", "GET"))
def change_password() -> Any:
    """
    Change password.

    Raises:
        404: if the member is not logged.
    """
    if "member_id" not in session:
        abort(404)
    if request.method == "POST":
        if not all(
            x in request.form
            for x in ["currentPassword", "newPassword", "passwordCheck"]
        ):
            flash("Missing data!", "danger")
            return render_template(
                "change_password.html",
                show_form=True,
            )
        current_password = escape(request.form["currentPassword"])
        new_password = escape(request.form["newPassword"])
        password_check = escape(request.form["passwordCheck"])
        if current_password == "" or new_password == "" or password_check == "":
            flash("Passwords required!", "danger")
            return render_template(
                "change_password.html",
                show_form=True,
            )
        if new_password != password_check:
            flash("Passwords different!", "danger")
            return render_template(
                "change_password.html",
                show_form=True,
            )
        member_id = int(session["member_id"])

        # check credentials:
        cursor = mysql.cursor()
        cursor.execute(
            """SELECT password
            FROM members
            WHERE member_id={member_id}""".format(
                member_id=member_id
            )
        )
        data = cursor.fetchone()
        if cursor.rowcount == 0 or not werkzeug.security.check_password_hash(
            data[0], current_password
        ):
            flash("Wrong password!", "danger")
            return render_template(
                "change_password.html",
                show_form=True,
            )

        # update password:
        add_audit_log(member_id, request.remote_addr, "password_changed")
        password = werkzeug.security.generate_password_hash(
            new_password, "pbkdf2:sha512:50000"
        )
        cursor.execute(
            """UPDATE members SET password='{password}'
            WHERE member_id={member_id}""".format(
                password=password, member_id=member_id
            )
        )
        mysql.commit()
        flash("Password successfully changed!", "success")
        return render_template(
            "change_password.html",
            show_form=False,
        )
    return render_template(
        "change_password.html",
        show_form=True,
    )


@visitor_app.route("/subscribe", methods=("POST",))
def subscribe_newsletter_form() -> FlaskResponse:
    """
    Subscribe the visitor to the newsletter members list.
    The feedback is intentionally lacking to avoid data disclosure.
    """
    if "email" not in request.form:
        return basic_json(False, "Missing data!")
    email = remove_whitespaces(escape(request.form["email"]))
    if not email_is_valid(email):
        return basic_json(False, "Invalid email!")
    if subscribe_newsletter(mysql.cursor(), session, email):
        mysql.commit()
    return basic_json(True, "Thank you!")


@visitor_app.route("/unsubscribe/<int:member_id>/<string:newsletter_id>")
def unsubscribe_from_newsletter(member_id: int, newsletter_id: str) -> Any:
    """
    Unsubscribe ``member_id`` from the newsletter.

    Raises:
        404: if ``member_id`` is not in the database.

    Args:
        member_id (int): Member ID according to the `members` table.
        newsletter_id (str): Newsletter ID according to the table.
    """
    cursor = mysql.cursor()
    cursor.execute(
        """SELECT username
        FROM members
        WHERE member_id={member_id}
        AND newsletter_id='{newsletter_id}'""".format(
            member_id=member_id, newsletter_id=escape(newsletter_id)
        )
    )
    member_data = cursor.fetchone()
    if cursor.rowcount == 0:
        abort(404)
    cursor.execute(
        """DELETE FROM members WHERE member_id={member_id}""".format(
            member_id=member_id
        )
    )
    mysql.commit()

    if "member_id" in session:  # disconnect
        if member_id == int(session["member_id"]):
            session.pop("member_id", None)
            if "access_level" in session:
                session.pop("access_level", None)
            if "username" in session:
                session.pop("username", None)
            if "email" in session:
                session.pop("email", None)

    username = member_data[0]
    if username is None or username == "":
        welcome = ""
    else:
        welcome = " " + username
    flash(
        "Hi"
        + welcome
        + "! You successfully unsubscribed from the newsletter."
        + " If you were a member, you lost your account!"
    )
    # render instead of redirect:
    # https://github.com/pallets/flask/issues/1168#issuecomment-314146774
    return render_template("gallery.html")


@visitor_app.route("/photos", methods=("POST",))
@same_site
def fetch_photos() -> FlaskResponse:
    """
    XHR procedure sending photos metadata according to the access level.
    Photo title and description are empty if the user is not allowed to read them.
    Notice that the `time` field (`date_taken` in the database) is formatted server side.

    Raises:
        404: if the request is not POST.
    """
    offset = int(request.form["offset"])
    total = int(request.form["total"])
    access_level = actual_access_level()
    include_info = access_level >= current_app.config["ACCESS_LEVEL_READ_INFO"]
    cursor = mysql.cursor()
    cursor.execute(
        """SELECT photo_id, thumbnail_src, photo_m_src,
        photo_m_width, photo_m_height, photo_l_src, photo_l_width,
        photo_l_height, focal_length_35mm, exposure_time, f_number, iso,
        date_taken, {include_info}
        FROM gallery
        WHERE access_level <= {access_level}
        ORDER BY position DESC
        LIMIT {offset},{total}""".format(
            offset=offset,
            total=total,
            access_level=access_level,
            include_info="title, description"
            if include_info
            else "'', '[undisclosed]'",
        )
    )
    data = cursor.fetchall()
    formatted_data = []
    for row in data:
        photo = dict(
            zip(
                [
                    "id",
                    "thumbnail",
                    "photo_m",
                    "photo_m_w",
                    "photo_m_h",
                    "photo_l",
                    "photo_l_w",
                    "photo_l_h",
                    "focal_length_35mm",
                    "exposure_time",
                    "f_number",
                    "iso",
                    "time",
                    "title",
                    "description",
                ],
                row,
            )
        )
        if photo["time"] is not None:
            photo["time"] = friendly_datetime(photo["time"])
        formatted_data.append(photo)
    return jsonify(formatted_data)


@visitor_app.route("/share_emotion_photo", methods=("POST",))
def share_emotion_photo() -> FlaskResponse:
    """
    XHR procedure updating the visitor log according to his emotion.

    Raises:
        404: if the request is not POST.
    """
    if "emotion" not in request.form:
        return basic_json(False, "Emotion required!")
    emotion = escape(request.form["emotion"])
    if emotion not in current_app.config["EMOTIONS"]:
        return basic_json(False, "Invalid emotion!")
    if "last_visit_photo_id" not in session:
        return basic_json(False, "Illogic request!")
    visit_id = int(session["last_visit_photo_id"])
    cursor = mysql.cursor()
    cursor.execute(
        """UPDATE visits
        SET emotion='{emotion}'
        WHERE visit_id={visit_id}
        AND element_type='gallery'""".format(
            emotion=emotion, visit_id=visit_id
        )
    )
    mysql.commit()
    session["old_visit_id"] = visit_id
    session.pop("last_visit_photo_id", None)  # block multi-request
    info = "Thank you"
    if "username" in session:
        info += " " + session["username"] + ", you're awesome"
    info += "!"
    return basic_json(True, info)


def generic_log(
    element_type: str, element_id: int, emotion: str = "neutral"
) -> FlaskResponse:
    """
    Handle the visitor ID, and update the database and the cookies
    which are returned with an empty response.

    Args:
        element_type (str): 'gallery' or 'shelf'.
        element_id (int): The book or photo ID.
        emotion (str): The user emotion (default is 'neutral').

    Returns:
        FlaskResponse: An empty response with the updated cookies.
    """
    # manage visitor identifier
    raw_cookie = request.cookies.get("visitor_data")

    def bake():
        # MySQL INT is 32-bit signed. Keep positive, so the 32nd bit is 0
        return JSONSecureCookie(
            {"id": secrets.randbits(31)}, current_app.config["COOKIE_SECRET_KEY"]
        )

    if not raw_cookie:  # create a new visitor identifier
        visitor_data = bake()
    else:
        visitor_data = JSONSecureCookie.unserialize(
            raw_cookie, current_app.config["COOKIE_SECRET_KEY"]
        )
        if "id" not in visitor_data:  # cookie compromised, bake a new one
            visitor_data = bake()
    visitor_id = int(visitor_data["id"])

    # visitor's decision to accept or deny long-term cookies
    cookies_forever = escape(request.cookies.get("cookies_forever", "false")) == "true"

    # add a new entry into the database and update cookies
    cursor = mysql.cursor()
    cursor.execute(
        """INSERT INTO visits(element_id, element_type, ip,
        visitor_id, member_id, emotion)
        VALUES ({element_id}, '{element_type}', INET6_ATON('{ip}'),
        {visitor_id}, {member_id}, '{emotion}')""".format(
            element_id=element_id,
            element_type=element_type,
            ip=anonymize_ip(request.remote_addr),
            visitor_id=visitor_id,
            member_id=int(session["member_id"]) if "member_id" in session else "NULL",
            emotion=emotion,
        )
    )
    mysql.commit()
    if element_type == "shelf":
        session["old_visit_id"] = cursor.lastrowid
        session["last_visited_book_id"] = element_id
    elif element_type == "gallery":
        session["last_visit_photo_id"] = cursor.lastrowid
    resp = make_response("")
    resp.set_cookie(
        "visitor_data",
        visitor_data.serialize(),
        httponly=True,
        samesite="Strict",
        secure=not current_app.config["DEBUG"],
        max_age=(60 * 60 * 24 * 365) if cookies_forever else None,
        expires=datetime.datetime.fromtimestamp(2 ** 31 - 1)
        if cookies_forever
        else None,
    )
    return resp


@visitor_app.route("/share_emotion_book", methods=("POST",))
def share_emotion_book() -> FlaskResponse:
    """
    XHR procedure adding a new entry into the visitor log. The emotion is
    neutral if the user has open a book or it is a like if the user clicked
    on the "Like" button.

    Raises:
        404: if the request is not POST.
    """
    if "emotion" not in request.form:
        return basic_json(False, "Emotion required!")
    emotion = escape(request.form["emotion"])
    if emotion not in current_app.config["EMOTIONS"]:
        return basic_json(False, "Invalid emotion!")

    # check book id
    json_error = "Bad request, incorrect identifier!"
    if "book_id" not in request.form:
        return basic_json(False, json_error)
    book_id = int(request.form["book_id"])
    if book_id < 1:
        return basic_json(False, json_error)
    cursor = mysql.cursor()
    cursor.execute(
        """SELECT book_id
        FROM shelf
        WHERE book_id={id}
        AND access_level <= {access_level}""".format(
            id=book_id, access_level=actual_access_level()
        )
    )
    cursor.fetchone()
    if cursor.rowcount == 0:
        return basic_json(False, json_error)
    return generic_log("shelf", book_id, emotion)


@visitor_app.route("/login", methods=("POST", "GET"))
def login(result: str = "", status: bool = True) -> Any:
    """
    Log in a user or logout if he is already logged in.
    Arguments are reset in POST requests and could be used in GET requests.

    Args:
        result (str): Message that would be displayed in the login.html template.
        status (boolean): False for error, True for success or info.
    """
    if request.method == "POST":
        if "last_attempt" in session and (
            int(session["last_attempt"]) + current_app.config["REQUIRED_TIME_GAP"]
        ) > int(time()):
            result = "Too many attempts!"
            status = False
        else:
            session["last_attempt"] = int(time())
            if not all(
                x in request.form
                for x in [
                    "email",
                    "password",
                    "captcha",
                    "privacyPolicy",
                    "copyrightNotice",
                ]
            ):
                result = "Missing data!"
                status = False
            elif not Captcha(current_app).check(
                escape(request.form["captcha"])
            ):  # pragma: no cover
                result = "Invalid CAPTCHA, try again!"
                status = False
            else:
                email = remove_whitespaces(escape(request.form["email"]))
                if not email_is_valid(email):
                    result = "Bad email address format!"
                    status = False
                else:
                    password = escape(request.form["password"])
                    cursor = mysql.cursor()
                    cursor.execute(
                        """SELECT password, access_level,
                        member_id, username, newsletter_id, one_time_password
                        FROM members
                        WHERE email='{email}'""".format(
                            email=email
                        )
                    )
                    data = cursor.fetchone()
                    if (
                        cursor.rowcount == 0
                        or data[0] == ""
                        or not werkzeug.security.check_password_hash(data[0], password)
                    ):
                        result = "Wrong email address or password!"
                        status = False
                    else:  # success
                        # allow consecutive successful connections:
                        session.pop("last_attempt", None)

                        # log before to give access:
                        add_audit_log(data[2], request.remote_addr)

                        if data[5]:  # unset the password reset procedure
                            cursor.execute(
                                """UPDATE members SET one_time_password=NULL
                                WHERE member_id={member_id}""".format(
                                    member_id=data[2]
                                )
                            )

                        mysql.commit()

                        session["username"] = data[3]
                        session["access_level"] = data[1]
                        session["member_id"] = data[2]
                        if data[3]:
                            session["email"] = email
                        if data[4]:
                            session["subscribed"] = True
                        flash(
                            "Hi"
                            + ((" " + data[3] + "!") if data[3] else "!")
                            + " You were successfully logged in."
                        )
                        return redirect("/index")
    if "access_level" in session:  # logout
        session.pop("access_level", None)
        session.pop("username", None)
        session.pop("member_id", None)
        session.pop("email", None)
        result = "You are logged out."
        status = True
    return render_template(
        "login.html",
        result=result,
        status=status,
        current_year=current_year(),
    )


@visitor_app.route("/reset_password", methods=("POST", "GET"))
def reset_password(result: str = "", status: bool = True) -> Any:
    """
    Send an email to reset the password. The email is only sent if the
    user does not have a one time password, which is generated and put
    in the email. If the user can log in with its current password, the
    one time password is unset.
    For security reason, admin password cannot be reset.
    """
    if request.method == "POST":
        if "last_attempt" in session and (
            int(session["last_attempt"]) + current_app.config["REQUIRED_TIME_GAP"]
        ) > int(time()):
            result = "Too many attempts!"
            status = False
        else:
            session["last_attempt"] = int(time())
            if not all(x in request.form for x in ["email", "captcha"]):
                result = "Missing data!"
                status = False
            elif not Captcha(current_app).check(
                escape(request.form["captcha"])
            ):  # pragma: no cover
                result = "Invalid CAPTCHA, try again!"
                status = False
            else:
                email = remove_whitespaces(escape(request.form["email"]))
                if not email_is_valid(email):
                    result = "Bad email address format!"
                    status = False
                else:
                    cursor = mysql.cursor()
                    cursor.execute(
                        """SELECT member_id, username, newsletter_id
                        FROM members
                        WHERE email='{email}'
                        AND access_level<255
                        AND newsletter_id IS NOT NULL
                        AND password IS NOT NULL
                        AND one_time_password IS NULL""".format(
                            email=email
                        )
                    )
                    data = cursor.fetchone()
                    if cursor.rowcount > 0:
                        member_id = data[0]
                        username = data[1]
                        newsletter_id = data[2]
                        one_time_password = generate_newsletter_id()
                        cursor.execute(
                            """UPDATE members
                            SET one_time_password='{one_time_password}'
                            WHERE member_id={member_id}""".format(
                                one_time_password=one_time_password, member_id=member_id
                            )
                        )
                        mysql.commit()
                        welcome = "Hi" + ((" " + username + "!") if username else "!")
                        subject = "Reset Your Password"
                        url_create_password = (
                            request.host_url
                            + "create_password/"
                            + str(member_id)
                            + "/"
                            + newsletter_id
                            + "/"
                            + one_time_password
                        )
                        url_unsubscribe = (
                            request.host_url
                            + "unsubscribe/"
                            + str(member_id)
                            + "/"
                            + newsletter_id
                        )
                        secure_email = SecureEmail(current_app)
                        text = render_template(
                            "email_password_reset.txt",
                            welcome=welcome,
                            subject=subject,
                            url_unsubscribe=url_unsubscribe,
                            url_create_password=url_create_password,
                        )
                        html = render_template(
                            "email_password_reset.html",
                            welcome=welcome,
                            subject=subject,
                            url_unsubscribe=url_unsubscribe,
                            url_create_password=url_create_password,
                        )
                        secure_email.send(email, subject, text, html)
                    flash(
                        "If you are a member, a password reset link "
                        + "has been sent to your email address: "
                        + email
                    )
                    return redirect("/index")
    return render_template(
        "reset_password.html",
        result=result,
        status=status,
        current_year=current_year(),
    )


@visitor_app.route("/log_visit_photo", methods=("POST",))
def log_visit_photo() -> Any:
    """
    XHR procedure logging visits. The `visitor_id` cookie is used but not
    required by ``share_emotion_photo()`` which uses the `last_visit_photo_id`
    session. The `visitor_id` cookie is refreshed at every call and will be
    persistent to the browser if the cookie `cookies_forever` exists and is set
    to "true".

    Raises:
        404: if the request is not POST.
    """
    # check photo id
    if "photo_id" not in request.form:
        return "Bad request, missing identifier!"
    photo_id = int(request.form["photo_id"])
    json_error = "Bad request, incorrect identifier!"
    if photo_id < 1:
        return json_error
    cursor = mysql.cursor()
    cursor.execute(
        """SELECT photo_id
        FROM gallery
        WHERE photo_id={id}
        AND access_level <= {access_level}""".format(
            id=photo_id, access_level=actual_access_level()
        )
    )
    cursor.fetchone()
    if cursor.rowcount == 0:
        return json_error
    return generic_log("gallery", photo_id)


@visitor_app.route("/captcha.png")
def create_captcha() -> FlaskResponse:
    """ Create a CAPTCHA and return it. """
    captcha = Captcha(current_app)
    captcha.create_image()
    return captcha.to_file()


@visitor_app.route("/")
@visitor_app.route("/index")
def index() -> Any:
    """ The gallery. """
    cursor = mysql.cursor()
    cursor.execute(
        """SELECT photo_id, thumbnail_src
        FROM gallery
        WHERE access_level = 0
        ORDER BY position
        DESC
        LIMIT 1"""
    )
    data = cursor.fetchone()
    if cursor.rowcount:
        thumbnail_networks = request.url_root + "photos/" + str(data[0]) + "/" + data[1]
    else:
        thumbnail_networks = None
    return render_template(
        "gallery.html",
        is_logged="access_level" in session,
        total_subscribers=total_subscribers(cursor),
        thumbnail_networks=thumbnail_networks,
    )


@visitor_app.route("/logout")
def logout() -> Any:
    """ The login page will log out the user. """
    return redirect("/login")
