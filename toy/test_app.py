import json
import os
from unittest import mock

import pytest

from i8t.adapters.decorator_adapter.loader import DecoratedCase, DecoratedPatch
from i8t.adapters.flask_adapter.loader import FlaskCase
from i8t.adapters.requests_adapter.loader import RequestsMock
from i8t.testing.session import IntrospectSession

from .app import MultiplyingCalculator, app, main, square

SESSION = IntrospectSession.from_jsonl(
    os.path.join(
        os.path.dirname(__file__),
        "testdata",
        "session-01.jsonl",
    ),
    main_is="toy.app",
)


@pytest.mark.parametrize("case", DecoratedCase.load(SESSION, "identity"))
def test_identity(case):
    calc = MultiplyingCalculator()
    assert calc.identity(*case.args, *case.kwargs) == case.expected


@pytest.mark.parametrize("case", DecoratedCase.load(SESSION, "mul"))
def test_mul(case):
    calc = MultiplyingCalculator()
    assert calc.mul(*case.args, *case.kwargs) == case.expected


@pytest.mark.parametrize("case", DecoratedCase.load(SESSION, "square"))
def test_square(case):
    with DecoratedPatch.activate(
        SESSION, "MultiplyingCalculator.*", within=case
    ) as decorated_patches:
        assert square(*case.args, *case.kwargs) == case.expected
    for decorated_patch in decorated_patches:
        assert decorated_patch.mock_obj.call_args_list == decorated_patch.call_args_list


@pytest.mark.parametrize("case", FlaskCase.load(SESSION, "/another"))
def test_another_endpoint(case: FlaskCase):
    with DecoratedPatch.activate(SESSION, ".square", within=case) as decorated_patches:
        with app.test_client() as client:
            response = case.call(client)
    assert response.status_code == case.expected_status_code
    assert response.json == json.loads(case.expected_body)
    for decorated_patch in decorated_patches:
        assert decorated_patch.mock_obj.call_args_list == decorated_patch.call_args_list


@pytest.mark.parametrize("case", FlaskCase.load(SESSION, "/example"))
def test_example_endpoint(case: FlaskCase) -> None:
    with RequestsMock.activate(SESSION, within=case):
        with app.test_client() as client:
            response = case.call(client)
    assert response.status_code == case.expected_status_code
    assert response.json == json.loads(case.expected_body)


def test_main():
    mock_app = mock.Mock(app)
    main(mock_app)
    mock_app.run.assert_called_once_with(debug=True)
