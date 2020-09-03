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

import pytest, os, filecmp, shutil
from io import StringIO
from pathlib import Path
from flask import session
from flaskr.db import get_db
from flaskr import utils

def test_move_into_wastebasket(files, client, auth, app):
    """ Try to move a file into the wastebasket and check the actual move. """
    auth.login("root@test.com", "admin")
    
    rv = client.post("/admin/photos/move_into_wastebasket", data=dict())
    assert b"Bad request" in rv.data
    
    with app.app_context():
        test_filename = "tmp_test_move_into_wastebasket.jpg"
        test_src = os.path.join(app.config["GALLERY_FOLDER"], test_filename)
        test_dst = os.path.join(app.config["WASTEBASKET_FOLDER"], test_filename)
        data_filename = "test_74gdf8hpw41i4qbpnl7b.jpg"
        data_src = os.path.join(app.config["GALLERY_FOLDER"], data_filename)
        shutil.copyfile(data_src, test_src) # create a new file with existing data
        rv = client.post(
            "/admin/photos/move_into_wastebasket",
            data=dict(photo_filename=test_filename))
        assert b"Photo successfully moved into the wastebasket" in rv.data
        assert not os.path.isfile(test_src) # file removed from the gallery folder
        assert filecmp.cmp(data_src, test_dst) # file well copied in the wastebasket
        os.remove(test_dst) # remove the file from the wastebasket

def test_change_access_level(client, auth):
    """ Try to change the access level. """
    auth.login("root@test.com", "admin")

    rv = client.post("/admin/members/change_access_level", data=dict(member_id=0))
    assert b"Missing data" in rv.data

    rv = client.post(
        "/admin/members/change_access_level",
        data=dict(member_id=0, new_access_level=1234))
    assert b"Invalid access level" in rv.data

    rv = client.post(
        "/admin/members/change_access_level",
        data=dict(member_id=0, new_access_level=123))
    assert b"Invalid member ID" in rv.data

    rv = client.post(
        "/admin/members/change_access_level",
        data=dict(member_id=1, new_access_level=123))
    assert b"Change not allowed" in rv.data

    rv = client.post(
        "/admin/members/change_access_level",
        data=dict(member_id=2, new_access_level=123))
    assert b"Access level successfully changed" in rv.data

    auth.logout()
    rv = auth.login()
    assert b"animated-full-screen" in rv.data
    with client:
        client.get("/")
        assert session["access_level"] == 123
        assert session["member_id"] == 2

def test_revoke_member(client, auth):
    """ Try withdrawing the member's granted access. """
    auth.login("root@test.com", "admin")

    # bad data:
    rv = client.post("/admin/members/revoke", data=dict())
    assert b"Member identifier required" in rv.data

    # ID not in the table:
    rv = client.post("/admin/members/revoke", data=dict(member_id=0))
    assert b"false" in rv.data

    # Administrator cannot be revoked through the web interface:
    rv = client.post("/admin/members/revoke", data=dict(member_id=1))
    assert b"Member cannot be revoked" in rv.data

    # Revoke `test-user` (not Roger because database updates don't persist between tests):
    rv = client.post("/admin/members/revoke", data=dict(member_id=2))
    assert b"Member revoked" in rv.data

    auth.logout()
    rv = auth.login()
    assert b"animated-full-screen" in rv.data
    with client:
        client.get("/")
        assert session["username"] == "test-user"
        assert session["access_level"] == 0
        assert session["member_id"] == 2
        assert session["email"] == "user@test.com"
    auth.logout()

    # Cannot revoke a member who does not have super access anymore:
    auth.login("root@test.com", "admin")
    rv = client.post("/admin/members/revoke", data=dict(member_id=2))
    assert b"Member cannot be revoked" in rv.data

def test_delete_member(client, auth):
    """ Try deleting a member. """
    auth.login("root@test.com", "admin")

    # bad data:
    rv = client.post("/admin/members/delete", data=dict())
    assert b"Member identifier required" in rv.data

    # ID not in the table:
    rv = client.post("/admin/members/delete", data=dict(member_id=0))
    assert b"false" in rv.data

    # Administrator cannot be deleted through the web interface:
    rv = client.post("/admin/members/delete", data=dict(member_id=1))
    assert b"Administrator cannot be deleted" in rv.data

    # Delete `test-user`:
    rv = client.post("/admin/members/delete", data=dict(member_id=2))
    assert b"Member deleted" in rv.data

    # `test-user` cannot login anymore:
    auth.logout()
    rv = auth.login()
    assert b"Wrong email address or password" in rv.data

def test_send_newsletter(client, auth):
    """ Try to send a newsletter to subscribers without sending the actual emails. """
    auth.login("root@test.com", "admin")
    
    rv = client.post("/admin/members/send_newsletter", data=dict())
    assert b"Missing data" in rv.data
    
    rv = client.post("/admin/members/send_newsletter", data=dict(
        subject="  ",
        news="  "
    ))
    assert b"Subject required" in rv.data
    
    rv = client.post("/admin/members/send_newsletter", data=dict(
        subject=" Test  ",
        news="  "
    ))
    assert b"Please write something" in rv.data
    
    rv = client.post("/admin/members/send_newsletter", data=dict(
        subject=" Test  ",
        news="Hello world  "
    ))
    assert b"News sent" in rv.data

def test_failed_to_send_password_creation(client, auth):
    """
    Try to generate a message containing the link to create a user password.
    Successful attempt done in test_xhr_visitor_space.test_failed_to_create_password()
    """
    auth.login("root@test.com", "admin")
    
    rv = client.post("/admin/members/send_password_creation", data=dict())
    assert b"Missing data" in rv.data
    
    rv = client.post("/admin/members/send_password_creation", data=dict(
        member_id=-1
    ))
    assert b"Invalid member" in rv.data

def test_save_photo_metadata(client, auth):
    """ Update the metadata of one photo. """
    auth.login("root@test.com", "admin")

    rv = client.post("/admin/photos/metadata", data=dict())
    assert b"Bad request, missing data" in rv.data

    rv = client.post("/admin/photos/metadata", data=dict(
        photo_id=2,
        access_level=10,
        title="New title",
        description="New description",
        focal_length=21,
        exposure_numerator=1,
        exposure_denominator=22,
        f=2.3,
        iso=50,
        local_date_taken=""
    ))
    assert b"Changes saved" in rv.data

def test_save_book_metadata(files, client, auth, app):
    """ Update the metadata of one book. """
    auth.login("root@test.com", "admin")

    ransomware_filename = utils.absolute_path("ransomware.exe", __file__)
    card_png_filename = utils.absolute_path("card.png", __file__)
    md_book_filename = utils.absolute_path("my_ebook.md", __file__)
    md_update_book_filename = utils.absolute_path("my_new_ebook.md", __file__)
    card_jpg_filename = utils.absolute_path("card.jpg", __file__)

    rv = client.post("/admin/books/metadata",
        content_type="multipart/form-data",
        data={
            "input-book-id": 6,
            "input-book-url": "exploration_of_aotearoa",
            "input-book-filename": "exploration_of_aotearoa.md",
            "input-title": "",
            "input-period": "",
            "input-status": "",
            "input-access-level": 0,
            "input-book-file": (md_update_book_filename,),
            "input-thumbnail": (card_jpg_filename,),
        }
    )
    assert b"Bad request, missing data" in rv.data # missing description input field

    rv = client.post("/admin/books/metadata",
        content_type="multipart/form-data",
        data={
            "input-book-id": 6,
            "input-book-url": "exploration_of_aotearoa",
            "input-book-filename": "exploration_of_aotearoa.md",
            "input-title": " ",
            "input-description": "",
            "input-period": "",
            "input-status": "",
            "input-crowdfunding-goal": 12.34,
            "input-access-level": 0,
            "input-book-file": (md_update_book_filename,),
            "input-thumbnail": (card_jpg_filename,),
        }
    )
    assert b"Missing title" in rv.data # empty title

    rv = client.post("/admin/books/metadata",
        content_type="multipart/form-data",
        data={
            "input-book-id": 6,
            "input-book-url": "exploration_of_aotearoa",
            "input-book-filename": "exploration_of_aotearoa.md",
            "input-title": "My Title",
            "input-description": "",
            "input-period": "",
            "input-status": "",
            "input-crowdfunding-goal": 12.34,
            "input-access-level": 0,
            "input-book-file": (md_update_book_filename,),
            "input-thumbnail": (card_jpg_filename,),
        }
    )
    assert b"Missing description" in rv.data # empty description

    rv = client.post("/admin/books/metadata",
        content_type="multipart/form-data",
        data={
            "input-book-id": 6,
            "input-book-url": "exploration_of_aotearoa",
            "input-book-filename": "exploration_of_aotearoa.md",
            "input-title": "My Title",
            "input-description": "My description.",
            "input-period": "",
            "input-status": "",
            "input-crowdfunding-goal": 12.34,
            "input-access-level": -1,
            "input-book-file": (md_update_book_filename,),
            "input-thumbnail": (card_jpg_filename,),
        }
    )
    assert b"Invalid access level" in rv.data
    
    rv = client.post("/admin/books/metadata",
        content_type="multipart/form-data",
        data={
            "input-book-id": 6,
            "input-book-url": "exploration_of_aotearoa",
            "input-book-filename": "exploration_of_aotearoa.md",
            "input-title": "My Title",
            "input-description": "My description.",
            "input-period": "",
            "input-status": "crowdfunding",
            "input-crowdfunding-goal": -12.34,
            "input-access-level": 0,
            "input-book-file": (md_update_book_filename,),
            "input-thumbnail": (card_jpg_filename,),
        }
    )
    assert b"Crowdfunding goal required" in rv.data
    
    rv = client.post("/admin/books/metadata",
        content_type="multipart/form-data",
        data={
            "input-book-id": 6,
            "input-book-url": "exploration_of_aotearoa",
            "input-book-filename": "exploration_of_aotearoa.md",
            "input-title": "My Title",
            "input-description": "My description.",
            "input-period": "",
            "input-status": "crowdfunding",
            "input-crowdfunding-goal": "blabla",
            "input-access-level": 0,
            "input-book-file": (md_update_book_filename,),
            "input-thumbnail": (card_jpg_filename,),
        }
    )
    assert b"Crowdfunding goal required" in rv.data

    rv = client.post("/admin/books/add/request",
        content_type="multipart/form-data",
        data={
            "add-book-access-level": 10,
            "add-book-title": "Test",
            "add-book-description-md": "Blabla",
            "add-book-file": (md_book_filename,),
            "add-book-thumbnail": (card_jpg_filename,)
        }
    )
    assert b"Book successfully added to the shelf" in rv.data
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""SELECT book_id
            FROM shelf
            WHERE url='test'
            ORDER BY book_id DESC LIMIT 1""")
        data = cursor.fetchone()
        book_id = data[0]

    rv = client.post("/admin/books/metadata",
        content_type="multipart/form-data",
        data={
            "input-book-id": book_id,
            "input-book-url": "test",
            "input-book-filename": "my_ebook.md",
            "input-title": "My Title",
            "input-description": "My description.",
            "input-period": "",
            "input-status": "",
            "input-crowdfunding-goal": 12.34,
            "input-access-level": 0,
            "input-book-file": (ransomware_filename,),
            "input-thumbnail": (card_jpg_filename,),
        }
    )
    assert b"Wrong book file extension" in rv.data

    rv = client.post("/admin/books/metadata",
        content_type="multipart/form-data",
        data={
            "input-book-id": book_id,
            "input-book-url": "test",
            "input-book-filename": "my_ebook.md",
            "input-title": "My Title",
            "input-description": "My description.",
            "input-period": "",
            "input-status": "",
            "input-crowdfunding-goal": 12.34,
            "input-access-level": 0,
            "input-book-file": (md_book_filename,),
            "input-thumbnail": (card_png_filename,),
        }
    )
    assert b"Thumbnail extension must be jpg" in rv.data

    rv = client.post("/admin/books/metadata",
        content_type="multipart/form-data",
        data={
            "input-book-id": book_id, # use the created book ID
            "input-book-url": "test", # created book
            "input-book-filename": "my_ebook.md", # old file
            "input-title": "My Title",
            "input-description": "My description.",
            "input-period": "",
            "input-status": "", # 'draft' by default
            "input-crowdfunding-goal": 12.34,
            "input-access-level": 0,
            "input-book-file": (md_update_book_filename,), # new file
            "input-thumbnail": (card_jpg_filename,),
        }
    )
    assert b"Changes saved" in rv.data

    rv = client.post("/admin/books/delete", data=dict(book_id=book_id, book_url="test"))
    assert b"Book successfully deleted" in rv.data

def test_move_photo(files, client, auth):
    """ Preliminary test checking input data but not the logic. """
    auth.login("root@test.com", "admin")

    rv = client.post("/admin/photos/move", data=dict())
    assert b"Bad request, missing identifiers" in rv.data

    rv = client.post("/admin/photos/move", data=dict(
        dropped_id=0,
        id_above_drop=0,
        id_below_drop=0
    ))
    assert b"Bad request, Unknown photo dropped" in rv.data

    rv = client.post("/admin/photos/move", data=dict(
        dropped_id=1,
        id_above_drop=0,
        id_below_drop=0
    ))
    assert b"Bad request, Unknown photos in-between the drop" in rv.data

    rv = client.post("/admin/photos/move", data=dict(
        dropped_id=1,
        id_above_drop=2,
        id_below_drop=3
    ))
    assert b"Photo moved" in rv.data

def test_move_book(files, client, auth):
    """ Preliminary test checking input data but not the logic. """
    auth.login("root@test.com", "admin")

    rv = client.post("/admin/books/move", data=dict())
    assert b"Bad request, missing identifiers" in rv.data

    rv = client.post("/admin/books/move", data=dict(
        dropped_id=0,
        id_above_drop=0,
        id_below_drop=0
    ))
    assert b"Bad request, Unknown book dropped" in rv.data

    rv = client.post("/admin/books/move", data=dict(
        dropped_id=1,
        id_above_drop=0,
        id_below_drop=0
    ))
    assert b"Bad request, Unknown books in-between the drop" in rv.data

    rv = client.post("/admin/books/move", data=dict(
        dropped_id=1,
        id_above_drop=2,
        id_below_drop=3
    ))
    assert b"Book moved" in rv.data

def test_add_delete_photo(files, client, auth, app):
    """ Try to add a photo in the database and the gallery folder and finally delete it. """
    auth.login("root@test.com", "admin")

    rv = client.post("/admin/photos/add/request", data=dict())
    assert b"Missing data" in rv.data

    rv = client.post("/admin/photos/add/request", data={
        "add-photo-access-level": 1024,
        "add-photo-title": "",
        "add-photo-description": ""
    })
    assert b"Invalid access level" in rv.data

    rv = client.post("/admin/photos/add/request", data={
        "add-photo-access-level": 10,
        "add-photo-title": "",
        "add-photo-description": ""
    })
    assert b"No file part" in rv.data

    filename = utils.absolute_path("original.tif", __file__)
    rv = client.post("/admin/photos/add/request",
        content_type="multipart/form-data",
        data={
            "add-photo-access-level": 10,
            "add-photo-title": "",
            "add-photo-description": "",
            "add-photo-file": (filename + "i",) # .tifi
        }
    )
    assert b"Wrong file extension" in rv.data

    rv = client.post("/admin/photos/add/request",
        buffered=True,
        content_type="multipart/form-data",
        data={
            "add-photo-access-level": 10,
            "add-photo-title": "Great view!",
            "add-photo-description": "Once upon a time...",
            "add-photo-file": (filename,)
        }
    )
    assert b"Photo successfully added to the gallery" in rv.data

    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""SELECT thumbnail_src, photo_m_src, photo_m_width,
            photo_m_height, photo_l_src, photo_l_width, photo_l_height, raw_src,
            raw_width, raw_height, title, description, access_level, photo_id
            FROM gallery
            ORDER BY photo_id DESC LIMIT 1""")
        data = cursor.fetchone()

        path_to_thumbnail = os.path.join(app.config["GALLERY_FOLDER"], data[0])
        assert Path(path_to_thumbnail).is_file()

        path_to_photo_m = os.path.join(app.config["GALLERY_FOLDER"], data[1])
        assert Path(path_to_photo_m).is_file()
        assert data[2] <= app.config["PHOTO_M_MAX_SIZE"][0] \
            and data[3] <= app.config["PHOTO_M_MAX_SIZE"][1] \
            and (data[2], data[3]) == utils.get_image_size(path_to_photo_m)

        path_to_photo_l = os.path.join(app.config["GALLERY_FOLDER"], data[4])
        assert Path(path_to_photo_l).is_file()
        assert data[5] <= app.config["PHOTO_L_MAX_SIZE"][0] \
            and data[6] <= app.config["PHOTO_L_MAX_SIZE"][1] \
            and (data[5], data[6]) == utils.get_image_size(path_to_photo_l)

        path_to_raw = os.path.join(app.config["GALLERY_FOLDER"], data[7])
        assert Path(path_to_raw).is_file()
        assert (data[8], data[9]) == utils.get_image_size(path_to_raw)
        assert data[10] == "Great view!"
        assert data[11] == "Once upon a time..."
        assert data[12] == 10

        photo_id = data[13]

        # add some visits which shoud be deleted later on:
        for _ in range(20):
            cursor.execute("""INSERT INTO visits(element_id, element_type)
                VALUES ({photo_id}, 'gallery')""".format(photo_id=photo_id))
        db.commit()

    rv = client.post("/admin/photos/add/request",
        buffered=True,
        content_type="multipart/form-data",
        data={
            "add-photo-access-level": 10,
            "add-photo-title": "Stunning view!",
            "add-photo-description": "A long time ago...",
            "add-photo-file": (filename,)
        }
    )
    assert b"Photo already in the database" in rv.data

    rv = client.post("/admin/photos/delete", data=dict())
    assert b"Bad request, missing identifier" in rv.data

    rv = client.post("/admin/photos/delete", data=dict(photo_id=248))
    assert b"Bad request, wrong identifier" in rv.data

    rv = client.post("/admin/photos/delete", data=dict(photo_id=photo_id))
    assert b"Photo successfully deleted" in rv.data

    with app.app_context():
        cursor = get_db().cursor()
        cursor.execute("""SELECT *
            FROM gallery
            WHERE photo_id={photo_id}""".format(
            photo_id=photo_id))
        cursor.fetchone()
        assert cursor.rowcount == 0
        cursor.execute("""SELECT *
            FROM visits
            WHERE element_id={photo_id} AND element_type='gallery'""".format(
            photo_id=photo_id))
        cursor.fetchone()
        assert cursor.rowcount == 0

    for path in (path_to_thumbnail, path_to_photo_m, path_to_photo_l, path_to_raw):
        assert not Path(path).is_file()

def test_add_delete_book(files, client, auth, app):
    """ Try to add a book in the database and the shelf folder and finally delete it. """
    auth.login("root@test.com", "admin")

    rv = client.post("/admin/books/add/request", data=dict())
    assert b"Missing data" in rv.data

    rv = client.post("/admin/books/add/request", data={
        "add-book-access-level": 1024,
        "add-book-title": "",
        "add-book-description-md": ""
    })
    assert b"Access level invalid" in rv.data

    rv = client.post("/admin/books/add/request", data={
        "add-book-access-level": 10,
        "add-book-title": "    ",
        "add-book-description-md": "  "
    })
    assert b"Missing title" in rv.data

    rv = client.post("/admin/books/add/request", data={
        "add-book-access-level": 10,
        "add-book-title": "Super Story",
        "add-book-description-md": "   "
    })
    assert b"Missing description" in rv.data

    rv = client.post("/admin/books/add/request", data={
        "add-book-access-level": 10,
        "add-book-title": "Lovely Poem",
        "add-book-description-md": "Blabla"
    })
    assert b"Book already existing in the shelf folder" in rv.data

    rv = client.post("/admin/books/add/request", data={
        "add-book-access-level": 10,
        "add-book-title": "Random Title",
        "add-book-description-md": "Blabla"
    })
    assert b"Book title already in the database" in rv.data

    md_book_filename = utils.absolute_path("my_ebook.md", __file__)
    rv = client.post("/admin/books/add/request",
        content_type="multipart/form-data",
        data={
            "add-book-access-level": 10,
            "add-book-title": "Super Story",
            "add-book-description-md": "Blabla",
            "add-book-file": (md_book_filename,)
        }
    )
    assert b"Missing file" in rv.data

    ransomware_filename = utils.absolute_path("ransomware.exe", __file__)
    card_png_filename = utils.absolute_path("card.png", __file__)
    card_jpg_filename = utils.absolute_path("card.jpg", __file__)
    rv = client.post("/admin/books/add/request",
        content_type="multipart/form-data",
        data={
            "add-book-access-level": 10,
            "add-book-title": "Super Story",
            "add-book-description-md": "Blabla",
            "add-book-file": (ransomware_filename,),
            "add-book-thumbnail": (card_jpg_filename,)
        }
    )
    assert b"Wrong book file extension" in rv.data

    rv = client.post("/admin/books/add/request",
        content_type="multipart/form-data",
        data={
            "add-book-access-level": 10,
            "add-book-title": "Super Story",
            "add-book-description-md": "Blabla",
            "add-book-file": (md_book_filename,),
            "add-book-thumbnail": (card_png_filename,)
        }
    )
    assert b"Thumbnail must be JPG" in rv.data

    rv = client.post("/admin/books/add/request",
        content_type="multipart/form-data",
        data={
            "add-book-access-level": 10,
            "add-book-title": "Super Story",
            "add-book-description-md": "Blabla",
            "add-book-file": (md_book_filename,),
            "add-book-thumbnail": (card_jpg_filename,)
        }
    )
    assert b"Book successfully added to the shelf" in rv.data

    rv = client.post("/admin/books/add/request",
        content_type="multipart/form-data",
        data={
            "add-book-access-level": 10,
            "add-book-title": "Super Story",
            "add-book-description-md": "Blabla",
            "add-book-file": (md_book_filename,),
            "add-book-thumbnail": (card_jpg_filename,)
        }
    )
    assert b"Book already existing in the shelf folder" in rv.data

    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""SELECT book_id
            FROM shelf
            WHERE url='super_story'
            ORDER BY book_id DESC LIMIT 1""")
        data = cursor.fetchone()
        book_id = data[0]

        path_to_thumbnail = os.path.join(app.config["SHELF_FOLDER"], "super_story", "card.jpg")
        assert Path(path_to_thumbnail).is_file()

        path_to_md_book = os.path.join(app.config["SHELF_FOLDER"], "super_story", "my_ebook.md")
        assert Path(path_to_md_book).is_file()

        # add some visits which shoud be deleted later on:
        for _ in range(20):
            cursor.execute("""INSERT INTO visits(element_id, element_type)
                VALUES ({book_id}, 'shelf')""".format(book_id=book_id))
        db.commit()

    rv = client.post("/admin/books/delete", data=dict())
    assert b"Bad request" in rv.data

    rv = client.post("/admin/books/delete", data=dict(book_id=248, book_url="super_story"))
    assert b"Bad request" in rv.data

    rv = client.post("/admin/books/delete", data=dict(book_id=book_id, book_url="super_story"))
    assert b"Book successfully deleted" in rv.data

    with app.app_context():
        cursor = get_db().cursor()
        cursor.execute("""SELECT *
            FROM shelf
            WHERE book_id={book_id}""".format(
            book_id=book_id))
        cursor.fetchone()
        assert cursor.rowcount == 0
        cursor.execute("""SELECT *
            FROM visits
            WHERE element_id={book_id} AND element_type='shelf'""".format(
            book_id=book_id))
        cursor.fetchone()
        assert cursor.rowcount == 0

    for path in (path_to_thumbnail, path_to_md_book):
        assert not Path(path).is_file()
