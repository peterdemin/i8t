from typing import Tuple

import flask

from i8t.client import IntrospectClient


class FlaskAdapter:
    LOCATION = "flask"

    def __init__(self, client: IntrospectClient) -> None:
        self._client = client

    def record(
        self, start_time: float, request: flask.Request, response: flask.Response
    ) -> flask.Response:
        self._send(self._for_success(start_time, request, response))
        return response

    def _send(self, checkpoint_params: Tuple) -> None:
        self._client.send(self._client.make_checkpoint(*checkpoint_params))

    def _for_success(
        self, start_time: float, request: flask.Request, response: flask.Response
    ) -> Tuple:
        return (
            "flask",
            {
                "method": request.method,
                "url": request.url,
                "headers": dict(request.headers),
                "args": request.args,
                "form": request.form,
                "json": request.get_json(silent=True),
                "data": request.get_data(as_text=True),
            },
            {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "body": response.get_data(as_text=True),
            },
            start_time,
        )
