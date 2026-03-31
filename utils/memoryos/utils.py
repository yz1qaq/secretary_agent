import json
import math
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


def ensure_parent_dir(file_path: Path) -> None:
    file_path.parent.mkdir(parents=True, exist_ok=True)


def load_json_file(file_path: Path, default: dict[str, Any]) -> dict[str, Any]:
    if not file_path.exists():
        return default

    content = file_path.read_text(encoding="utf-8").strip()
    if not content:
        return default

    try:
        payload = json.loads(content)
    except json.JSONDecodeError:
        return default

    if not isinstance(payload, dict):
        return default
    return payload


def save_json_file(file_path: Path, payload: dict[str, Any]) -> None:
    ensure_parent_dir(file_path)
    file_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def normalize_text(text: str) -> str:
    return " ".join((text or "").strip().lower().split())


def excerpt(text: str, max_length: int = 180) -> str:
    clean = " ".join((text or "").strip().split())
    if len(clean) <= max_length:
        return clean
    return f"{clean[:max_length]}..."


def tokenize_text(text: str) -> list[str]:
    normalized = normalize_text(text)
    if not normalized:
        return []

    latin_tokens = re.findall(r"[a-z0-9_]+", normalized)
    chinese_chars = [char for char in normalized if "\u4e00" <= char <= "\u9fff"]

    tokens = list(latin_tokens)
    tokens.extend(chinese_chars)
    tokens.extend(
        f"{chinese_chars[index]}{chinese_chars[index + 1]}"
        for index in range(len(chinese_chars) - 1)
    )
    return [token for token in tokens if token]


def cosine_similarity(a_tokens: list[str], b_tokens: list[str]) -> float:
    if not a_tokens or not b_tokens:
        return 0.0

    a_counter = Counter(a_tokens)
    b_counter = Counter(b_tokens)
    shared = set(a_counter) & set(b_counter)
    numerator = sum(a_counter[token] * b_counter[token] for token in shared)
    if numerator <= 0:
        return 0.0

    a_norm = math.sqrt(sum(value * value for value in a_counter.values()))
    b_norm = math.sqrt(sum(value * value for value in b_counter.values()))
    if a_norm == 0 or b_norm == 0:
        return 0.0

    return numerator / (a_norm * b_norm)


def score_text(query: str, candidate: str) -> float:
    return cosine_similarity(tokenize_text(query), tokenize_text(candidate))


def dedupe_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        normalized = normalize_text(value)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        result.append(value.strip())
    return result
