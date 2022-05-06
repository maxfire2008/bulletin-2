# flask app
import flask
import bulletin_config
import psycopg2
import datetime

app = flask.Flask(__name__)

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


@app.route('/')
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

@app.route("/bulletin/")
def bulletin():
    return flask.render_template(
        'bulletin.html.j2',
        current_page="/bulletin/",
        PAGE_NAMES=PAGE_NAMES,
        bulletin_config=bulletin_config,
        permissions=get_permissions(1),
        user_info=SAMPLE_USER_INFO)
