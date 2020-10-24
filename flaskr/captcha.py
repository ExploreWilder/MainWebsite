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

from .utils import *


class Captcha:
    """ Create, check and kill a CAPTCHA. """

    #: File path to the current CAPTCHA. No CAPTCHA file if empty.
    filepath: str = ""

    #: Value of the CAPTCHA once generated. No CAPTCHA if empty.
    passcode: str = ""

    def __init__(self, app: Flask) -> None:
        """
        Define the captcha salt.

        Args:
            app: Flask App.
        """
        self.config = app.config

    def check(self, passcode: str) -> bool:
        """
        Check if ``passcode`` is equal to the CAPTCHA code previously generated.
        Case insensitive. Whatever the result, the test unset the CAPTCHA.

        Args:
            passcode (str): The passcode typed by the user.

        Returns:
            bool: True if correct. False otherwise.
        """
        if self.config["TESTING"]:
            return True
        if not "captcha_passcode" in session:
            return False
        hashed_input = werkzeug.security.pbkdf2_bin(
            passcode.upper(), self.config["CAPTCHA_SALT"]
        )[:9]
        result = hashed_input == session["captcha_passcode"]
        session.pop("captcha_passcode", None)
        self.passcode = ""
        return result

    def create_image(self) -> None:
        """
        Create the image.
        The CAPTCHA font is hard to read by a machine, and easy by a human.
        If the CAPTCHA font file cannot be read, a 'better than nothing' default font is loaded.
        """
        self.captcha = Image.new(
            "RGB", (self.config["CAPTCHA_LENGTH"] * 37, 35), "white"
        )
        try:
            font = ImageFont.truetype(self.config["CAPTCHA_TTF_FONT"], 32)
        except OSError:  # font file not found or could not be read
            font = ImageFont.load_default()
        draw = ImageDraw.Draw(self.captcha)
        self.generate_passcode()
        offset = 0
        border_left = 10
        for c in self.passcode:
            draw.text(
                (border_left + 35 * offset, 2), c, self.random_colour(), font=font
            )
            offset += 1
        draw = ImageDraw.Draw(self.captcha)

    def generate_passcode(self) -> None:
        """
        Generate the passcode and save into the session. Data in session are signed
        but just base64 encoded, i.e. clear text. Therefore, the captcha is hashed
        with a secret salt (simple encryption). Uses the 9 most significant bytes
        of the SHA-256, which make a colision resistance of 36 bits.
        The captcha works like a candom anyway, single use/try.
        Do NOT call that function outside the class.
        """
        self.passcode = "".join(
            secrets.choice(self.config["CAPTCHA_CHARACTERS_OKAY"])
            for _ in range(self.config["CAPTCHA_LENGTH"])
        )
        session["captcha_passcode"] = werkzeug.security.pbkdf2_bin(
            self.passcode, self.config["CAPTCHA_SALT"]
        )[:9]

    def random_colour(self) -> Tuple[int, int, int]:
        """
        Generate a random colour as a tuple (R, G, B).

        Returns:
            tuple of 3 ints in the [0, 255] range.
        """
        sigma = 255 / 6  # 99.7% of samples within [-255, 255]
        average = 100  # Average colour = (red + green + blue) / 3 or less in a white background

        def random_element():
            return min(
                abs(random.gauss(average, sigma)), 255
            )  # all samples within [0, 255]

        red = random_element()
        green = random_element()
        blue = min(max(3 * average - red - green, 0), 255)  # force to [0, 255]
        return (int(red), int(green), int(blue))

    def to_file(self) -> FlaskResponse:
        """
        Image to file. The image have to be already generated.

        Returns:
            PNG file.

        Raises:
            404: If the image cannot be saved.
        """
        self.filepath = os.path.join(
            self.config["CAPTCHA_FOLDER"], random_filename(64, "png")
        )
        try:
            self.captcha.save(self.filepath, "PNG")
        except:  # directory
            abort(404)
        return send_file(self.filepath, mimetype="image/png")  # copy file into RAM

    def __del__(self) -> None:
        """ Remove the created file if existing. """
        if self.filepath != "":
            os.remove(self.filepath)
