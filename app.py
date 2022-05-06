# flask app
import flask
import bulletin_config
import psycopg2

conn_string = "host=" + "127.0.0.1" + " port=" + "5432" + " dbname=" + "bulletin-2" + " user=" + "bulletin-2" \
    + " password=" + input("Enter postgres password: ")
conn = psycopg2.connect(conn_string)

app = flask.Flask(__name__)


def database_connection

#SELECT distinct("date") FROM "bulletin-2".occurrences ORDER BY "date" DESC LIMIT 2;

def get_permissions(user_id):
    return ["admin"]


@app.route('/')
def index():
    user_info = {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@example.com",
        "name": "John Doe",
    }
    return flask.render_template(
        'index.html.j2',
        bulletin_config=bulletin_config,
        permissions=get_permissions(1),
        user_info=user_info
    )
