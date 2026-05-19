import json
from pathlib import Path
from typing import Set

SEEN_FILE = Path("./seen_topics.json")


def load_seen() -> Set[int]:
    if not SEEN_FILE.exists():
        return set()
    try:
        data = json.loads(SEEN_FILE.read_text(encoding="utf-8"))
        return set(int(x) for x in data)
    except Exception:
        return set()


def save_seen(seen: Set[int]):
    SEEN_FILE.write_text(
        json.dumps(sorted(seen), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def mark_seen(topic_id: int):
    seen = load_seen()
    seen.add(int(topic_id))
    save_seen(seen)