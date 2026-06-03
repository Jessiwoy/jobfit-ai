from __future__ import annotations

import json
from typing import Any


def decode_string_list(value: str | None) -> list[str]:
    if not value:
        return []

    data = json.loads(value)
    if not isinstance(data, list):
        return []

    return [str(item) for item in data if str(item).strip()]


def encode_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)

