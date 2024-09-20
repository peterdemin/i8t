import json
import os
from unittest import mock

import pytest

from i8t.adapters.decorator_adapter.loader import DecoratedCase, DecoratedPatch
from i8t.adapters.flask_adapter.loader import FlaskCase
from i8t.adapters.requests_adapter.loader import RequestsMock
from i8t.testing.session import IntrospectSession

from .app import Calculator, Multiplier, app, main, square

SESSION = IntrospectSession.from_jsonl(
    os.path.join(
        os.path.dirname(__file__),
        "testdata",
        "session-01.jsonl",
    ),
    main_is="toy.app",
)
SHORT_SESSION = IntrospectSession.from_jsonl(
    os.path.join(
        os.path.dirname(__file__),
        "testdata",
        "session-04.jsonl",
    ),
    main_is="toy.app",
)


@pytest.mark.parametrize("case", DecoratedCase.load(SESSION, "identity"))
def test_identity(case):
    multiplier = Multiplier(0)
    assert multiplier.identity(*case.args, *case.kwargs) == case.expected


@pytest.mark.parametrize("case", DecoratedCase.load(SESSION, "mul"))
def test_mul(case):
    multiplier = Multiplier(case.args[0])
    assert multiplier.mul(*case.args, *case.kwargs) == case.expected


@pytest.mark.parametrize("case", DecoratedCase.load(SESSION, "calculate"))
def test_calculate(case):
    calculator = Calculator()
    assert calculator.calculate(*case.args, *case.kwargs) == case.expected


@pytest.mark.parametrize("case", DecoratedCase.load(SESSION, "calculate2"))
def test_calculate2(case):
    calculator = Calculator()
    with DecoratedPatch.activate(SESSION, "[M]*.*", within=case) as decorated_patches:
        assert calculator.calculate2(*case.args, *case.kwargs) == case.expected
    patch_names = " ".join(p.qualname for p in decorated_patches)
    assert "Multiplier.mul" in patch_names
    assert "Multiplier.identity" in patch_names
    for decorated_patch in decorated_patches:
        assert decorated_patch.mock_obj.call_args_list == decorated_patch.call_args_list


@pytest.mark.parametrize("case", DecoratedCase.load(SESSION, "square"))
def test_square(case):
    with DecoratedPatch.activate(SESSION, "[C]*.*", within=case) as decorated_patches:
        assert square(*case.args, *case.kwargs) == case.expected
    for decorated_patch in decorated_patches:
        assert decorated_patch.mock_obj.call_args_list == decorated_patch.call_args_list
    patch_names = " ".join(p.qualname for p in decorated_patches)
    assert "Calculator.calculate" in patch_names


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


@pytest.mark.parametrize("case", FlaskCase.load(SHORT_SESSION, "/example"))
def test_example_endpoint_in_short_session(case: FlaskCase) -> None:
    # There's only one requests checkpoint in the session, don't need within:
    with RequestsMock.activate(SESSION):
        with app.test_client() as client:
            response = case.call(client)
    assert response.status_code == case.expected_status_code
    assert response.json == json.loads(case.expected_body)


def test_main():
    mock_app = mock.Mock(app)
    main(mock_app)
    mock_app.run.assert_called_once_with(debug=True)
