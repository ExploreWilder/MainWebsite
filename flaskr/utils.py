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
Common utilities.
"""

from .dependencies import *


class JSONSecureCookie(SecureCookie):
    """ https://werkzeug.palletsprojects.com/en/0.15.x/contrib/securecookie/#security """

    serialization_method = json


def get_static_package_config() -> Dict:
    """ Read the package.json file in the static directory and returns a dictionary. """
    with open(absolute_path("static/package.json")) as static_package:
        return json.loads(static_package.read())


def secure_decode_query_string(query_str: bytes) -> str:
    """
    Convert to UTF string and remove the ``<>%`` characters that could make
    a Cross Site Scripting attack.

    Args:
        query_str (ByteString): Basically request.query_string, which is the URL parameters as raw bytestring.

    Returns:
        str: Should be the same string utf-8 decoded if there is no attack.
    """
    return (
        query_str.decode("utf-8")
        .translate({ord(c): None for c in "<>"})
        .replace("%3C", "")
    )


def current_year() -> str:
    """
    Returns the current year in a 2-digit format.

    Example:
        "19" if the current year is 2019.
    """
    return str(datetime.datetime.now().year)[2:]


def anonymize_ip(real_ip: str) -> str:
    """
    Sets the last byte of the IP address `real_ip`.

    .. note::
        It is a good step but it may be possible to find out the physical address
        with some efforts.

    Example:
        If the input is "595.42.122.983", the output is "595.42.122.0".

    Raises:
        ValueError: ``real_ip`` must have 4 blocks separated with a dot.

    Args:
        real_ip (str): Full IPv4 address.

    Returns:
        str: ``real_ip`` with the last `byte` zeroed.
    """
    anonymized_ip = real_ip.split(".")
    if len(anonymized_ip) != 4:
        raise ValueError("Bad format of the IP address '" + real_ip + "'")
    anonymized_ip[3] = "0"
    return ".".join(anonymized_ip)


def absolute_path(secured_filename: str, curr_file: str = __file__) -> str:
    """
    Prepend `secured_filename` with the current path.

    Args:
        secured_filename (str): Safe file name. Can be a sub path without the first '/'.
        curr_file (str): File name of the module.

    Returns:
        str: String which contains the full path to ``secured_filename``.
    """
    return os.path.join(os.path.dirname(os.path.realpath(curr_file)), secured_filename)


def new_line_to_br(text: str) -> str:
    """
    Transform new lines to HTML tags.

    Args:
        text (str): Text from textarea.

    Returns:
        str: Text with <br />.
    """
    return re.sub(r"\n", "<br />", text, flags=re.UNICODE)


def remove_whitespaces(text: str) -> str:
    """
    Remove all whitespaces (space, tab, new line) in ``text``.

    Args:
        text (str): Text with whitespaces.

    Returns:
        str: Text without whitespaces.
    """
    return re.sub(r"\s+", "", text, flags=re.UNICODE)  # Python 2 AND 3 compatible


def email_is_valid(email_addr: str) -> bool:
    """
    Check if the email address is ``___@___.___``

    Args:
        email_addr (str): Email address to check.

    Returns:
        bool: True if valid, otherwise False.
    """
    return (
        email_addr != ""
        and re.match(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)", email_addr)
        is not None
    )


def check_access_level_range(access_level: int) -> bool:
    """
    Check if `access_level` is in the range [0, 255]. The actual level is not check.

    Args:
        access_level (int): Any access level, does not need to be the actual one.

    Returns:
        bool: True if in the range [0, 255].
    """
    return 0 <= access_level <= 255


def is_same_site() -> bool:
    """
    Check if the request comes from the same website.
    The decision is based on the Sec-Fetch-Site field if
    existing, otherwise the Referer. The Sec-Fetch-Site is
    only supported by Chrome-based browsers, that do not
    include the Referer when requested (contrary to Firefox-
    based browsers).

    * Sec-Fetch-Site Spec: https://www.w3.org/TR/fetch-metadata/
    * Referer Spec: https://tools.ietf.org/html/rfc7231#section-5.5.2

    Returns:
        True if the page loaded comes from the same website. False otherwise.
    """
    if "Sec-Fetch-Site" in request.headers:
        return (
            request.headers.get("Sec-Fetch-Site") == "same-origin"
        )  # pragma: no cover; tested on Chrome
    return request.referrer is not None and request.url_root in str(request.referrer)


def is_admin() -> bool:
    """
    Check user credentials.

    Returns:
        bool: True if the access level is maximum: admin.
    """
    return "access_level" in session and session["access_level"] == 255


def file_is_pdf(filename: str) -> bool:
    """
    Check if `filename` has the .pdf extension.

    Args:
        filename (str): Any filename, including its path.

    Returns:
        True if `filename` ends with .pdf, false otherwise.
    """
    return filename.endswith(".pdf")


def book_title_to_url(title: str) -> str:
    """
    Transform a book title into its URL-friendly equivalent.

    Args:
        title (str): Any one-line string already secured.

    Returns:
        String containing only the following characters ``a-zA-Z0-9_-``
    """
    return re.sub(r"[^a-zA-Z0-9_-]", "", re.sub(r" ", "_", title)).lower()


def file_extension(filename: str, file_type: str = "photo") -> str:
    """
    Get the file extension of `filename`.

    Args:
        filename (str): Any filename, including its path.
        file_type (str): "photo", "book", or "any"

    Returns:
        Image (png, jp(e)g, ti(f)f), book (md, pdf) or *any* extension or False.
    """
    if "." in filename:
        ext = filename.rsplit(".", 1)[1].lower()
        if file_type == "photo" and ext in {"png", "jpg", "jpeg", "tiff", "tif"}:
            return ext
        if file_type == "book" and ext in {"md", "pdf", "json"}:
            return ext
        if file_type == "any":
            return ext
    return ""


def csp_dict_to_str(csp: Dict) -> str:
    """ Convert the `csp` to string for the HTML meta tag. """
    return Markup(  # pragma: no cover; not used
        "; ".join(
            k + " " + (csp[k] if isinstance(csp[k], str) else " ".join(csp[k]))
            for k in csp
        )
        + ";"
    )


def csp_nonce() -> str:
    """
    Generate a Base64 random string of 24 characters for the cryptographic nonce.

    Returns:
        str: Random string of 24 Base64 characters.
    """
    return base64.b64encode(secrets.token_bytes(18)).decode("utf-8")


def generate_newsletter_id() -> str:
    """
    Generate a random string of characters which include any lower/upper cases and digits.

    Returns:
        str: Random string.
    """
    return "".join(
        secrets.choice(string.ascii_letters + string.digits) for _ in range(64)
    )


def random_text(size: int) -> str:
    """
    Generate a random string of characters which include any lower cases and digits.

    Args:
        size (int): The length of the generated string.

    Returns:
        str: Random string.
    """
    return "".join(
        secrets.choice(string.ascii_lowercase + string.digits) for _ in range(size)
    )


def random_filename(size: int, file_ext: str = "jpg") -> str:
    """
    Generate a random file name with the extension `file_extension`.

    Args:
        size (int): The length of the filename, file extension excluded.
        file_ext (string): The file extension. Default is jpg.

    Returns:
        str: A random file name with a specified extension.
    """
    return random_text(size) + "." + file_ext


def actual_access_level() -> int:
    """
    Get the access level of the current session or the lowest one.

    Returns:
        int: The access level or 0.
    """
    return session["access_level"] if "access_level" in session else 0


def escape(text: str) -> str:
    """
    Escape ``'"<>`` from `text` so that SQL injection and similar attacks are avoided.

    Args:
        text (str): Unsafe text.

    Returns:
        str: Safe text.
    """
    return str(Markup.escape(text))


def basic_json(
    success: bool, info: str, args: Union[Dict, None] = None
) -> FlaskResponse:
    """
    Simplify JSON format by returning a preformatted JSON.

    Args:
        success (bool): True for the Bootstrap alert-success or False for alert-danger.
        info (str): Message displayed.
        args: Optional dictionary appended to the JSON string.

    Returns:
        JSON data and its content-type header.
    """
    data = {"success": success, "info": info}
    returned_data = data.copy()
    if args:
        returned_data.update(args)
    return jsonify(returned_data)


def params_urlencode(params: Dict[str, Any]) -> str:
    """ Returns a string of 'key=value' pairs joined by '&'. Don't forget to add the extra '&' or '?' to the URL. """
    return "&".join([k + "=" + v for k, v in params.items()])


def create_and_save(
    raw_path: str,
    max_size: Tuple[int, int],
    filename_size: int,
    image_quality: int,
    upload_path: str,
) -> str:
    """
    Create a smaller picture of `raw_path` which fit in `max_size`. The file
    name is random with `filename_size` character, extension excluded.

    Args:
        raw_path (str): Path to the RAW picture.
        max_size: (max_width, max_height) in pixel.
        filename_size (int): File name size without the extension '.jpg'.
        image_quality (int): Image quality in percent.
        upload_path (str): Directory where the new picture would be saved.

    Returns:
        str: File path to the newly created and saved picture.
    """
    image = Image.open(raw_path)
    image = image.convert("RGB")
    image.thumbnail(
        (min(max_size[0], image.size[0]), min(max_size[1], image.size[1])),
        Image.ANTIALIAS,
    )
    photo_filename = random_filename(filename_size)
    image.save(os.path.join(upload_path, photo_filename), "JPEG", quality=image_quality)
    image.close()
    return photo_filename


def match_absolute_path(path: str) -> bool:
    """
    Return true if the path starts with ``http(s)://``, false otherwise.

    Args:
        path (str): URL

    Returns:
        bool: True for absolute URL, false for relative URL.
    """
    return re.match(r"http(s)*://*", path, re.IGNORECASE) is not None


def verbose_md_ext(extensions: List[str]) -> List[str]:
    """ Prepend `markdown.extensions.` to each element of the list `extensions`. """
    return ["markdown.extensions.{0}".format(ext) for ext in extensions]


def get_access_level_from_id(member_id: int, cursor: MySQLCursor) -> int:
    """
    Get the access level from the member `id`.

    Args:
        member_id (int): Member unique id.
        cursor: Cursor to access the database.

    Returns:
        int: Number or throw a ValueError exception if the member is not found.
    """
    cursor.execute(
        """SELECT access_level
        FROM members
        WHERE member_id={id}""".format(
            id=str(member_id)
        )
    )
    data = cursor.fetchone()
    if cursor.rowcount == 0 or not data:
        raise ValueError("Invalid member identifier!")
    return data[0]  # type: ignore[index]


def get_image_size(path: str) -> Tuple[int, int]:
    """
    Get the image size.

    Args:
        path (str): Path to the image.

    Returns:
        (width, height)
    """
    image = Image.open(path)
    size = image.size
    image.close()
    return size


def get_image_exif(path: str) -> Tuple:
    """
    Get some EXIF data with the exifread module.

    Args:
        path (str): Path to the image (tiff or jpg).

    Returns:
        (date taken in a datetime format or None if not available, focal length
        35mm-format as integer or None if not available, exposure time as a
        formatted string in seconds or None if not available, f-number ratio as
        float or None if not available, ISO as integer or None if not available)
    """
    with open(path, "rb") as raw_file:
        tags = exifread.process_file(raw_file)
        date_taken: Union[datetime.datetime, None]
        focal_length_35mm: Union[int, None]
        exposure_time_s: Union[str, None]
        f_number: Union[float, None]
        iso: Union[int, None]

        if "EXIF DateTimeOriginal" in tags:
            date_taken = datetime.datetime.strptime(
                str(tags["EXIF DateTimeOriginal"]), "%Y:%m:%d %H:%M:%S"
            )
        else:
            date_taken = None
        if "EXIF FocalLengthIn35mmFilm" in tags:
            focal_length_35mm = int(float(str(tags["EXIF FocalLengthIn35mmFilm"])))
        else:
            focal_length_35mm = None
        if "EXIF ExposureTime" in tags:
            exposure_time_s = str(tags["EXIF ExposureTime"])
        else:
            exposure_time_s = None
        if "EXIF FNumber" in tags:
            f_number = float(Fraction(str(tags["EXIF FNumber"])))
        else:
            f_number = None
        if "EXIF ISOSpeedRatings" in tags:
            iso = int(str(tags["EXIF ISOSpeedRatings"]))
        else:
            iso = None
        return date_taken, focal_length_35mm, exposure_time_s, f_number, iso


def friendly_datetime(ugly_datetime: str) -> str:
    """
    Format `ugly_datetime` in a more logical way.

    Args:
        ugly_datetime (str): Formatted to ``%Y-%m-%d %H:%M:%S``

    Returns:
        str: For example: `early morning, May 2018`
    """
    formatted_datetime = datetime.datetime.strptime(
        str(ugly_datetime), "%Y-%m-%d %H:%M:%S"
    )
    hour = int(datetime.datetime.strftime(formatted_datetime, "%H"))
    if hour < 5:
        h_time = "overnight"
    elif hour < 8:
        h_time = "early morning"
    elif hour < 12:
        h_time = "late morning"
    elif hour < 15:
        h_time = "early afternoon"
    elif hour < 17:
        h_time = "late afternoon"
    elif hour < 19:
        h_time = "early evening"
    elif hour < 21:
        h_time = "the evening"
    else:
        h_time = "overnight"
    month_year = datetime.datetime.strftime(formatted_datetime, "%B %Y")
    return h_time + ", " + month_year


def preview_image(image_path: str) -> bytes:
    """
    Create a tiny data:image/jpeg;base64-type image of `image_path`.
    The tiny image is 42px wide and keeps the ratio of the original image.
    The image is black & white even if the original image is RGB.
    Idea from https://css-tricks.com/the-blur-up-technique-for-loading-background-images/

    Args:
        image_path (str): Path to the image file.

    Returns:
        bytes: encoded ASCII string or b'' in case of error.
    """
    try:
        image = Image.open(image_path)
        image = image.convert("L")  # black and white
        preview_w = 42
        preview_h = int(
            float(preview_w) * float(image.size[1]) / float(image.size[0])
        )  # keep ratio
        image = image.resize((preview_w, preview_h))
        preview_buffer = io.BytesIO()
        image.save(preview_buffer, format="JPEG", quality=70)
        preview_base64 = bytes(
            "data:image/jpeg;base64,", encoding="utf-8"
        ) + base64.b64encode(preview_buffer.getvalue())
        image.close()
        return preview_base64
    except OSError:
        return b""


def fracstr_to_numerator(text: str) -> int:
    """ Returns the numerator of `text`. """
    return Fraction(text).limit_denominator().numerator


def fracstr_to_denominator(text: str) -> int:
    """ Returns the denominator of `text`. """
    return Fraction(text).limit_denominator().denominator


def allowed_external_connections(csp_config: Dict) -> List[str]:
    """ Returns a list of ``https://`` sources from `csp_config`. """
    connections = []
    for _, sources in csp_config.items():
        for source in sources:
            if source.startswith("https://"):
                connections.append(source)
    return list(dict.fromkeys(connections))


def total_subscribers(cursor: MySQLCursor) -> int:
    """ Count the number of subscribers and returns a positive integer or 0. """
    cursor.execute("SELECT COUNT(newsletter_id) FROM members WHERE email IS NOT NULL")
    data = cursor.fetchone()
    return data[0] if cursor.rowcount and data else 0  # type: ignore[index]


def same_site(view: Any) -> Any:
    """ View decorator redirecting external requests to the 404-error page. """

    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if not is_same_site() and not (
            current_app.config["TESTING"] or current_app.config["DEBUG"]
        ):  # pragma: no cover
            ext = file_extension(str(request.url_rule))
            if ext in ["jpg", "jpeg", "png"]:
                return tile_not_found("image/" + ext)
            abort(404)
        return view(**kwargs)

    return wrapped_view


def replace_extension(filename_src: str, new_ext: str) -> str:
    """
    Replace the extension of `filename_src` to `new_ext`.

    Args:
        filename_src (str): The filename with the old extension.
        new_ext (str): The new extension without dot.

    Returns:
        str: The filename with the new extension.
    """
    pre, _ = os.path.splitext(filename_src)
    return ".".join([pre, new_ext])


def tile_not_found(mimetype: str) -> FlaskResponse:
    """
    Send an image error instead of the 404 error page.

    Args:
        mimetype (str): image/[jp(e)g|png]
    """
    ext = mimetype.split("/")[-1]
    return send_from_directory("static/images", "tile404." + ext, mimetype=mimetype)
