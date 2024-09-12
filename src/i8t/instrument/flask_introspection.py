import time

import flask

from ..client import IntrospectionClient


class FlaskIntrospection:
    def __init__(self, client: IntrospectionClient) -> None:
        self._client = client

    def register(self, app: flask.Flask) -> None:
        app.before_request(self.before_request)
        app.after_request(self.after_request)

    def before_request(self) -> None:
        flask.g.start_time = time.time()

    def after_request(self, response: flask.Response) -> flask.Response:
        self._client.send(
            self._client.make_checkpoint(
                "flask",
                {
                    "method": flask.request.method,
                    "url": flask.request.url,
                    "headers": dict(flask.request.headers),
                    "body": flask.request.get_data(as_text=True),
                },
                {
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "body": response.get_data(as_text=True),
                },
                time.time() - flask.g.start_time,
            )
        )
        return response
