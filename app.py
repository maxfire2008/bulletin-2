# flask app
import flask
import bulletin_config
import datetime
# import markdown_it
import base64
import flask_minify
import json
import re
import markdown
import bleach
import database

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
    "bulletin": {
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
        "permissions": ["view_early", "minor_approve", "major_approve", "admin", "superuser", "edit_all"],
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


def base64_encode(string):
    if type(string) is str:
        string = string.encode()
    return base64.urlsafe_b64encode(string).decode()


def grades_string(grades: list):
    if -1 in grades:
        return "<i>All Grades</i>"
    else:
        return "<b>"+"</b>, <b>".join(map(str, grades))+"</b>"


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


def filter_visibility(text, visibility="public"):
    if visibility != "internal":
        text = re.sub("<!--internal-->(?s:.)*?<!--\/internal-->\n?", "", text)
    if visibility != "public":
        text = re.sub("<!--public-->(?s:.)*?<!--\/public-->\n?", "", text)
    text = re.sub("<!--/?internal-->\n?", "", text)
    text = re.sub("<!--/?public-->\n?", "", text)
    return text


def render_markdown(text: str, visibility: str = "public"):
    text = filter_visibility(text, visibility)
    rendered_markdown = markdown.markdown(
        text,
        extensions=['tables']
    )

    return bleach.clean(
        rendered_markdown,
        tags=[
            "h1",
            "h2",
            "h3",
            "h4",
            "h5",
            "h6",
            "p",
            "strong",
            "em",
            "blockquote",
            "ul",
            "ol",
            "li",
            "code",
            "a",
            "img",
        ],
        attributes={
            "*": ["class"],
            "a": ["href", "title"],
            "img": ["src", "alt", "title"],
        }
    )


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
        bulletins=database.fetch_bulletins(earlier_than=datetime.date.today()),
        get_age_from_time=get_age_from_time,
        users_items=database.get_items_for_user([user_id]),
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
                bulletin_items=database.fetch_items_for_day(date),
                base64_encode=base64_encode,
                viewing_early=(not (datetime.date.today()-date).days >= 0),
                render_markdown=render_markdown,
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


@app.route("/item/edit/<id>")
def item_edit(id):
    user_id = flask.request.cookies.get('user_id')
    item = database.fetch_item(id)
    if item["owner"] == user_id or "edit_all" in get_permissions(user_id):
        return flask.render_template(
            'item_edit.html.j2',
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


@app.route("/api/item/edit/<id>", methods=["POST"])
def item_edit_execute(id):
    user_id = flask.request.cookies.get('user_id')
    item = database.fetch_item(id)
    if item["owner"] == user_id or "edit_all" in get_permissions(user_id):
        if int(flask.request.form["last_edit"]) < item["last_edit"]:
            # return json.dumps(
            #     {
            #         "error": "This item has been edited since you loaded it. Please reload the page.",
            #         "current_state": {
            #             "title": item["title"],
            #             "content": item["content"],
            #             "notes": item["notes"],
            #             "grades": item["grades"],
            #         }
            #     }
            # ), 409
            return "newer_version_in_database", 409
        database.update_item(
            id,
            json.loads(flask.request.form["title"]),
            json.loads(flask.request.form["content"]),
            json.loads(flask.request.form["notes"]),
            json.loads(flask.request.form["grades"]),
        )
        return json.dumps({"success": True}), 200
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


@app.route("/api/preview/", methods=["POST"])
def preview():
    return json.dumps(
        {
            "preview_internal": render_markdown(json.loads(flask.request.form["content"]), "internal"),
            "preview_public": render_markdown(json.loads(flask.request.form["content"]), "public"),
            "wait_until_preview": 1000,
            "preview_rate": 5000,
        }
    )


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
