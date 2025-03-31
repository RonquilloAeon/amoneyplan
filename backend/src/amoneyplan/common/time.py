import datetime
import time


def get_utc_now() -> datetime.datetime:
    return datetime.datetime.now(datetime.UTC)


def get_timestamp_in_ns() -> int:
    return int(time.time() * 1_000_000_000)
