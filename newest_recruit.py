import argparse
import json
from datetime import datetime, timedelta, timezone
from typing import Dict

from shuiyuan_client import BASE_URL, ShuiyuanClient
from text_utils import html_to_text, shorten


def parse_time(s):
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return None


def main():
    parser = argparse.ArgumentParser(description="获取最近一段时间的招募/招新/招人信息")
    parser.add_argument("--days", type=int, default=15, help="默认近半个月")
    parser.add_argument("--keywords", default="招募,招新,招人,招聘,志愿者,内推,实习,项目组,课题组,实验室招", help="逗号分隔")
    parser.add_argument("--count", type=int, default=50)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    client = ShuiyuanClient()
    since = datetime.now(timezone.utc) - timedelta(days=args.days)
    after = since.strftime("%Y-%m-%d")
    keywords = [x.strip() for x in args.keywords.split(",") if x.strip()]

    topics_by_id: Dict[int, dict] = {}

    for kw in keywords:
        query = f"{kw} after:{after}"
        try:
            data = client.search(query)
        except Exception as e:
            print(f"搜索 {query!r} 失败: {e}")
            continue

        for t in data.get("topics", []) or []:
            topic_id = t.get("id")
            if not topic_id or topic_id in topics_by_id:
                continue
            topics_by_id[int(topic_id)] = {
                "id": int(topic_id),
                "title": t.get("title"),
                "created_at": t.get("created_at"),
                "last_posted_at": t.get("last_posted_at"),
                "posts_count": t.get("posts_count"),
                "like_count": t.get("like_count"),
                "matched_keyword": kw,
                "url": f"{BASE_URL}/t/{topic_id}",
            }

    results = []
    for topic_id, item in topics_by_id.items():
        created = parse_time(item.get("created_at") or item.get("last_posted_at"))
        if created and created < since:
            continue

        try:
            topic = client.topic(topic_id)
            posts = topic.get("post_stream", {}).get("posts", [])
            if posts:
                item["excerpt"] = shorten(html_to_text(posts[0].get("cooked", "")), 500)
        except Exception:
            item["excerpt"] = ""

        results.append(item)

    results.sort(key=lambda x: x.get("created_at") or x.get("last_posted_at") or "", reverse=True)
    results = results[: args.count]

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        print(f"近 {args.days} 天招募类信息，共 {len(results)} 条")
        for item in results:
            print("\n" + "=" * 100)
            print(f"标题: {item.get('title')}")
            print(f"关键词: {item.get('matched_keyword')}")
            print(f"时间: {item.get('created_at') or item.get('last_posted_at')}")
            print(f"链接: {item.get('url')}")
            if item.get("excerpt"):
                print("-" * 80)
                print(item["excerpt"])


if __name__ == "__main__":
    main()