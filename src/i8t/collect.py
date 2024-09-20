import json
import sys
import time
from typing import Iterable, Optional, Set

import requests


class CheckpointCollector:
    def __init__(self) -> None:
        self._all_records: Set[str] = set()

    def filter_new(self, latest: Iterable[str]) -> Iterable[str]:
        """Records latest lines and returns only new ones."""
        for line in latest:
            if line not in self._all_records:
                self._all_records.add(line)
                yield line


class CheckpointFetcher:
    def __init__(self, api_url: str, session: requests.Session) -> None:
        self._api_url = api_url
        self._session = session

    def fetch(self) -> Iterable[str]:
        response = self._session.get(self._api_url, timeout=1)
        for record in response.json():
            yield json.dumps(self._parse(record))

    def _parse(self, record: dict) -> dict:
        return dict(
            record,
            input=json.loads(record["input"]),
            output=json.loads(record["output"]),
        )


class CheckpointPoller:
    DEFAULT_DELAY_SEC = 1

    def __init__(
        self,
        checkpoint_fetcher: CheckpointFetcher,
        checkpoint_collector: CheckpointCollector,
        delay_sec: float = DEFAULT_DELAY_SEC,
    ) -> None:
        self._checkpoint_fetcher = checkpoint_fetcher
        self._checkpoint_collector = checkpoint_collector
        self._delay_sec = delay_sec

    def poll_once(self) -> Iterable[str]:
        yield from self._checkpoint_collector.filter_new(self._checkpoint_fetcher.fetch())

    def iter_lines(self) -> Iterable[str]:
        while True:
            try:
                yield from self.poll_once()
                time.sleep(self._delay_sec)
            except KeyboardInterrupt:
                break
            except Exception as exc:  # pylint: disable=broad-except
                print(f"WARNING: {exc}", file=sys.stderr)

    def print_forever(self) -> None:
        for i, line in enumerate(self.iter_lines()):
            print(f"\rCollected {i+1} checkpoints. Press Ctrl+C to stop.", file=sys.stderr, end="")
            print(line)


def main(session: Optional[requests.Session] = None) -> None:
    CheckpointPoller(
        checkpoint_fetcher=CheckpointFetcher(
            api_url=sys.argv[1],
            session=session or requests.Session(),
        ),
        checkpoint_collector=CheckpointCollector(),
    ).print_forever()


if __name__ == "__main__":
    main()  # pragma: no cover
