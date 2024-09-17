import json
import os
from unittest import mock

import pytest

from i8t.testing.loader import (
    load_flask_calls,
    load_requests_mocks,
    load_test_cases,
    patch_checkpoints,
)

from .app import app, main, square

HERE = os.path.dirname(__file__)
TESTDATA = os.path.join(HERE, "testdata")
SESSION = os.path.join(TESTDATA, "session-01.jsonl")


@pytest.mark.parametrize(*load_test_cases(SESSION, "square"))
def test_square(case):
    assert square(*case.args, *case.kwargs) == case.expected


@pytest.mark.parametrize(*load_flask_calls(SESSION, "/another"))
def test_another_endpoint(case):
    with patch_checkpoints(SESSION, "toy.*", within=case) as expected_calls:
        with app.test_client() as client:
            response = client.open(
                case.url, method=case.method, json=case.json, headers=case.headers
            )
    for checkpoint in expected_calls:
        assert checkpoint.mock_obj.call_args_list == checkpoint.call_args_list
    assert response.status_code == case.expected_status_code
    assert response.json == json.loads(case.expected_body)


@pytest.mark.parametrize(*load_flask_calls(SESSION, "/example"))
def test_example_endpoint(case):
    with load_requests_mocks(SESSION, within=case):
        with app.test_client() as client:
            response = client.open(
                case.url, method=case.method, json=case.json, headers=case.headers
            )
    assert response.status_code == case.expected_status_code
    assert response.json == json.loads(case.expected_body)


def test_main():
    mock_app = mock.Mock(app)
    main(mock_app)
    mock_app.run.assert_called_once_with(debug=True)
