import time

import flask

from i8t.adapters.flask_adapter.exporter import FlaskAdapter
from i8t.client import IntrospectClient


class FlaskIntrospect:
    def __init__(self, client: IntrospectClient) -> None:
        self._client = client
        self._flask_adapter = FlaskAdapter(client)

    def register(self, app: flask.Flask) -> None:
        app.before_request(self.before_request)
        app.after_request(self.after_request)

    def before_request(self) -> None:
        flask.g.start_time = time.time()

    def after_request(self, response: flask.Response) -> flask.Response:
        self._flask_adapter.record(flask.g.start_time, flask.request, response)
        return response
