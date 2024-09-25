import os

import flask
import requests

from i8t import introspect
from i8t.client import IntrospectClient
from i8t.instrument.decorator_introspect import DecoratorIntrospect
from i8t.instrument.flask_introspect import FlaskIntrospect
from i8t.instrument.requests_introspect import RequestsIntrospect

app = flask.Flask(__name__)


def main(app_: flask.Flask) -> None:
    introspect_client = IntrospectClient(
        api_url=os.environ.get("I8T_URL", "https://api.demin.dev/i8t/toy"),
        name="app",
    )
    FlaskIntrospect(introspect_client).register(app_)
    RequestsIntrospect(introspect_client).register()
    DecoratorIntrospect(introspect_client).register()
    app_.run(debug=True)


@app.route("/example", methods=["GET", "POST"])
def example_route():
    response = requests.post(
        app.url_for("another", _external=True),
        json={"number": int(flask.request.values.get("number", "0"))},
        timeout=10.0,
    )
    response.raise_for_status()
    return {"message": response.json()}


@app.route("/another", methods=["GET", "POST"])
def another():
    return {"squares": [square(number) for number in range(flask.request.json.get("number", 0))]}


@introspect
def square(number: int) -> int:
    multiplier = Multiplier(number)
    calc = Calculator()
    calc.calculate(multiplier, number)
    return calc.calculate2(number)


class Multiplier:
    def __init__(self, number: int) -> None:
        self._number = number

    @introspect
    def mul(self, number: int) -> int:
        return self._number * number

    @introspect
    def identity(self, arg: int) -> int:
        return arg

    def __eq__(self, other: object) -> bool:
        return self._number == getattr(other, "_number", None)  # pragma: no cover


class Calculator:
    @introspect
    def calculate(self, multiplier: Multiplier, number: int) -> int:
        return multiplier.mul(multiplier.identity(number))

    @introspect
    def calculate2(self, number: int) -> int:
        multiplier = Multiplier(number)
        return multiplier.mul(multiplier.identity(number))


if __name__ == "__main__":
    main(app)  # pragma: no cover
