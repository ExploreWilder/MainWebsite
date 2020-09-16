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

from .utils import *

class BookProcessor:
    """
    Process a Markdown story.
    
    Notice:
        The Markdown file and the processed Markdown (HTML files) are TRUSTED.
        Do NOT allow changes on those files by anyone but the webmaster.
    """
    def __init__(self, app: Flask, book_id: int, book_url: str, book_filename: str) -> None:
        """
        Args:
            app: The Flask app.
            book_id (int): Book ID.
            book_url (str): Book URL.
            book_filename (str): Book file name.
        """
        self.book_id = book_id
        self.book_url = book_url
        self.path_to_book_dir = os.path.join(app.config["SHELF_FOLDER"], book_url)
        self.path_to_md_book = os.path.join(self.path_to_book_dir, book_filename)
        self.p_md_book = Path(self.path_to_md_book)
        self.p_html_content = Path(self.path_to_md_book + ".html")
        self.p_html_toc = Path(self.path_to_md_book + ".toc.html")
        self.md = markdown.Markdown(extensions=app.config["BOOK_MD_EXT"])
        self.static_map_height = 100 * app.config["MAPBOX_STATIC_IMAGES"]["height"] / app.config["MAPBOX_STATIC_IMAGES"]["width"]
        self.current_app = app
    
    def get_empty_book(self) -> Dict[str, str]:
        """ Returns an empty book dictionary. Static member. """
        return {"html": "", "toc": ""}
    
    def is_outdated(self) -> bool:
        return not(self.p_html_content.is_file() \
            and self.p_html_toc.is_file() \
            and self.p_html_content.stat().st_mtime > self.p_md_book.stat().st_mtime)
    
    def print_book(self) -> Dict[str, str]:
        """
        Returns:
            A dictionary looking like { "html": ..., "toc": ... }
        """
        if self.is_outdated():
            self.convert()
        else:
            self.html = self.p_html_content.open("r", encoding="utf-8").read()
            self.toc = self.p_html_toc.open("r", encoding="utf-8").read()
        return { "html": Markup(self.html), "toc": Markup(self.toc) }
    
    def convert(self) -> None:
        with self.p_md_book.open("r", encoding="utf-8") as fd:
            content = re.sub(re.compile(r'!\[([^\]]*)]\(([^\)]*)\)'), self.img, fd.read())
        self.html = self.md.convert(content)
        self.html = self.remove_hr()
        self.html = re.sub(re.compile(r'<p><a href="~([^~]+)~">([^<]+)</a></p>'), self.custom_link, self.html)
        self.html = re.sub(re.compile(r'href="#fn:([0-9]+)"'), self.custom_footnote, self.html)
        self.p_html_content.open("w", encoding="utf-8").write(self.html)
        self.toc = self.md.toc
        self.p_html_toc.open("w", encoding="utf-8").write(self.toc)
    
    def remove_hr(self) -> str:
        return self.html.replace('<hr />', '')
    
    def img(self, match_obj: re.Match) -> str:
        """ Prepend the absolute path to images. """
        text = match_obj.group(1)
        image_tag_content = match_obj.group(2).split(' ', 1)
        image_filename = image_tag_content[0]
        image_legend = image_tag_content[1]
        link = os.path.join("/books", str(self.book_id), self.book_url, image_filename)
        with Image.open(os.path.join(self.path_to_book_dir, image_filename)) as im:
            return """<p style="position:relative; width:100%; height:0; padding-top:{image_height}%"
                title={image_legend}><img style="position:absolute; top:0; left:0; width:100%;"
                src="{link}" alt="{text}"></p>""".format(text=text,
                link=link,
                image_legend=image_legend,
                image_height=100 * im.size[1] / im.size[0])
    
    def custom_link(self, match_obj: re.Match) -> str:
        """ Create button to something (map or video). """
        type = match_obj.group(1)
        text = match_obj.group(2)
        formated_text = text.replace(" ", "_")
        if "track/" in type:
            return render_template('clickable_static_map.html',
                image_height=self.static_map_height,
                book_id=self.book_id,
                book_url=self.book_url,
                gpx_file=formated_text,
                gpx_title=text,
                country_code=type.rsplit("/")[1])
        elif type == "video":
            path = match_absolute_path(text)
            if not path: # internal link
                link = os.path.join("/books", str(self.book_id), self.book_url, formated_text + ".webm")
                text = "Watch video: " + text
            else:
                link = text
                text = "Watch video on " + re.split("/+", text)[1]
            title = "Watch video"
            icon = "fas fa-video"
        elif type == "pdf":
            link = os.path.join("/books", str(self.book_id), self.book_url, formated_text + ".pdf")
            title = "Open PDF file"
            icon = "fas fa-file-pdf"
        else:
            link = "#"
            title = ""
            icon = ""
            text = "BAD FORMAT"
        return """<p class="text-center">
            <a href="{link}" target="_blank" class="btn btn-light"
            role="button" title="{title}">
            <i class="{icon}"></i>
            {text}
            </a>
            </p>""".format(
                text=text,
                link=link,
                title=title,
                icon=icon)
    
    def custom_footnote(self, match_obj: re.Match) -> str:
        """ Add a title to the footnote link (so that the reader doesn't have to click). """
        ref = match_obj.group(1)
        footnote_content = re.search(re.compile(r'id="fn:' + re.escape(ref) + r'">\n<p>(.+)&#160;'), self.html)
        # convert HTML to text by removing tags
        footnote_content = re.sub(re.compile(r'<.*?>'), '', footnote_content.group(1))
        return 'href="#fn:%(ref)s" data-toggle="tooltip" title="%(title)s"' %{'ref': ref, 'title': footnote_content}
