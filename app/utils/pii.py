from __future__ import annotations

import json
from typing import Any, Iterable, Set

REDACTION_TEXT = "***REDACTED***"


def _scrub(data: Any, pii_keys: Set[str]) -> Any:
    if isinstance(data, dict):
        return {
            key: (REDACTION_TEXT if key.lower() in pii_keys else _scrub(value, pii_keys))
            for key, value in data.items()
        }

    if isinstance(data, list):
        return [_scrub(item, pii_keys) for item in data]

    if isinstance(data, str):
        try:
            parsed = json.loads(data)
        except (json.JSONDecodeError, TypeError):
            return data
        return json.dumps(_scrub(parsed, pii_keys))

    return data


def scrub_pii(data: Any, pii_fields: Iterable[str]) -> Any:
    """
    Recursively scrub PII fields from dictionaries, lists, and JSON strings.

    Non-dict inputs are returned unchanged unless they are JSON strings that can be parsed.
    """
    pii_keys = {field.lower() for field in pii_fields}
    if not pii_keys:
        return data
    return _scrub(data, pii_keys)


