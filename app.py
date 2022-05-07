# flask app
import flask
import bulletin_config
import psycopg2
import datetime
# import markdown_it
import base64
import flask_minify

app = flask.Flask(__name__)

flask_minify.Minify(app=app)


PAGE_NAMES = {
    "/": "Home",
    "/admin/": "Admin",
    "/superuser/": "Superuser"
}

SAMPLE_USER_INFO = {
    "first_name": "John",
    "last_name": "Citizen",
    "email": "john.citizen@example.com",
    "name": "John Citizen",
}

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


def fetch_bulletins(count: int = 50, offset: int = 0, earlier_than: datetime.date = None):
    conn = database_connection()
    cur = conn.cursor()
    if earlier_than:
        cur.execute(
            'SELECT distinct("date") FROM "bulletin-2".occurrences ' +
            'WHERE date <= %s::timestamp ORDER BY "date" DESC LIMIT %s OFFSET %s',
            (earlier_than.strftime("%Y-%m-%d"), count, offset)
        )
    else:
        cur.execute(
            'SELECT distinct("date") FROM "bulletin-2".occurrences ' +
            'ORDER BY "date" DESC LIMIT %s OFFSET %s',
            (count, offset)
        )
    results = cur.fetchall()
    cur.close()
    conn.close()
    return results

def grades_string(grades: list):
    if -1 in grades:
        return "<i>All Grades</i>"
    else:
        return "<b>"+"</b> & <b>".join(map(str, grades))+"</b>"

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


def get_permissions(user_id):
    return ["admin"]


@ app.route('/')
def index():
    return flask.render_template(
        'index.html.j2',
        current_page="/",
        PAGE_NAMES=PAGE_NAMES,
        bulletin_config=bulletin_config,
        permissions=get_permissions(1),
        user_info=SAMPLE_USER_INFO,
        bulletins=fetch_bulletins(earlier_than=datetime.date.today()),
        get_age_from_time=get_age_from_time
    )


@ app.route("/bulletin/")
def bulletin():
    # get the date from ?date
    date = flask.request.args.get("date")
    if date:
        date = datetime.date.fromisoformat(date)
        return flask.render_template(
            'bulletin.html.j2',
            current_page="/bulletin/",
            PAGE_NAMES=PAGE_NAMES,
            bulletin_config=bulletin_config,
            permissions=get_permissions(1),
            user_info=SAMPLE_USER_INFO,
            bulletin_items=fetch_items_for_day(date),
            bulletin_date=date,
            base64_encode=base64.b64encode,
            # MARKDOWN_IT_RENDERER=MARKDOWN_IT_RENDERER
        )
