import argparse
import time
from datetime import datetime

from shuiyuan_client import BASE_URL, ShuiyuanClient
from seen_store import load_seen, mark_seen


def main():
    parser = argparse.ArgumentParser(description="持续巡查水源最新帖子，只读，不回复")
    parser.add_argument("--interval", type=int, default=300, help="每隔多少秒检查一次，最低 60")
    parser.add_argument("--count", type=int, default=20, help="每次检查最新多少个帖子")
    parser.add_argument("--keyword", help="只关注标题中包含关键词的帖子")
    args = parser.parse_args()

    interval = max(args.interval, 60)
    client = ShuiyuanClient()

    print("开始巡帖：只读取帖子列表，不会发帖或回复。")
    print(f"检查间隔: {interval} 秒")

    while True:
        try:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print("\n" + "=" * 100)
            print(f"检查时间: {now}")

            data = client.latest_topics()
            topics = data.get("topic_list", {}).get("topics", [])
            seen = load_seen()
            new_count = 0

            for t in topics[: args.count]:
                topic_id = t.get("id")
                title = t.get("title", "")
                reply_count = t.get("reply_count")
                last_posted_at = t.get("last_posted_at")

                if not topic_id:
                    continue
                if int(topic_id) in seen:
                    continue
                if args.keyword and args.keyword not in title:
                    continue

                new_count += 1
                print("-" * 100)
                print(f"新帖: {title}")
                print(f"ID: {topic_id}")
                print(f"回复数: {reply_count}")
                print(f"最后活动: {last_posted_at}")
                print(f"链接: {BASE_URL}/t/{topic_id}")
                mark_seen(int(topic_id))

            if new_count == 0:
                print("没有发现新帖。")

        except KeyboardInterrupt:
            print("\n已停止巡帖。")
            break
        except Exception as e:
            print(f"巡帖出错: {e}")

        time.sleep(interval)


if __name__ == "__main__":
    main()