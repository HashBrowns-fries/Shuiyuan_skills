import argparse
import time
import webbrowser

from shuiyuan_client import BASE_URL, ShuiyuanClient
from seen_store import load_seen, mark_seen
from text_utils import html_to_text, shorten


def print_topic(client: ShuiyuanClient, topic_id: int, post_limit: int, text_limit: int):
    topic = client.topic(topic_id)
    title = topic.get("title")
    posts = topic.get("post_stream", {}).get("posts", [])

    print("\n" + "=" * 100)
    print(f"标题: {title}")
    print(f"链接: {BASE_URL}/t/{topic_id}")
    print("=" * 100)

    for post in posts[:post_limit]:
        username = post.get("username")
        post_number = post.get("post_number")
        created_at = post.get("created_at")
        text = html_to_text(post.get("cooked", ""))

        print(f"\n#{post_number} {username} | {created_at}")
        print("-" * 80)
        print(shorten(text, text_limit))


def main():
    parser = argparse.ArgumentParser(description="浏览水源最新帖子，只读，不回复")
    parser.add_argument("--count", type=int, default=10, help="浏览最新多少个帖子")
    parser.add_argument("--post-limit", type=int, default=3, help="每个帖子最多显示几楼")
    parser.add_argument("--text-limit", type=int, default=800, help="每楼最多显示多少字")
    parser.add_argument("--keyword", help="只看标题中包含关键词的帖子")
    parser.add_argument("--unseen-only", action="store_true", help="只看没看过的帖子")
    parser.add_argument("--open-browser", action="store_true", help="同时用浏览器打开帖子")
    parser.add_argument("--delay", type=float, default=2.0, help="每个帖子之间等待秒数")
    args = parser.parse_args()

    client = ShuiyuanClient()
    data = client.latest_topics()

    topics = data.get("topic_list", {}).get("topics", [])
    seen = load_seen()
    selected = []

    for t in topics:
        topic_id = t.get("id")
        title = t.get("title", "")

        if not topic_id:
            continue
        if args.keyword and args.keyword not in title:
            continue
        if args.unseen_only and int(topic_id) in seen:
            continue

        selected.append(t)
        if len(selected) >= args.count:
            break

    if not selected:
        print("没有找到符合条件的新帖子。")
        return

    for t in selected:
        topic_id = int(t["id"])
        if args.open_browser:
            webbrowser.open(f"{BASE_URL}/t/{topic_id}")

        print_topic(client, topic_id, args.post_limit, args.text_limit)
        mark_seen(topic_id)
        time.sleep(max(args.delay, 1.0))


if __name__ == "__main__":
    main()