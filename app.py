# flask app
import flask
import bulletin_config

app = flask.Flask(__name__)


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
