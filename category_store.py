"""이벤트별 공개 카테고리(private/busy/public)를 파일에 저장."""
from __future__ import annotations

import json
import os

PATH = "categories.json"
_LEGACY_HIDDEN = "hidden.json"  # 구버전: 숨김 set → private 로 이관

VALID = {"private", "busy", "public"}


def load() -> dict[str, str]:
    if os.path.exists(PATH):
        try:
            with open(PATH, encoding="utf-8") as f:
                return {k: v for k, v in json.load(f).items() if v in VALID}
        except Exception:
            return {}
    # 구버전 hidden.json 이 있으면 private 로 이관
    if os.path.exists(_LEGACY_HIDDEN):
        try:
            with open(_LEGACY_HIDDEN, encoding="utf-8") as f:
                migrated = {k: "private" for k in json.load(f)}
            _save(migrated)
            return migrated
        except Exception:
            return {}
    return {}


def _save(data: dict[str, str]) -> None:
    with open(PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=0, sort_keys=True)


def set_category(key: str, category: str) -> None:
    if category not in VALID:
        raise ValueError(category)
    data = load()
    data[key] = category
    _save(data)
