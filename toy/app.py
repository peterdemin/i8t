import flask
import requests

from i8t.client import IntrospectClient, IntrospectDecorator, introspect
from i8t.instrument.flask_introspect import FlaskIntrospect
from i8t.instrument.requests_introspect import RequestsIntrospect

app = flask.Flask(__name__)


def main(app_: flask.Flask) -> None:
    introspect_client = IntrospectClient(
        session=requests.Session(),
        api_url="https://api.demin.dev/i8t/t",
        name="app",
    )
    FlaskIntrospect(introspect_client).register(app_)
    RequestsIntrospect(introspect_client).register()
    IntrospectDecorator(introspect_client).register()
    app_.run(debug=True)


@app.route("/example", methods=["GET", "POST"])
def example_route():
    response = requests.post(
        app.url_for("another", _external=True),
        json={"number": flask.request.args.get("number", 0)},
        timeout=1.0,
    )
    response.raise_for_status()
    return {"message": response.text}


@app.route("/another", methods=["GET", "POST"])
def another():
    return process(flask.request.json)


@introspect
def process(payload):
    return {"square": payload.get("number", 0) ** 2}


if __name__ == "__main__":
    main(app)
