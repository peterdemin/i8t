import json
import os
from unittest import mock

import requests

from i8t.collect import main

HERE = os.path.dirname(__file__)
TESTDATA = os.path.join(HERE, "testdata")
RAW_SESSION_PATH = os.path.join(TESTDATA, "raw-session-02.jsonl")
COLLECTED_SESSION_PATH = os.path.join(TESTDATA, "session-02.jsonl")


def test_collect_prints_jsonl() -> None:
    with open(RAW_SESSION_PATH, encoding="utf-8") as fobj:
        raw_session = json.load(fobj)
    with open(COLLECTED_SESSION_PATH, encoding="utf-8") as fobj:
        collected_session = list(fobj)
    assert len(raw_session) == len(collected_session)
    mock_session = mock.Mock(requests.Session)
    mock_session.get.return_value.json.return_value = raw_session
    with mock.patch("i8t.collect.time.sleep") as mock_sleep:
        mock_sleep.side_effect = KeyboardInterrupt()
        with mock.patch("i8t.collect.print") as mock_print:
            main(mock_session)
    assert len(mock_print.call_args_list) == len(raw_session) * 2
    printed = [call[0][0] + "\n" for call in mock_print.call_args_list if not call[1].get("file")]
    assert printed == collected_session
