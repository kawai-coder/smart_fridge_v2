from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, timedelta
from typing import Any, Iterable

DATE_FMT = "%Y-%m-%d"
DATETIME_FMT = "%Y-%m-%d %H:%M:%S"


def today() -> date:
    return date.today()


def now_ts() -> str:
    return datetime.utcnow().strftime(DATETIME_FMT)


def parse_date(value: str | None) -> date | None:
    if not value:
        return None
    return datetime.strptime(value, DATE_FMT).date()


def format_date(value: date | None) -> str | None:
    if value is None:
        return None
    return value.strftime(DATE_FMT)


def add_days(value: date, days: int) -> date:
    return value + timedelta(days=days)


def to_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False)


def from_json(value: str | None, default: Any) -> Any:
    if not value:
        return default
    return json.loads(value)


def stable_hash(value: str) -> int:
    return int(hashlib.sha256(value.encode("utf-8")).hexdigest(), 16) % (10**8)


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(value, maximum))


def sum_by_key(rows: Iterable[dict], key: str) -> float:
    return sum(float(row.get(key, 0) or 0) for row in rows)
