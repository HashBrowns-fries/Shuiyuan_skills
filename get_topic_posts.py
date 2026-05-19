import argparse
import csv
import json
from pathlib import Path

from shuiyuan_client import BASE_URL, ShuiyuanClient
from text_utils import html_to_text


def normalize_post(post):
    return {
        "id": post.get("id"),
        "topic_id": post.get("topic_id"),
        "post_number": post.get("post_number"),
        "username": post.get("username"),
        "name": post.get("name"),
        "created_at": post.get("created_at"),
        "updated_at": post.get("updated_at"),
        "reply_count": post.get("reply_count"),
        "like_count": post.get("like_count"),
        "score": post.get("score"),
        "cooked": post.get("cooked"),
        "text": html_to_text(post.get("cooked", "")),
        "post_url": f"{BASE_URL}/t/{post.get('topic_id')}/{post.get('post_number')}",
    }


def write_json(path: Path, rows):
    path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")


def write_csv(path: Path, rows):
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields = ["id", "topic_id", "post_number", "username", "name", "created_at", "like_count", "reply_count", "text", "post_url"]
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description="获取某一主题下所有 posts")
    parser.add_argument("topic_id", type=int)
    parser.add_argument("--limit", type=int, help="最多获取多少楼")
    parser.add_argument("--output", help="输出文件，支持 .json / .csv / .txt")
    args = parser.parse_args()

    client = ShuiyuanClient()
    posts = client.topic_posts_all(args.topic_id, limit=args.limit)
    rows = [normalize_post(p) for p in posts]

    if args.output:
        path = Path(args.output)
        if path.suffix.lower() == ".json":
            write_json(path, rows)
        elif path.suffix.lower() == ".csv":
            write_csv(path, rows)
        else:
            text = "\n\n".join(
                f"#{r['post_number']} {r['username']} | {r['created_at']}\n{r['post_url']}\n{'-'*80}\n{r['text']}"
                for r in rows
            )
            path.write_text(text, encoding="utf-8")
        print(f"已写入 {path.resolve()}，共 {len(rows)} 条 posts")
    else:
        print(json.dumps(rows, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()