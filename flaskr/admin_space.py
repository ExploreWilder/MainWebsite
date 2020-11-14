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
Administration interface.
"""

from .db import get_db
from .secure_email import SecureEmail
from .utils import *
from .visitor_space import fetch_audit_log

admin_app = Blueprint("admin_app", __name__)
mysql = LocalProxy(get_db)


def restricted_admin(view: Any) -> Any:
    """
    View decorator that redirects anonymous users to the 404-error page.
    This must be before any procedure in this file even if ``is_admin()`` is used.
    That is to be sure that no one function has been missed.
    Also, do not forget to update the unit tests.
    """

    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if not is_admin():
            abort(404)
        return view(**kwargs)

    return wrapped_view


@admin_app.route("/members/revoke", methods=("POST",))
@restricted_admin
def revoke_member() -> FlaskResponse:
    """
    XHR request. Set to 0 the access level of the chosen user, he could still log in.

    Raises:
        404: if the user is not admin or the request is not POST.
    """
    if not is_admin():
        abort(404)  # pragma: no cover
    if "member_id" not in request.form:
        return basic_json(False, "Member identifier required!")
    cursor = mysql.cursor()
    member_id = int(request.form["member_id"])
    try:
        access_level = get_access_level_from_id(member_id, cursor)
    except ValueError as error:
        return basic_json(False, repr(error))
    if access_level in (255, 0):  # admin or already revoked
        return basic_json(False, "Member cannot be revoked!")
    cursor.execute(
        """UPDATE members SET access_level=0
        WHERE member_id={id}""".format(
            id=member_id
        )
    )
    mysql.commit()
    return basic_json(True, "Member revoked!")


@admin_app.route("/members/delete", methods=("POST",))
@restricted_admin
def delete_member() -> FlaskResponse:
    """
    XHR request. Delete a user from the database.

    Raises:
        404: if the user is not admin or the request is not POST.
    """
    if not is_admin():
        abort(404)  # pragma: no cover
    if "member_id" not in request.form:
        return basic_json(False, "Member identifier required!")
    cursor = mysql.cursor()
    member_id = int(request.form["member_id"])
    try:
        access_level = get_access_level_from_id(member_id, cursor)
    except ValueError as error:
        return basic_json(False, repr(error))
    if access_level == 255:
        return basic_json(False, "Administrator cannot be deleted!")
    cursor.execute(
        """DELETE FROM members
        WHERE member_id={id}""".format(
            id=member_id
        )
    )
    mysql.commit()
    return basic_json(True, "Member deleted!")


@admin_app.route("/members/change_access_level", methods=("POST",))
@restricted_admin
def change_access_level() -> FlaskResponse:
    """
    XHR request. Change the access level of a member.

    Raises:
        404: if the user is not admin or the request is not POST.
    """
    if not is_admin():
        abort(404)  # pragma: no cover
    if not all(x in request.form for x in ["member_id", "new_access_level"]):
        return basic_json(False, "Missing data!")
    new_access_level = int(request.form["new_access_level"])
    if not check_access_level_range(new_access_level):
        return basic_json(False, "Invalid access level!")
    member_id = int(request.form["member_id"])
    cursor = mysql.cursor()
    cursor.execute(
        """SELECT access_level
        FROM members
        WHERE member_id={member_id}""".format(
            member_id=member_id
        )
    )
    data = cursor.fetchone()
    if cursor.rowcount == 0:
        return basic_json(False, "Invalid member ID!")
    if data[0] == 255:
        return basic_json(False, "Change not allowed!")

    cursor.execute(
        """UPDATE members SET access_level={access_level}
        WHERE member_id={member_id}""".format(
            access_level=new_access_level, member_id=member_id
        )
    )
    mysql.commit()
    return basic_json(True, "Access level successfully changed!")


@admin_app.route("/members/list")
@restricted_admin
def members() -> Any:
    """
    List all members with information about the last successful connection.

    Raises:
        404: if the user is not admin.
    """
    if not is_admin():
        abort(404)  # pragma: no cover
    cursor = mysql.cursor()
    cursor.execute(
        """SELECT member_id, username, email, access_level,
        newsletter_id, password
        FROM members
        ORDER BY member_id DESC"""
    )
    data_members = [
        list(member) + [fetch_audit_log(member[0], "logged_in")]
        for member in cursor.fetchall()
    ]
    cursor.execute(
        """SELECT COUNT(*) FROM members
        WHERE (newsletter_id <> '' AND newsletter_id IS NOT NULL)
        AND (email <> '' AND email IS NOT NULL)"""
    )
    total_newsletter = cursor.fetchone()[0]
    return render_template(
        "members.html",
        members=data_members,
        access_level_read_info=current_app.config["ACCESS_LEVEL_READ_INFO"],
        total_newsletter=total_newsletter,
        is_prod=not current_app.config["DEBUG"],
    )


@admin_app.route("/members/send_password_creation", methods=("POST",))
@restricted_admin
def send_password_creation() -> FlaskResponse:
    """
    Send an e-mail to the member to create a password.

    Raises:
        404: if the user is not admin.
    """
    if not is_admin():
        abort(404)  # pragma: no cover
    if "member_id" not in request.form:
        return basic_json(False, "Missing data!")
    member_id = int(request.form["member_id"])
    cursor = mysql.cursor()
    cursor.execute(
        """SELECT newsletter_id, username, email
        FROM members
        WHERE member_id={member_id}
        AND (password='' OR password IS NULL)
        AND (newsletter_id<>'' AND newsletter_id IS NOT NULL)
        AND (email<>'' AND email IS NOT NULL)""".format(
            member_id=member_id
        )
    )
    data = cursor.fetchone()
    if cursor.rowcount == 0:
        return basic_json(False, "Invalid member!")

    # create the one time password:
    one_time_password = generate_newsletter_id()
    cursor.execute(
        """UPDATE members SET one_time_password='{one_time_password}'
        WHERE member_id={member_id}""".format(
            one_time_password=one_time_password, member_id=member_id
        )
    )
    mysql.commit()

    # send e-mail:
    username = data[1]
    newsletter_id = data[0]
    email = data[2]
    subject = "Create Your Password"
    url_unsubscribe = (
        request.host_url + "unsubscribe/" + str(member_id) + "/" + newsletter_id
    )
    url_create_password = (
        request.host_url
        + "create_password/"
        + str(member_id)
        + "/"
        + newsletter_id
        + "/"
        + one_time_password
    )
    welcome = "Hi" + ("!" if (not username) else (" " + username + "!"))
    secure_email = SecureEmail(current_app)
    text = render_template(
        "email_password_creation.txt",
        welcome=welcome,
        subject=subject,
        url_unsubscribe=url_unsubscribe,
        url_create_password=url_create_password,
    )
    html = render_template(
        "email_password_creation.html",
        welcome=welcome,
        subject=subject,
        url_unsubscribe=url_unsubscribe,
        url_create_password=url_create_password,
    )
    secure_email.send(email, subject, text, html)
    return basic_json(True, "E-mail sent to the member!")


@admin_app.route("/members/send_newsletter", methods=("POST",))
@restricted_admin
def send_newsletter() -> FlaskResponse:
    """
    Send an e-mail to the newsletter subscribers.

    Raises:
        404: if the user is not admin.
    """
    if not is_admin():
        abort(404)  # pragma: no cover
    if not all(x in request.form for x in ["subject", "news"]):
        return basic_json(False, "Missing data!")
    short_subject = escape(request.form["subject"].strip())
    subject = current_app.config["BRAND_NAME"] + " News: " + short_subject
    if short_subject == "":
        return basic_json(False, "Subject required!")
    news = escape(request.form["news"].strip())
    if news == "":
        return basic_json(False, "Please write something!")
    news_text = news
    news_html = markdown.Markdown(extensions=current_app.config["MD_EXT"]).convert(news)

    cursor = mysql.cursor()
    cursor.execute(
        """SELECT newsletter_id, username, email, member_id
        FROM members
        WHERE (newsletter_id<>'' AND newsletter_id IS NOT NULL)
        AND (email<>'' AND email IS NOT NULL)"""
    )
    data = cursor.fetchall()
    total_emails_sent = 0

    secure_email = SecureEmail(current_app)
    for member in data:
        username = member[1]
        newsletter_id = member[0]
        email = member[2]
        member_id = member[3]
        url_unsubscribe = (
            request.host_url + "unsubscribe/" + str(member_id) + "/" + newsletter_id
        )
        text = render_template(
            "email_newsletter.txt",
            username=username,
            news=news_text,
            subject=short_subject,
            url_unsubscribe=url_unsubscribe,
        )
        html = render_template(
            "email_newsletter.html",
            username=username,
            news=news_html,
            subject=short_subject,
            url_unsubscribe=url_unsubscribe,
        )
        secure_email.send(email, subject, text, html)
        total_emails_sent += 1
    return basic_json(
        True, "News sent to the " + str(total_emails_sent) + " subscriber(s)!"
    )


@admin_app.route("/photos/add/form")
@restricted_admin
def add_photo() -> Any:
    """
    Form to submit a photo.

    Raises:
        404: if the user is not admin.
    """
    if not is_admin():
        abort(404)  # pragma: no cover
    return render_template("add_photo.html", is_prod=not current_app.config["DEBUG"])


@admin_app.route("/books/add/form")
@restricted_admin
def add_book() -> Any:
    """
    Form to submit a book.

    Raises:
        404: if the user is not admin.
    """
    if not is_admin():
        abort(404)  # pragma: no cover
    return render_template("add_book.html", is_prod=not current_app.config["DEBUG"])


@admin_app.route("/photos/add/request", methods=("POST",))
@restricted_admin
def xhr_add_photo() -> FlaskResponse:
    """
    XHR procedure to add a new photo into the server.
    New files are created and saved. A new row into the `gallery` table is added.

    Raises:
        404: if the user is not admin or the request is not POST.
    """
    if not is_admin():
        abort(404)  # pragma: no cover
    if not all(
        x in request.form
        for x in ["add-photo-access-level", "add-photo-title", "add-photo-description"]
    ):
        return basic_json(False, "Missing data!")
    access_level = int(request.form["add-photo-access-level"])
    if not check_access_level_range(access_level):
        return basic_json(False, "Invalid access level!")
    if "add-photo-file" not in request.files:
        return basic_json(False, "No file part!")
    file = request.files["add-photo-file"]
    if file.filename == "":
        return basic_json(False, "No selected file!")
    raw_filename_ext = file_extension(file.filename)
    if not raw_filename_ext:
        return basic_json(False, "Wrong file extension!")
    raw_filename = hashlib.sha1(file.read()).hexdigest() + "." + raw_filename_ext
    cursor = mysql.cursor()
    cursor.execute(
        """SELECT photo_id
        FROM gallery
        WHERE raw_src='{raw}'""".format(
            raw=raw_filename
        )
    )
    data = cursor.fetchone()  # pylint: disable=unused-variable
    if not cursor.rowcount == 0:  # the file name must be unique
        return basic_json(False, "Photo already in the database!")
    raw_path = os.path.join(current_app.config["GALLERY_FOLDER"], raw_filename)
    if Path(raw_path).is_file():
        return basic_json(
            False,
            "File '" + raw_filename + "' already existing but missing in the database!",
        )
    file.seek(0)  # reset the pointer moved during the hashing
    file.save(raw_path)
    try:
        image = Image.open(raw_path)
        image = image.convert("RGB")
        image_w = image.size[0]
        image_h = image.size[1]
        raw_size = image.size
        if image_w > image_h:
            thumbnail_h = float(current_app.config["THUMBNAIL_SIZE"])
            thumbnail_w = thumbnail_h * float(image_w) / float(image_h)
            offset_x = (thumbnail_w - thumbnail_h) / 2.0
            thumbnail_crop = (
                int(offset_x),
                0,
                int(thumbnail_h + offset_x),
                current_app.config["THUMBNAIL_SIZE"],
            )
        else:
            thumbnail_w = float(current_app.config["THUMBNAIL_SIZE"])
            thumbnail_h = thumbnail_w * float(image_h) / float(image_w)
            offset_y = (thumbnail_h - thumbnail_w) / 2.0
            thumbnail_crop = (
                0,
                int(offset_y),
                current_app.config["THUMBNAIL_SIZE"],
                int(thumbnail_w + offset_y),
            )
        image = image.resize((int(thumbnail_w), int(thumbnail_h)), Image.ANTIALIAS)
        image = image.crop(thumbnail_crop)
        thumbnail_filename = random_filename(
            current_app.config["THUMBNAIL_FILENAME_SIZE"]
        )
        image.save(
            os.path.join(current_app.config["GALLERY_FOLDER"], thumbnail_filename),
            "JPEG",
            quality=current_app.config["PHOTO_QUALITY"],
        )
        image.close()
    except IOError:  # pragma: no cover
        return basic_json(False, "Cannot create thumbnail!")
    try:
        photo_l_filename = create_and_save(
            raw_path,
            current_app.config["PHOTO_L_MAX_SIZE"],
            current_app.config["PHOTO_L_FILENAME_SIZE"],
            current_app.config["PHOTO_QUALITY"],
            current_app.config["GALLERY_FOLDER"],
        )
    except IOError:  # pragma: no cover
        return basic_json(False, "Cannot create the large photo!")
    try:
        photo_m_filename = create_and_save(
            raw_path,
            current_app.config["PHOTO_M_MAX_SIZE"],
            current_app.config["PHOTO_M_FILENAME_SIZE"],
            current_app.config["PHOTO_QUALITY"],
            current_app.config["GALLERY_FOLDER"],
        )
    except IOError:  # pragma: no cover
        return basic_json(False, "Cannot create the medium photo!")
    try:
        photo_l_size = get_image_size(
            os.path.join(current_app.config["GALLERY_FOLDER"], photo_l_filename)
        )
        photo_m_size = get_image_size(
            os.path.join(current_app.config["GALLERY_FOLDER"], photo_m_filename)
        )
        image_exif = get_image_exif(raw_path)
    except IOError:  # pragma: no cover
        return basic_json(False, "Cannot get metadata!")
    position = "SELECT IF(COUNT(clone.photo_id), MAX(clone.position) + 1, 1) FROM gallery clone"
    cursor.execute(
        """INSERT INTO gallery(thumbnail_src, photo_l_src, photo_m_src,
        raw_src, title, description, access_level, position, photo_m_width,
        photo_m_height, photo_l_width, photo_l_height, raw_width, raw_height,
        date_taken, focal_length_35mm, exposure_time, f_number, iso)
        VALUES ('{thumbnail}', '{photo_l}', '{photo_m}', '{raw}', '{title}',
        '{description}', {access_level}, ({position}), {photo_m_width},
        {photo_m_height}, {photo_l_width}, {photo_l_height}, {raw_width},
        {raw_height}, {date_taken}, {focal_length_35mm}, {exposure_time},
        {f_number}, {iso})""".format(
            thumbnail=thumbnail_filename,
            photo_l=photo_l_filename,
            photo_m=photo_m_filename,
            raw=raw_filename,
            title=escape(request.form["add-photo-title"]),
            description=escape(request.form["add-photo-description"]),
            access_level=access_level,
            position=position,
            photo_m_width=photo_m_size[0],
            photo_m_height=photo_m_size[1],
            photo_l_width=photo_l_size[0],
            photo_l_height=photo_l_size[1],
            raw_width=raw_size[0],
            raw_height=raw_size[1],
            date_taken="'" + str(image_exif[0]) + "'"
            if not image_exif[0] is None
            else "NULL",
            focal_length_35mm=image_exif[1] if not image_exif[1] is None else "NULL",
            exposure_time="'" + image_exif[2] + "'"
            if not image_exif[2] is None
            else "NULL",
            f_number=image_exif[3] if not image_exif[3] is None else "NULL",
            iso=image_exif[4] if not image_exif[4] is None else "NULL",
        )
    )
    mysql.commit()
    return basic_json(True, "Photo successfully added to the gallery!")


@admin_app.route("/books/add/request", methods=("POST",))
@restricted_admin
def xhr_add_book() -> FlaskResponse:
    """
    XHR procedure to add a new book into the server.
    In case of success, the book is saved in the created directory and a new row
    is added into the `shelf` table.

    Raises:
        404: if the user is not admin or the request is not POST.
    """
    if not is_admin():
        abort(404)  # pragma: no cover
    if not all(
        x in request.form
        for x in ["add-book-access-level", "add-book-title", "add-book-description-md"]
    ):
        return basic_json(False, "Missing data!")
    access_level = int(request.form["add-book-access-level"])
    if not check_access_level_range(access_level):
        return basic_json(False, "Access level invalid!")
    book_title = escape(request.form["add-book-title"].strip())
    if not book_title:
        return basic_json(False, "Missing title!")
    book_url = secure_filename(book_title_to_url(book_title))
    book_description_md = escape(request.form["add-book-description-md"].strip())
    if not book_description_md:
        return basic_json(False, "Missing description!")
    book_description_html = markdown.Markdown(
        extensions=current_app.config["MD_EXT"]
    ).convert(book_description_md)
    book_dir_path = os.path.join(current_app.config["SHELF_FOLDER"], book_url)
    if os.path.exists(book_dir_path):
        return basic_json(False, "Book already existing in the shelf folder!")
    cursor = mysql.cursor()
    cursor.execute(
        """SELECT book_id
        FROM shelf
        WHERE title='{book_title}' OR url='{book_url}'""".format(
            book_title=book_title, book_url=book_url
        )
    )
    data = cursor.fetchone()  # pylint: disable=unused-variable
    if not cursor.rowcount == 0:  # the title and url must be unique
        return basic_json(False, "Book title already in the database!")
    if not ("add-book-file" in request.files and "add-book-thumbnail" in request.files):
        return basic_json(False, "Missing file(s)!")
    file = request.files["add-book-file"]
    thumbnail = request.files["add-book-thumbnail"]
    if file.filename == "" or thumbnail.filename == "":
        return basic_json(False, "Missing file(s)!")
    if not file_extension(file.filename, "book"):
        return basic_json(False, "Wrong book file extension!")
    thumbnail_ext = file_extension(thumbnail.filename, "any")
    if thumbnail_ext != "jpg":
        return basic_json(False, "Thumbnail must be JPG!")
    try:
        os.mkdir(book_dir_path)
    except FileExistsError:
        message = "Failed to create the book directory! Already existing path."
        current_app.logger.exception(message)
        return basic_json(False, message + " Error logged.")
    filename = secure_filename(
        file.filename.rsplit("/", 1)[1] if "/" in file.filename else file.filename
    )
    thumbnail_path = os.path.join(book_dir_path, "card.jpg")
    thumbnail.save(thumbnail_path)
    file.save(os.path.join(book_dir_path, filename))
    book_period = (
        escape(request.form["add-book-period"].strip())
        if "add-book-period" in request.form
        else ""
    )
    cursor.execute(
        """INSERT INTO shelf(url, file_name, title, period,
        description_md, description_html, access_level, position, preview_card)
        VALUES ('{url}', '{filename}', '{title}', '{period}',
        '{description_md}', '{description_html}', {access_level},
        ({position}), '{preview_card}')""".format(
            url=book_url,
            filename=filename,
            title=book_title,
            period=book_period,
            description_md=book_description_md,
            description_html=book_description_html,
            access_level=access_level,
            position="SELECT IF(COUNT(clone.book_id), MAX(clone.position) + 1, 1) FROM shelf clone",
            preview_card=preview_image(thumbnail_path).decode(),
        )
    )
    mysql.commit()
    return basic_json(True, "Book successfully added to the shelf!")


@admin_app.route("/photos/list")
@restricted_admin
def manage_photos() -> Any:
    """
    List some photos to manage them. Find out global information about the gallery.

    Raises:
        404: if the user is not admin.
    """
    if not is_admin():
        abort(404)  # pragma: no cover
    cursor = mysql.cursor()
    order_by = request.args.get("orderby", "position", type=str)
    current_page = request.args.get("page", 1, type=int)
    cursor.execute(
        """SELECT COUNT(photo_id) AS total,
        SUM(CASE WHEN access_level=0 THEN 1 ELSE 0 END) AS total_public
        FROM gallery"""
    )
    data = cursor.fetchone()
    total_photos = data[0]
    total_public_photos = data[1]
    photos_per_page = request.args.get(
        "photos", current_app.config["DEFAULT_PHOTOS_PER_PAGE"], type=int
    )
    if photos_per_page < 1:
        photos_per_page = 1
    last_page = 1 + int(total_photos / photos_per_page)
    if current_page < 1:
        current_page = 1
    if current_page > last_page:
        current_page = last_page
    pagination = range(1, last_page + 1)
    ordering_options = ["position", "views", "loves"]
    is_not_admin = (
        "(m.access_level<255 OR (m.access_level IS NULL AND v.visitor_id IS NOT NULL))"
    )

    def sum_emotions(emotion):
        return """SUM(CASE WHEN v.emotion='{emotion}'
            AND v.element_type='gallery'
            AND {is_not_admin} THEN 1 ELSE 0 END)
            AS {emotion}s""".format(
            emotion=emotion, is_not_admin=is_not_admin
        )

    def all_sums():
        return """SUM(CASE WHEN {is_not_admin}
            AND v.element_type='gallery'
            THEN 1 ELSE 0 END) AS views,
            {loves}, {likes}, {dislikes}, {hates}""".format(
            is_not_admin=is_not_admin,
            loves=sum_emotions("love"),
            likes=sum_emotions("like"),
            dislikes=sum_emotions("dislike"),
            hates=sum_emotions("hate"),
        )

    if order_by == "position":
        query_order_by = "a.position"
    else:
        query_order_by = order_by
    cursor.execute(
        """SELECT a.photo_id, a.thumbnail_src, a.photo_l_src,
        a.photo_m_src, a.raw_src, a.title, a.description, a.date_added,
        a.date_modified, a.access_level, {sums}, a.date_taken, a.focal_length_35mm,
        a.exposure_time, a.f_number, a.iso
        FROM gallery a
        LEFT JOIN visits v ON a.photo_id=v.element_id
        LEFT JOIN members m ON m.member_id=v.member_id
        GROUP BY a.photo_id
        ORDER BY {order_by} DESC
        LIMIT {start},{photos_per_page}""".format(
            sums=all_sums(),
            order_by=query_order_by,
            start=(current_page - 1) * photos_per_page,
            photos_per_page=photos_per_page,
        )
    )
    gallery = cursor.fetchall()
    cursor.execute(
        """SELECT {sums}
        FROM visits v
        LEFT JOIN members m ON m.member_id=v.member_id""".format(
            sums=all_sums()
        )
    )
    gallery_total = cursor.fetchone()
    if not gallery_total[0]:
        gallery_total = [0] * 5  # 0 instead of None
    return render_template(
        "manage_photos.html",
        gallery=gallery,
        gallery_total=gallery_total,
        total_photos=total_photos,
        total_public_photos=total_public_photos,
        current_page=current_page,
        last_page=last_page,
        pagination=pagination,
        photos_per_page=photos_per_page,
        options_photos_per_page=current_app.config["OPTIONS_PHOTOS_PER_PAGE"],
        ordering_options=ordering_options,
        selected_ordering_type=order_by,
        is_prod=not current_app.config["DEBUG"],
    )


@admin_app.route("/books/list")
@restricted_admin
def manage_books() -> Any:
    """
    List some books to manage them. Find out global information about the shelf.

    Raises:
        404: if the user is not admin.
    """
    if not is_admin():
        abort(404)  # pragma: no cover
    cursor = mysql.cursor()
    current_page = request.args.get("page", 1, type=int)
    cursor.execute(
        """SELECT COUNT(book_id) AS total,
        SUM(CASE WHEN access_level=0 THEN 1 ELSE 0 END) AS total_public
        FROM shelf"""
    )
    data = cursor.fetchone()
    total_books = data[0]
    total_public_books = data[1]
    books_per_page = request.args.get(
        "books", current_app.config["DEFAULT_BOOKS_PER_PAGE"], type=int
    )
    if books_per_page < 1:
        books_per_page = 1
    last_page = 1 + int(total_books / books_per_page)
    if current_page < 1:
        current_page = 1
    if current_page > last_page:
        current_page = last_page
    pagination = range(1, last_page + 1)
    is_not_admin = (
        "(m.access_level<255 OR (m.access_level IS NULL AND v.visitor_id IS NOT NULL))"
    )

    def sum_emotions(emotion: str) -> str:
        return """SUM(CASE WHEN v.emotion='{emotion}'
            AND v.element_type='shelf'
            AND {is_not_admin} THEN 1 ELSE 0 END)
            AS {emotion}s""".format(
            emotion=emotion, is_not_admin=is_not_admin
        )

    def all_sums() -> str:
        return """SUM(CASE WHEN {is_not_admin}
            AND v.element_type='shelf'
            THEN 1 ELSE 0 END) AS views,
            {loves}, {likes}, {dislikes}, {hates}""".format(
            is_not_admin=is_not_admin,
            loves=sum_emotions("love"),
            likes=sum_emotions("like"),
            dislikes=sum_emotions("dislike"),
            hates=sum_emotions("hate"),
        )

    cursor.execute(
        """SELECT s.book_id, s.url, s.file_name, s.title, s.period,
        s.description_md, s.description_html, {sums}, s.date_added,
        s.date_modified, s.access_level, s.status, s.position, s.crowdfunding_goal
        FROM shelf s
        LEFT JOIN visits v ON s.book_id=v.element_id
        LEFT JOIN members m ON m.member_id=v.member_id
        GROUP BY s.book_id
        ORDER BY s.position DESC
        LIMIT {start},{books_per_page}""".format(
            sums=all_sums(),
            start=(current_page - 1) * books_per_page,
            books_per_page=books_per_page,
        )
    )
    shelf = cursor.fetchall()

    # add the directory listing to each book
    shelf_as_list = list(shelf)

    def get_files(path_name: str, ext: str) -> List:
        reduced_path = [
            file
            for file in glob.glob(path_name + "/*." + ext)
            if ".gpx_static_map." not in file
        ]
        return [path.split("/")[-1] for path in reduced_path]

    for i, book in enumerate(shelf_as_list):
        pathname = os.path.join(current_app.config["SHELF_FOLDER"], book[1])
        images = get_files(pathname, "jpg")
        card = "card.jpg"
        if card in images:
            images.remove(card)
        images = images + get_files(pathname, "jpeg") + get_files(pathname, "png")
        gpx = get_files(pathname, "gpx")
        pdfs = get_files(pathname, "pdf")
        book_file_name = book[2]
        if book_file_name in pdfs:
            pdfs.remove(book_file_name)  # exclude the book itself if it is a PDF
        movies = get_files(pathname, "webm")
        if not (gpx or images or movies or pdfs):
            resources = None
        else:
            resources = {"gpx": gpx, "image": images, "movie": movies, "pdf": pdfs}
        shelf_as_list[i] = book + (resources,)
    shelf = tuple(shelf_as_list)

    cursor.execute(
        """SELECT {sums}
        FROM visits v
        LEFT JOIN members m
        ON m.member_id=v.member_id""".format(
            sums=all_sums()
        )
    )
    shelf_total = cursor.fetchone()
    if not shelf_total[0]:
        shelf_total = [0] * 5  # 0 instead of None
    return render_template(
        "manage_books.html",
        shelf=shelf,
        shelf_total=shelf_total,
        total_books=total_books,
        total_public_books=total_public_books,
        current_page=current_page,
        last_page=last_page,
        pagination=pagination,
        books_per_page=books_per_page,
        options_books_per_page=current_app.config["OPTIONS_BOOKS_PER_PAGE"],
        is_prod=not current_app.config["DEBUG"],
    )


@admin_app.route("/photos/metadata", methods=("POST",))
@restricted_admin
def save_photo_metadata() -> FlaskResponse:
    """
    XHR request. Update the information about a photo.

    Raises:
        404: if the user is not admin or the request is not POST.
    """
    if not is_admin():
        abort(404)  # pragma: no cover
    if not all(
        x in request.form
        for x in [
            "photo_id",
            "access_level",
            "title",
            "description",
            "focal_length",
            "exposure_numerator",
            "exposure_denominator",
            "f",
            "iso",
            "local_date_taken",
        ]
    ):
        return basic_json(False, "Bad request, missing data!")
    photo_id = int(request.form["photo_id"])
    title = escape(request.form["title"].strip())
    focal_length: Union[int, None]
    exposure_numerator: Union[int, None]
    exposure_denominator: Union[int, None]
    exposure_time: Union[str, None]
    f_number: Union[float, None]
    iso: Union[int, None]

    try:
        focal_length = int(request.form["focal_length"])
    except (ValueError, TypeError):
        focal_length = None
    try:
        exposure_numerator = int(request.form["exposure_numerator"])
    except (ValueError, TypeError):
        exposure_numerator = None
    try:
        exposure_denominator = int(request.form["exposure_denominator"])
    except (ValueError, TypeError):
        exposure_denominator = None
    if exposure_numerator and exposure_denominator:
        exposure_time = str(exposure_numerator) + "/" + str(exposure_denominator)
    else:
        exposure_time = None
    try:
        f_number = float(request.form["f"])
    except (ValueError, TypeError):
        f_number = None
    try:
        iso = int(request.form["iso"])
    except (ValueError, TypeError):
        iso = None

    access_level = int(request.form["access_level"])
    date_taken = escape(request.form["local_date_taken"].strip())
    description = escape(request.form["description"].strip())
    cursor = mysql.cursor()
    cursor.execute(
        """UPDATE gallery SET title='{title}', description='{description}',
        access_level={access_level},
        date_modified=CURRENT_TIMESTAMP,
        focal_length_35mm={focal_length_35mm},
        exposure_time={exposure_time},
        f_number={f_number},
        iso={iso},
        date_taken={local_date_taken}
        WHERE photo_id={photo_id}""".format(
            title=title,
            description=description,
            photo_id=photo_id,
            access_level=access_level,
            focal_length_35mm=focal_length or "NULL",
            exposure_time="'" + exposure_time + "'" if exposure_time else "NULL",
            f_number=f_number or "NULL",
            iso=iso or "NULL",
            local_date_taken="'" + str(date_taken) + "'"
            if date_taken != ""
            else "NULL",
        )
    )
    mysql.commit()
    return basic_json(True, "Changes saved!")


@admin_app.route("/books/metadata", methods=("POST",))
@restricted_admin
def save_book_metadata() -> FlaskResponse:
    """
    XHR request. Update the information about a book.

    Raises:
        404: if the user is not admin or the request is not POST.
    """
    if not is_admin():
        abort(404)  # pragma: no cover
    if not (
        all(
            x in request.form
            for x in [
                "input-book-id",  # hidden field
                "input-book-url",  # hidden field
                "input-book-filename",  # hidden field, this is the current file before update
                "input-title",
                "input-description",
                "input-period",
                "input-status",
                "input-status",
                "input-crowdfunding-goal",
                "input-access-level",
            ]
        )
        and (all(x in request.files for x in ["input-book-file", "input-thumbnail"]))
    ):
        return basic_json(False, "Bad request, missing data!")
    book_id = int(request.form["input-book-id"])
    book_url = secure_filename(escape(request.form["input-book-url"]))
    book_filename = secure_filename(escape(request.form["input-book-filename"]))
    title = escape(request.form["input-title"].strip())
    if not title:
        return basic_json(False, "Missing title!")
    description_md = escape(request.form["input-description"].strip())
    if not description_md:
        return basic_json(False, "Missing description!")
    description_html = markdown.Markdown(
        extensions=current_app.config["MD_EXT"]
    ).convert(description_md)
    period = escape(request.form["input-period"].strip())
    status = escape(request.form["input-status"]).lower()
    if status not in ["released", "crowdfunding"]:
        status = "draft"  # reset unknown or empty status to 'draft'
    try:
        crowdfunding_goal = float(request.form["input-crowdfunding-goal"])
    except (ValueError, TypeError):
        crowdfunding_goal = 0
    if status == "crowdfunding" and crowdfunding_goal <= 0:
        return basic_json(False, "Crowdfunding goal required or change status!")
    access_level = int(request.form["input-access-level"])
    if not check_access_level_range(access_level):
        return basic_json(False, "Invalid access level!")
    book_dir_path = os.path.join(current_app.config["SHELF_FOLDER"], book_url)
    file = request.files["input-book-file"]
    new_book = file.filename != ""
    if new_book:
        if not file_extension(file.filename, "book"):
            return basic_json(False, "Wrong book file extension!")
        new_book_filename = secure_filename(
            file.filename.rsplit("/", 1)[1] if "/" in file.filename else file.filename
        )
        if book_filename != new_book_filename:  # replace the old file with the new one
            old_path_file = os.path.join(book_dir_path, book_filename)
            if os.path.isfile(old_path_file):
                os.remove(old_path_file)
            book_filename = new_book_filename
        file.save(os.path.join(book_dir_path, new_book_filename))
    thumbnail = request.files["input-thumbnail"]
    new_thumbnail = thumbnail.filename != ""
    if new_thumbnail:
        thumbnail_ext = file_extension(thumbnail.filename, "any")
        if thumbnail_ext != "jpg":
            return basic_json(
                False, "Thumbnail extension must be jpg!"
            )  # changes had been done if new_book anyway!
        thumbnail_path = os.path.join(book_dir_path, "card.jpg")
        thumbnail.save(thumbnail_path)
        preview_card = preview_image(thumbnail_path).decode()
    cursor = mysql.cursor()
    cursor.execute(
        """UPDATE shelf SET file_name='{file_name}', title='{title}',
        period='{period}', description_md='{description_md}',
        description_html='{description_html}', access_level={access_level},
        date_modified=CURRENT_TIMESTAMP,status='{status}',
        crowdfunding_goal={crowdfunding_goal},
        preview_card={preview_card}
        WHERE book_id={book_id}""".format(
            file_name=book_filename,
            title=title,
            period=period,
            description_md=description_md,
            description_html=description_html,
            access_level=access_level,
            status=status,
            crowdfunding_goal=crowdfunding_goal if crowdfunding_goal > 0 else "NULL",
            book_id=book_id,
            preview_card="'" + preview_card + "'" if new_thumbnail else "preview_card",
        )
    )
    mysql.commit()
    return basic_json(True, "Changes saved!")


@admin_app.route("/photos/move", methods=("POST",))
@restricted_admin
def move_photo() -> FlaskResponse:
    """
    XHR request. Re-order a photo. Listing should be ordered by `position` DESC.

    Raises:
        404: if the user is not admin or the request is not POST.
    """
    if not is_admin():
        abort(404)  # pragma: no cover
    if not all(
        x in request.form for x in ["dropped_id", "id_above_drop", "id_below_drop"]
    ):
        return basic_json(False, "Bad request, missing identifiers!")
    dropped_id = int(request.form["dropped_id"])
    id_above_drop = int(request.form["id_above_drop"])  # -1 if no photo above
    id_below_drop = int(request.form["id_below_drop"])  # -1 if no photo below
    cursor = mysql.cursor()

    # NOTICE: the photo on top has the highest 'position'.
    def get_position_from_id(photo_id: int) -> int:
        cursor.execute(
            """SELECT position
            FROM gallery
            WHERE photo_id={id}""".format(
                id=photo_id
            )
        )
        position = cursor.fetchone()
        if cursor.rowcount == 0:
            raise IndexError()
        return position[0]

    try:
        # get original position of the dropped photo
        old_pos = get_position_from_id(dropped_id)
    except IndexError:
        return basic_json(False, "Bad request, Unknown photo dropped!")

    if id_above_drop > 0:
        try:
            # get the position of the photo above the drop
            pos_above = get_position_from_id(id_above_drop)
        except IndexError:
            return basic_json(False, "Bad request, Unknown photo above drop!")

        if pos_above > old_pos:
            value_to_add = -1
            new_pos = pos_above - 1
            min_range = old_pos + 1
            max_range = pos_above - 1
        else:
            value_to_add = +1
            new_pos = pos_above
            min_range = pos_above
            max_range = old_pos - 1
    elif id_below_drop > 0:
        try:
            # get the position of the photo below the drop
            pos_below = get_position_from_id(id_below_drop)
        except IndexError:
            return basic_json(False, "Bad request, Unknown photo below drop!")

        if pos_below > old_pos:
            value_to_add = -1
            new_pos = pos_below
            min_range = old_pos + 1
            max_range = pos_below
        else:
            value_to_add = +1
            new_pos = pos_below + 1
            min_range = pos_below + 1
            max_range = old_pos - 1
    else:
        return basic_json(False, "Bad request, Unknown photos in-between the drop!")

    cursor.execute(
        """UPDATE gallery SET position=(position + {inc})
        WHERE position BETWEEN {min} AND {max}""".format(
            inc=value_to_add, min=min_range, max=max_range
        )
    )
    cursor.execute(
        """UPDATE gallery SET position={new_pos}
        WHERE photo_id={dropped_id}""".format(
            new_pos=new_pos, dropped_id=dropped_id
        )
    )
    mysql.commit()
    return basic_json(True, "Photo moved!")


@admin_app.route("/books/move", methods=("POST",))
@restricted_admin
def move_book() -> FlaskResponse:
    """
    XHR request. Re-order a book. Listing should be ordered by `position` DESC.

    Raises:
        404: if the user is not admin or the request is not POST.
    """
    if not is_admin():
        abort(404)  # pragma: no cover
    if not all(
        x in request.form for x in ["dropped_id", "id_above_drop", "id_below_drop"]
    ):
        return basic_json(False, "Bad request, missing identifiers!")
    dropped_id = int(request.form["dropped_id"])
    id_above_drop = int(request.form["id_above_drop"])  # -1 if no book above
    id_below_drop = int(request.form["id_below_drop"])  # -1 if no book below
    cursor = mysql.cursor()

    # NOTICE: the book on top has the highest 'position'.
    def get_position_from_id(book_id: int) -> int:
        cursor.execute(
            """SELECT position
            FROM shelf
            WHERE book_id={id}""".format(
                id=book_id
            )
        )
        position = cursor.fetchone()
        if cursor.rowcount == 0:
            raise IndexError()
        return position[0]

    try:
        # get original position of the dropped book
        old_pos = get_position_from_id(dropped_id)
    except IndexError:
        return basic_json(False, "Bad request, Unknown book dropped!")

    if id_above_drop > 0:
        try:
            # get the position of the book above the drop
            pos_above = get_position_from_id(id_above_drop)
        except IndexError:
            return basic_json(False, "Bad request, Unknown book above drop!")

        if pos_above > old_pos:
            value_to_add = -1
            new_pos = pos_above - 1
            min_range = old_pos + 1
            max_range = pos_above - 1
        else:
            value_to_add = +1
            new_pos = pos_above
            min_range = pos_above
            max_range = old_pos - 1
    elif id_below_drop > 0:
        try:
            # get the position of the book below the drop
            pos_below = get_position_from_id(id_below_drop)
        except IndexError:
            return basic_json(False, "Bad request, Unknown book below drop!")

        if pos_below > old_pos:
            value_to_add = -1
            new_pos = pos_below
            min_range = old_pos + 1
            max_range = pos_below
        else:
            value_to_add = +1
            new_pos = pos_below + 1
            min_range = pos_below + 1
            max_range = old_pos - 1
    else:
        return basic_json(False, "Bad request, Unknown books in-between the drop!")

    cursor.execute(
        """UPDATE shelf SET position=(position + {inc})
        WHERE position BETWEEN {min} AND {max}""".format(
            inc=value_to_add, min=min_range, max=max_range
        )
    )
    cursor.execute(
        """UPDATE shelf SET position={new_pos}
        WHERE book_id={dropped_id}""".format(
            new_pos=new_pos, dropped_id=dropped_id
        )
    )
    mysql.commit()
    return basic_json(True, "Book moved!")


@admin_app.route("/photos/delete", methods=("POST",))
@restricted_admin
def delete_photo() -> FlaskResponse:
    """
    XHR request. Remove a photo from the files and the database as well.

    Raises:
        404: if the user is not admin or the request is not POST.
    """
    if not is_admin():
        abort(404)  # pragma: no cover
    if "photo_id" not in request.form:
        return basic_json(False, "Bad request, missing identifier!")
    photo_id = int(request.form["photo_id"])
    cursor = mysql.cursor()

    # fetch the file names to remove the photos from the hard drive
    cursor.execute(
        """SELECT thumbnail_src, photo_l_src, photo_m_src, raw_src
        FROM gallery
        WHERE photo_id={id}""".format(
            id=photo_id
        )
    )
    files = cursor.fetchone()
    if cursor.rowcount == 0:
        return basic_json(False, "Bad request, wrong identifier!")

    # update the database first
    cursor.execute("DELETE FROM gallery WHERE photo_id={id}".format(id=photo_id))
    cursor.execute(
        "DELETE FROM visits WHERE element_id={id} AND element_type='gallery'".format(
            id=photo_id
        )
    )
    mysql.commit()

    # remove files "permanently"
    for file in files:
        os.remove(os.path.join(current_app.config["GALLERY_FOLDER"], file))
    return basic_json(True, "Photo successfully deleted!")


@admin_app.route("/photos/move_into_wastebasket", methods=("POST",))
@restricted_admin
def move_into_wastebasket() -> FlaskResponse:
    """
    XHR request. Move a photo into the wastebasket. The database is unchanged.

    Raises:
        404: if the user is not admin or the request is not POST.
    """
    if not is_admin():
        abort(404)  # pragma: no cover
    if "photo_filename" not in request.form:
        return basic_json(False, "Bad request, missing file name!")
    photo_filename = secure_filename(escape(request.form["photo_filename"]))
    photo_src = os.path.join(current_app.config["GALLERY_FOLDER"], photo_filename)
    photo_dst = current_app.config["WASTEBASKET_FOLDER"]
    path_dst = Path(photo_dst)
    if not path_dst.is_dir():
        path_dst.mkdir()
    shutil.move(photo_src, photo_dst)
    return basic_json(True, "Photo successfully moved into the wastebasket!")


@admin_app.route("/books/delete", methods=("POST",))
@restricted_admin
def delete_book() -> FlaskResponse:
    """
    XHR request. Remove a book from the files and the database as well.

    Raises:
        404: if the user is not admin or the request is not POST.
    """
    if not is_admin():
        abort(404)  # pragma: no cover
    if not ("book_id" in request.form and "book_url" in request.form):
        return basic_json(False, "Bad request!")
    book_id = int(request.form["book_id"])
    book_url = secure_filename(escape(request.form["book_url"]))
    cursor = mysql.cursor()

    # check request before action
    cursor.execute(
        """SELECT book_id
        FROM shelf
        WHERE book_id={id}
        AND url='{url}'""".format(
            id=book_id, url=book_url
        )
    )
    data = cursor.fetchone()  # pylint: disable=unused-variable
    if cursor.rowcount == 0:
        return basic_json(False, "Bad request!")

    # update the database first
    cursor.execute("DELETE FROM shelf WHERE book_id={id}".format(id=book_id))
    cursor.execute(
        "DELETE FROM visits WHERE element_id={id} AND element_type='shelf'".format(
            id=book_id
        )
    )
    mysql.commit()

    # remove the book folder "permanently"
    shutil.rmtree(os.path.join(current_app.config["SHELF_FOLDER"], book_url))
    return basic_json(True, "Book successfully deleted!")


@admin_app.route("/photos/lost")
@restricted_admin
def lost_photos() -> Any:
    """
    Look for lost photos.

    Raises:
        404: if the user is not admin.
    """
    if not is_admin():
        abort(404)  # pragma: no cover
    cursor = mysql.cursor()
    gallery_folder = current_app.config["GALLERY_FOLDER"]

    # Look for photos saved in the database but not existing in the server:
    cursor.execute(
        """SELECT photo_id, thumbnail_src, photo_l_src, photo_m_src, raw_src
        FROM gallery
        ORDER BY photo_id ASC"""
    )
    gallery = cursor.fetchall()
    photos_lost_in_server = []
    filenames_from_db = ()  # contains all filenames from the database
    for photo in gallery:
        types = ("Thumbnail", "Large", "Medium", "RAW")
        i = 0
        for src in photo[1:]:
            if not os.path.isfile(os.path.join(gallery_folder, src)):
                photos_lost_in_server.append((photo[0], types[i], src))
            i = i + 1
        filenames_from_db = filenames_from_db + (photo[1:])

    # Look for photos in the server not saved in the database:
    photos_lost_in_database = []
    if Path(gallery_folder).is_dir():
        directory = os.fsencode(gallery_folder)
        for file in os.listdir(directory):
            filename = os.fsdecode(file)
            if filename not in filenames_from_db:
                photos_lost_in_database.append(filename)

    return render_template(
        "lost_photos.html",
        photos_lost_in_server=photos_lost_in_server,
        total_photos_lost_in_server=len(photos_lost_in_server),
        photos_lost_in_database=photos_lost_in_database,
        total_photos_lost_in_database=len(photos_lost_in_database),
        is_prod=not current_app.config["DEBUG"],
    )


@admin_app.route("/photos/open/<string:filename>")
@restricted_admin
def photo_admin_dir(filename: str) -> FlaskResponse:
    """
    Make photo files reachable by the admin even if not existing in the database.
    That bypasses photo_dir()

    Raises:
        404: if the user is not admin.

    Args:
        filename (str): File name of the file located in the gallery folder/directory.
    """
    if not is_admin():
        abort(404)  # pragma: no cover
    filename = secure_filename(escape(filename))
    return send_from_directory(current_app.config["GALLERY_FOLDER"], filename)


@admin_app.route("/statistics")
@restricted_admin
def statistics() -> Any:
    """
    Do some statistics on photos and books.

    Raises:
        404: if the user is not admin.
    """
    if not is_admin():
        abort(404)  # pragma: no cover
    cursor = mysql.cursor()
    monthly_visits = {}
    for element_type in ["gallery", "shelf"]:
        cursor.execute(
            """SELECT EXTRACT(YEAR_MONTH FROM v.time) AS yearmonth,
            COUNT(v.visit_id) AS visits,
            COUNT(DISTINCT(v.visitor_id)) AS unique_visits
            FROM visits v
            LEFT JOIN members m
            ON m.member_id=v.member_id
            WHERE v.element_type='{element_type}' AND (m.access_level < 255 OR v.member_id IS NULL)
            GROUP BY yearmonth
            ORDER BY yearmonth ASC""".format(
                element_type=element_type
            )
        )
        monthly_visits[element_type] = cursor.fetchall()
    return render_template(
        "statistics.html",
        gallery_monthly_visits=json.dumps(monthly_visits["gallery"]),
        shelf_monthly_visits=json.dumps(monthly_visits["shelf"]),
        is_prod=not current_app.config["DEBUG"],
    )
