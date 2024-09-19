from dataclasses import dataclass


@dataclass
class TimeRange:
    start_ts: float
    finish_ts: float
