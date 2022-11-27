import os
import psycopg2
from dotenv import load_dotenv
from flask import Flask, request, render_template, url_for, redirect, flash, session
from flask_session.__init__ import Session
from datetime import datetime, timezone


load_dotenv()  # loads variables from .env file into environment

app = Flask(__name__)
url = os.environ.get("DATABASE_URL")  # gets variables from environment
app.secret_key = os.environ.get("secret_key")
connection = psycopg2.connect(url)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config.from_object(__name__)
Session(app)

CREATE_BOOKMARKS_TABLE = (
    "CREATE TABLE IF NOT EXISTS bookmarks ( id SERIAL PRIMARY KEY, name TEXT, url VARCHAR, folder_id INTEGER NULL, created_at timestamp, updated_at timestamp, FOREIGN KEY (folder_id) REFERENCES folders(id) ON DELETE CASCADE);"
)

CREATE_FOLDERS_TABLE = """CREATE TABLE IF NOT EXISTS folders (id SERIAL PRIMARY KEY, name TEXT, description TEXT, created_at timestamp, updated_at timestamp);"""

INSERT_BOOKMARK_RETURN_ID = "INSERT INTO bookmarks (name, url,created_at) VALUES (%s, %s, %s) RETURNING id;"

INSERT_FOLDER_RETURN_ID = (
    "INSERT INTO folders (name, description, created_at) VALUES (%s, %s, %s) RETURNING id;")

GET_ALL_BOOKMARKS_LIST = (""" SELECT * FROM bookmarks;""")
GET_ALL_FOLDERS_LIST = (""" SELECT * FROM folders; """)

UPDATE_BOOKMARKS = ("SELECT * FROM bookmarks where id = %s;")


@app.route("/")
def index():
    with connection:
        with connection.cursor() as cursor:
            cursor.execute(GET_ALL_BOOKMARKS_LIST)
            bookmarks_list = cursor.fetchall()
    return render_template('index.html', bookmarks_list=bookmarks_list)


@app.route("/api/v1/bookmarks", methods=['GET', 'POST'])
def create_bookmark():
    if request.method == 'POST':
        bookmark_name = request.form["name"]
        url = request.form["url"]
        created_at = datetime.now(timezone.utc)
        with connection:
            with connection.cursor() as cursor:
                cursor.execute(CREATE_BOOKMARKS_TABLE)
                cursor.execute(INSERT_BOOKMARK_RETURN_ID,
                               (bookmark_name, url, created_at))

                flash('Bookmark Added Successfully.')
                return redirect(url_for('index'))


@app.route("/api/v1/bookmarks", methods=['GET'])
def get_all_bookmarks():
    with connection:
        with connection.cursor() as cursor:
            cursor.execute(GET_ALL_BOOKMARKS_LIST)
            bookmarks_list = cursor.fetchall()

    return {"bookmark_list": bookmarks_list}


@app.route("/api/v1/folders", methods=['POST'])
def create_folder():
    folder_data = request.get_json()
    folder_name = folder_data["name"]
    description = folder_data["description"]
    created_at = datetime.now(timezone.utc)
    with connection:
        with connection.cursor() as cursor:
            cursor.execute(CREATE_FOLDERS_TABLE)
            cursor.execute(INSERT_FOLDER_RETURN_ID,
                           (folder_name, description, created_at))
            folder_id = cursor.fetchone()[0]

    return {"id": folder_id, "message": f"Folder {folder_name} has been created."}, 201


@app.route("/api/v1/folders", methods=['GET'])
def get_all_folders():
    with connection:
        with connection.cursor() as cursor:
            cursor.execute(GET_ALL_FOLDERS_LIST)
            folders_list = cursor.fetchall()

    return {"folder_list": folders_list}


@app.route("/api/v1/bookmarks/<int:bookmark_id>", methods=['PUT'])
def update_bookmark(bookmark_id):
    with connection:
        with connection.cursor() as cursor:
            cursor.execute(UPDATE_BOOKMARKS, (bookmark_id))
            data = cursor.fetchall()

            return render_template('edit.html', data=data[0])


if __name__ == "__main__":
    app.run(debug=True)
