__author__ = 'kocsenc'

from flask import Flask, g, render_template, request, url_for, Response
import flask
import sqlite3

DATABASE = './db.sqlite3'

app = Flask(__name__)


@app.route('/student/<hashed_sid>')
def student_validate(hashed_sid):
    student = get_student(hashed_sid)
    if student:
        return flask.jsonify(**student)
    else:
        return Response(status=404, response="User does not exist.")


def get_student(hashed_sid):
    c = get_db().cursor()
    try:
        c.execute("SELECT sid, fname, lname, rit_username, issue_number FROM students WHERE sid=?", (hashed_sid,))

        fetched_student = c.fetchone()
        if fetched_student:
            hashed_sid = fetched_student[0]
            fname = fetched_student[1]
            lname = fetched_student[2]
            rit_username = fetched_student[3]
            issue_number = fetched_student[4]

            return {
                "hashed_sid": fetched_student[0],
                "fname": fetched_student[1],
                "lname": fetched_student[2],
                "rit_username": fetched_student[3],
                "issue_number": fetched_student[4]
            }
        else:
            return None
    except Exception as e:
        return None


@app.route("/student", methods=['GET', 'POST'])
def student_endpoint():
    if request.method == 'POST':
        json = request.json

        try:
            hashed_sid = json['hashed_sid']
            fname = json['fname']
            lname = json['lname']
            rit_username = json['rit_username']
            issue_number = json['issue_number']

            save_student_info(hashed_sid, fname, lname, rit_username, issue_number)
            return "saved"  # Status = 200
        except sqlite3.IntegrityError as e:
            # User is already registered, return a 409 CONFLICT error.
            return Response(status=409, response="Duplicate. User is already registered.")
        except KeyError as e:
            return Response(status=400, response="Bad request. Check your json keys: %s" % str(e))

    elif request.method == 'GET':
        return get_all_students_json()
    else:
        return Response(status=501)  # NOT IMPLEMENTED status code


def get_all_students_json():
    c = get_db().cursor()

    query = "SELECT sid, fname, lname, rit_username, issue_number from students;"
    students = c.execute(query)

    student_dict = {}

    for s in students:
        student_dict[s[0]] = {
            "sid": s[0],
            "fname": s[1],
            "lname": s[2],
            "rit_username": s[3],
            "issue_number": s[4],
        }

    return flask.jsonify(**student_dict)


def save_student_info(hashed_sid, fname, lname, rit_username, issue_number):
    setup_db()

    db = get_db()
    c = db.cursor()
    c.execute(
        "INSERT INTO students VALUES (?, ?, ?, ?, ?);",
        (hashed_sid, fname, lname, rit_username, issue_number)
    )
    db.commit()
    return True


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = connect_to_database()
    return db


def connect_to_database():
    return sqlite3.connect(DATABASE)


def setup_db():
    # Check if the table/db has been set, if not set it
    if g.get('is_db_created', None):  # FIXME: This does not work
        print("db already created, not creating again")
        return
    else:
        db = get_db()
        c = db.cursor()
        c.execute(
            "CREATE TABLE IF NOT EXISTS students (sid text primary key, fname text, lname text, rit_username text, issue_number integer);")
        db.commit()
        g.is_db_created = True
        print('db created')


if __name__ == "__main__":
    app.run()
