# flask app
import flask
import bulletin_config
import datetime
# import markdown_it
import flask_minify
import json
import database
import utilities
import render_markdown

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
        utilities=utilities,
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
                utilities=utilities,
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
            current_page="item_edit",
            PAGES=PAGES,
            bulletin_config=bulletin_config,
            permissions=get_permissions(user_id),
            user_info=USERS_LIST[user_id],
            item=item,
            utilities=utilities,
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
            # json.loads(flask.request.form["grades"]),
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


@app.route("/occurrences/edit/<id>")
def occurrences_edit(id):
    user_id = flask.request.cookies.get('user_id')
    item = database.fetch_item(id)
    occurrences = database.fetch_occurrences(id)
    if item["owner"] == user_id or "edit_all" in get_permissions(user_id):
        return flask.render_template(
            'occurrences_edit.html.j2',
            current_page="occurrences_edit",
            PAGES=PAGES,
            bulletin_config=bulletin_config,
            permissions=get_permissions(user_id),
            user_info=USERS_LIST[user_id],
            item=item,
            utilities=utilities,
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


@app.route("/api/preview/")
def preview():
    preview_visibilities = json.loads(
        flask.request.args.get("preview_visibilities", "[]")
    )
    preview_content = json.loads(flask.request.args.get("preview_content", '""'))
    previews = []
    for preview in preview_visibilities[:100]:
        previews.append(
            render_markdown.render_markdown(
                preview_content,
                visibilities=preview,
            )
        )
    return json.dumps(
        {
            "previews": previews,
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
