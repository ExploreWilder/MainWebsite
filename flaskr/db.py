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

def get_db():
    """
    Connect to the application's configured database. The connection is unique
    for each request and will be reused if this is called again.
    """
    if "db" not in g:
        try:
            g.db = pymysql.connect(
                current_app.config["MYSQL_DATABASE_HOST"],
                current_app.config["MYSQL_DATABASE_USER"],
                current_app.config["MYSQL_DATABASE_PASSWORD"],
                current_app.config["MYSQL_DATABASE_DB"]
            )
        except pymysql.Error as e:
            if e.args[0] == 1049: # unknown database, create it
                g.db = pymysql.connect(
                    current_app.config["MYSQL_DATABASE_HOST"],
                    current_app.config["MYSQL_DATABASE_USER"],
                    current_app.config["MYSQL_DATABASE_PASSWORD"]
                )
                cursor = g.db.cursor()
                cursor.execute("CREATE DATABASE {db_name}".format(
                    db_name=current_app.config["MYSQL_DATABASE_DB"])
                )
                g.db.commit()
            else:
                print("MySQL error %d: %s" % (e.args[0], e.args[1]))

    return g.db

def close_db(error=None):
    """ If this request connected to the database, close the connection. """
    db = g.pop("db", None)

    if db is not None:
        db.close()

def load_from_file(file):
    """ Load an SQL file descriptor into the database. """
    request_list = file.read().decode("utf8").split(';') # split file in list
    request_list.pop() # drop last empty entry
    if request_list is not False:
        db = get_db()
        cursor = db.cursor()
        for idx, sql_request in enumerate(request_list):
            cursor.execute(sql_request)
        db.commit()

def init_db():
    """
    Run the file schema.sql which clears the database.
    Ensure to be connected to the right database or data may be lost forever!
    """
    with current_app.open_resource("schema.sql") as f:
        load_from_file(f)

@click.command("init-db")
@with_appcontext
def init_db_command():
    """
    Clear the existing data and create new tables.
    Ensure to be connected to the right database or data may be lost forever!
    """
    init_db()
    click.echo("Database initialized.")

def init_app(app):
    """
    Register database functions with the Flask app. This is called by the
    application factory.
    """
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
