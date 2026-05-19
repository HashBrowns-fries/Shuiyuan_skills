import argparse
import json
from collections import Counter

from shuiyuan_client import ShuiyuanClient
from text_utils import count_emojis_from_texts, html_to_text


def emoji_stats_for_username(client: ShuiyuanClient, username: str, limit: int):
    actions = client.user_posts(username, limit=limit)
    texts = []

    for a in actions:
        post_id = a.get("post_id")
        if post_id:
            try:
                post = client.post_by_id(int(post_id))
                texts.append(html_to_text(post.get("cooked", "")))
                continue
            except Exception:
                pass
        texts.append(a.get("excerpt") or "")

    return count_emojis_from_texts(texts), len(texts)


def emoji_stats_for_topic(client: ShuiyuanClient, topic_id: int, limit: int):
    posts = client.topic_posts_all(topic_id, limit=limit)
    texts = [html_to_text(p.get("cooked", "")) for p in posts]
    return count_emojis_from_texts(texts), len(texts)


def main():
    parser = argparse.ArgumentParser(description="统计用户或主题中使用了哪些 emoji")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--username", help="统计某个用户的 posts")
    group.add_argument("--topic-id", type=int, help="统计某个主题中的 posts")
    parser.add_argument("--limit", type=int, default=500)
    parser.add_argument("--top", type=int, default=50)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    client = ShuiyuanClient()

    if args.username:
        counter, scanned = emoji_stats_for_username(client, args.username, args.limit)
        subject = {"type": "username", "value": args.username}
    else:
        counter, scanned = emoji_stats_for_topic(client, args.topic_id, args.limit)
        subject = {"type": "topic_id", "value": args.topic_id}

    result = {
        "subject": subject,
        "posts_scanned": scanned,
        "total_emoji_count": sum(counter.values()),
        "unique_emoji_count": len(counter),
        "top": [{"emoji": k, "count": v} for k, v in counter.most_common(args.top)],
    }

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"统计对象: {subject}")
        print(f"扫描 posts: {scanned}")
        print(f"emoji 总数: {result['total_emoji_count']}")
        print(f"不同 emoji 数: {result['unique_emoji_count']}")
        print("-" * 40)
        for item in result["top"]:
            print(f"{item['emoji']}\t{item['count']}")


if __name__ == "__main__":
    main()