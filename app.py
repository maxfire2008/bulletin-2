# flask app
import flask
import bulletin_config

app = flask.Flask(__name__)


@app.route('/')
def index():
    return flask.render_template('student-index.html.j2', bulletin_config=bulletin_config)
