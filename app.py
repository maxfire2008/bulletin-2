# flask app
import flask
import bulletin_config
import psycopg2
import datetime
# import markdown_it
import base64
import flask_minify

#import requests
#STACK_EDIT = "data:text/base64,"+base64.urlsafe_b64encode(requests.get("https://unpkg.com/stackedit-js@1.0.7/docs/lib/stackedit.min.js").content).decode()

app = flask.Flask(__name__)
app.jinja_options["autoescape"] = lambda _: True

if not app.debug:
    flask_minify.Minify(app=app)


PAGES = {
    "home": {
        "name": "Home",
        "deeplink": "/",
        "show_in_nav": True,
        "permission": None,
    },
    "error": {
        "name": "Error",
        "deeplink": "#",
        "show_in_nav": False,
        "permission": None,
    },
    "bullletin": {
        "name": "Bulletin",
        "deeplink": "#",
        "show_in_nav": False,
        "permission": None,
    },
    "admin": {
        "name": "Admin",
        "deeplink": "/admin/",
        "show_in_nav": True,
        "permission": "admin",
    },
    "superuser": {
        "name": "Superuser",
        "deeplink": "/superuser/",
        "show_in_nav": True,
        "permission": "superuser",
    },
}

USERS_LIST = {
    "1": {
        "first_name": "John",
        "last_name": "Citizen",
        "email": "john.citizen@example.com",
        "name": "John Citizen",
        "permissions": ["view_early", "minor_approve", "major_approve", "admin", "superuser"],
    },
    "2": {
        "first_name": "Jane",
        "last_name": "Citizen",
        "email": "jane.citizen@example.com",
        "name": "Jane Citizen",
        "permissions": ["minor_approve"],
    },
    "3": {
        "first_name": "Tim",
        "last_name": "Student",
        "email": "tim.student@example.com",
        "name": "Tim Student",
        "permissions": [],
    },
}


def get_permissions(user_id):
    return USERS_LIST[user_id]["permissions"]

# MARKDOWN_IT_RENDERER = (
#     markdown_it.MarkdownIt()
#     # .enable('table')
# )


def database_connection():
    return psycopg2.connect(
        host=bulletin_config.DATABASE_HOST,
        port=bulletin_config.DATABASE_PORT,
        database=bulletin_config.DATABASE_NAME,
        user=bulletin_config.DATABASE_USER,
        password=bulletin_config.DATABASE_PASSWORD)


def base64_encode(string):
    if type(string) is str:
        string = string.encode()
    return base64.urlsafe_b64encode(string).decode()

def get_items_for_user(user_id: list[str], limit: int = 500, offset: int = 0):
    conn = database_connection()
    cur = conn.cursor()
    cur.execute(
        'SELECT "id", last_edit, title, notes, "owner" ' +
        'FROM "bulletin-2".items ' +
        'WHERE "owner" = ANY(%s) ORDER BY "last_edit" DESC LIMIT %s OFFSET %s',
        (user_id, limit, offset)
    )
    results = cur.fetchall()
    cur.close()
    conn.close()
    return [{
        "id": item[0],
        "last_edit": item[1],
        "title": item[2],
        "notes": item[3],
        "owner": item[4],
    } for item in results]
# SELECT "id", last_edit, title, notes, "owner"
# FROM "bulletin-2".items
# WHERE "owner" = ANY('{1,2}') ORDER BY "last_edit" DESC LIMIT 100 OFFSET 0;


def fetch_item(item_id):
    conn = database_connection()
    cur = conn.cursor()
    cur.execute(
        'SELECT "id", notes, last_edit, title, content, grades, "owner" ' +
        'FROM "bulletin-2".items ' +
        'WHERE "id" = %s',
        (item_id,)
    )
    result = cur.fetchone()
    cur.close()
    conn.close()
    return {
        "id": result[0],
        "notes": result[1],
        "last_edit": result[2],
        "title": result[3],
        "content": result[4],
        "grades": result[5],
        "owner": result[6],
    }


def fetch_bulletins(limit: int = 500, offset: int = 0, earlier_than: datetime.date = None):
    conn = database_connection()
    cur = conn.cursor()
    if earlier_than:
        cur.execute(
            'SELECT distinct("date") FROM "bulletin-2".occurrences ' +
            'WHERE date <= %s::timestamp ORDER BY "date" DESC LIMIT %s OFFSET %s',
            (earlier_than.strftime("%Y-%m-%d"), limit, offset)
        )
    else:
        cur.execute(
            'SELECT distinct("date") FROM "bulletin-2".occurrences ' +
            'ORDER BY "date" DESC LIMIT %s OFFSET %s',
            (limit, offset)
        )
    results = cur.fetchall()
    cur.close()
    conn.close()
    return results


def grades_string(grades: list):
    if -1 in grades:
        return "<i>All Grades</i>"
    else:
        return "<b>"+"</b>, <b>".join(map(str, grades))+"</b>"


def fetch_items_for_day(date: datetime.date):
    conn = database_connection()
    cur = conn.cursor()
    cur.execute('SELECT distinct on ("bulletin-2".items.id) "bulletin-2".items.id, "bulletin-2".items.title, "bulletin-2".items."content", "bulletin-2".items.grades ' +
                'FROM "bulletin-2".occurrences, "bulletin-2".items ' +
                'WHERE "bulletin-2".occurrences."date" = %s::timestamp ' +
                'AND "bulletin-2".occurrences."item" = "bulletin-2".items.id',
                (date.strftime("%Y-%m-%d"),)
                )
    results = cur.fetchall()
    cur.close()
    conn.close()
    return [{
        "id": item[0],
        "title": item[1],
        "content": item[2],
        "grades": item[3],
        "grades_string": grades_string(item[3]),
    } for item in results]


def get_age_from_time(time_from: datetime.datetime):
    # subtract time_from from now
    time_diff = datetime.datetime.now(
    ) - datetime.datetime.combine(time_from, datetime.time())

    days = time_diff.days

    if days == 0:
        return "Today"
    elif days == 1:
        return "Yesterday"
    elif days < 7:
        return f"{days} days ago"
    elif days < 30:
        return f"{days // 7} weeks ago"
    elif days < 365:
        return f"{days // 30} months ago"
    else:
        return f"{days // 365} years ago"


@app.route('/')
def index():
    user_id = flask.request.cookies.get('user_id')
    return flask.render_template(
        'index.html.j2',
        current_page="home",
        PAGES=PAGES,
        bulletin_config=bulletin_config,
        permissions=get_permissions(user_id),
        user_info=USERS_LIST[user_id],
        bulletins=fetch_bulletins(earlier_than=datetime.date.today()),
        get_age_from_time=get_age_from_time,
        users_items=get_items_for_user([user_id]),
    )


@app.route("/bulletin/")
def bulletin():
    user_id = flask.request.cookies.get('user_id')
    # get the date from ?date
    date = flask.request.args.get("date")
    if date:
        try:
            date = datetime.date.fromisoformat(date)
        except:
            return flask.render_template(
                "error.html.j2",
                error="400: Invalid date",
                current_page="error",
                PAGES=PAGES,
                bulletin_config=bulletin_config,
                permissions=get_permissions(user_id),
                user_info=USERS_LIST[user_id],
            ), 400
        if (datetime.date.today()-date).days >= 0 or "view_early" in get_permissions(user_id):
            return flask.render_template(
                'bulletin.html.j2',
                current_page="bulletin",
                PAGES=PAGES,
                bulletin_config=bulletin_config,
                permissions=get_permissions(user_id),
                user_info=USERS_LIST[user_id],
                bulletin_date=date,
                bulletin_items=fetch_items_for_day(date),
                base64_encode=base64_encode,
                viewing_early=(not (datetime.date.today()-date).days >= 0)
            )
        else:
            return flask.render_template(
                "error.html.j2",
                error="403: You are not allowed to view the bulletin early",
                current_page="error",
                PAGES=PAGES,
                bulletin_config=bulletin_config,
                permissions=get_permissions(user_id),
                user_info=USERS_LIST[user_id],
            ), 403
    else:
        return flask.render_template(
            "error.html.j2",
            error="400: This request does not have a date",
            current_page="error",
            PAGES=PAGES,
            bulletin_config=bulletin_config,
            permissions=get_permissions(user_id),
            user_info=USERS_LIST[user_id],
        ), 400


@app.route("/edit/<id>")
def edit(id):
    user_id = flask.request.cookies.get('user_id')
    item = fetch_item(id)
    if item["owner"] == user_id:
        return flask.render_template(
            'edit.html.j2',
            current_page="edit",
            PAGES=PAGES,
            bulletin_config=bulletin_config,
            permissions=get_permissions(user_id),
            user_info=USERS_LIST[user_id],
            item=item,
            base64_encode=base64_encode,
        )
    else:
        return flask.render_template(
            "error.html.j2",
            error="403: You are not allowed to edit this item",
            current_page="error",
            PAGES=PAGES,
            bulletin_config=bulletin_config,
            permissions=get_permissions(user_id),
            user_info=USERS_LIST[user_id],
        ), 403


@app.route("/login/<id>")
def login(id):
    user_id = flask.request.cookies.get('user_id')
    resp = flask.make_response(
        '<br>'.join(
            [f"<a href=\"/login/{user_id}\">{user_id}</a>" for user_id in USERS_LIST.keys()]
        )
    )
    if id != 0:
        resp.set_cookie('user_id', id)
    return resp


@app.errorhandler(404)
def not_found_error(error):
    user_id = flask.request.cookies.get('user_id')
    return flask.render_template(
        "error.html.j2",
        error="404: Page not found",
        current_page="error",
        PAGES=PAGES,
        bulletin_config=bulletin_config,
        permissions=get_permissions(user_id),
        user_info=USERS_LIST[user_id],
    ), 404


@app.errorhandler(500)
def internal_error(error):
    user_id = flask.request.cookies.get('user_id')
    return flask.render_template(
        "error.html.j2",
        error="500: Server error",
        current_page="error",
        PAGES=PAGES,
        bulletin_config=bulletin_config,
        permissions=get_permissions(user_id),
        user_info=USERS_LIST[user_id],
    ), 400


@app.route("/coffee/")
def coffee():
    user_id = flask.request.cookies.get('user_id')
    return flask.render_template(
        "error.html.j2",
        error="I don't really like coffee even though I'm a programmer.",
        current_page="error",
        PAGES=PAGES,
        bulletin_config=bulletin_config,
        permissions=get_permissions(user_id),
        user_info=USERS_LIST[user_id],
    ), 418
