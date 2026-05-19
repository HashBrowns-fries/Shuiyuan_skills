import argparse
import csv
import json
from pathlib import Path

from shuiyuan_client import BASE_URL, ShuiyuanClient


def normalize_action(a):
    topic_id = a.get("topic_id")
    post_number = a.get("post_number")
    url = None
    if topic_id:
        url = f"{BASE_URL}/t/{topic_id}"
        if post_number:
            url += f"/{post_number}"

    return {
        "username": a.get("username"),
        "name": a.get("name"),
        "filter_type": a.get("_filter_type"),
        "action_type": "topic" if a.get("_filter_type") == 4 else "reply" if a.get("_filter_type") == 5 else a.get("_filter_type"),
        "post_id": a.get("post_id"),
        "topic_id": topic_id,
        "post_number": post_number,
        "title": a.get("title"),
        "excerpt": a.get("excerpt"),
        "created_at": a.get("created_at"),
        "url": url,
    }


def write_csv(path: Path, rows):
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields = ["username", "action_type", "post_id", "topic_id", "post_number", "title", "excerpt", "created_at", "url"]
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description="获取某一用户所有 posts，包括主题和回复")
    parser.add_argument("username")
    parser.add_argument("--limit", type=int, default=300)
    parser.add_argument("--topics-only", action="store_true")
    parser.add_argument("--replies-only", action="store_true")
    parser.add_argument("--output", help="输出 .json/.csv/.txt")
    args = parser.parse_args()

    include_topics = not args.replies_only
    include_replies = not args.topics_only

    client = ShuiyuanClient()
    actions = client.user_posts(
        username=args.username,
        include_topics=include_topics,
        include_replies=include_replies,
        limit=args.limit,
    )

    rows = [normalize_action(a) for a in actions]

    if args.output:
        path = Path(args.output)
        if path.suffix.lower() == ".json":
            path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
        elif path.suffix.lower() == ".csv":
            write_csv(path, rows)
        else:
            text = "\n\n".join(
                f"[{r['action_type']}] {r['created_at']} {r['title']}\n{r['url']}\n{r['excerpt'] or ''}"
                for r in rows
            )
            path.write_text(text, encoding="utf-8")
        print(f"已写入 {path.resolve()}，共 {len(rows)} 条")
    else:
        print(json.dumps(rows, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()