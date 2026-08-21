from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def clean(value: object) -> str:
    return "" if value is None else str(value).strip()


def optional_id(value: object) -> str | None:
    text = clean(value)
    return text or None


def row_to_dict(row: sqlite3.Row | None) -> dict | None:
    return dict(row) if row else None


def rows_to_list(rows: list[sqlite3.Row]) -> list[dict]:
    return [dict(row) for row in rows]


def normalize_permissions(value: object) -> str:
    if isinstance(value, list):
        permissions = [clean(item) for item in value if clean(item)]
    else:
        try:
            parsed = json.loads(clean(value) or "[]")
            permissions = [clean(item) for item in parsed if clean(item)] if isinstance(parsed, list) else []
        except json.JSONDecodeError:
            permissions = []
    unique_permissions = list(dict.fromkeys(permissions))
    return json.dumps(unique_permissions, ensure_ascii=False)


def normalize_participants(value: object) -> str:
    if isinstance(value, list):
        raw_items = value
    else:
        try:
            parsed = json.loads(clean(value) or "[]")
            raw_items = parsed if isinstance(parsed, list) else []
        except json.JSONDecodeError:
            raw_items = []

    participants = []
    for item in raw_items:
        if not isinstance(item, dict):
            continue
        role = clean(item.get("role"))
        user = clean(item.get("user"))
        if role or user:
            participants.append({"role": role, "user": user})
    return json.dumps(participants, ensure_ascii=False)


def participant_owner(participants_json: str) -> str:
    try:
        participants = json.loads(participants_json or "[]")
    except json.JSONDecodeError:
        return ""
    if not isinstance(participants, list):
        return ""
    for participant in participants:
        if isinstance(participant, dict) and clean(participant.get("user")):
            return clean(participant.get("user"))
    return ""
