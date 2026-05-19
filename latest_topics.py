from shuiyuan_client import ShuiyuanClient


def main():
    client = ShuiyuanClient()
    data = client.latest_topics()

    topics = data.get("topic_list", {}).get("topics", [])

    for t in topics[:20]:
        topic_id = t.get("id")
        title = t.get("title")
        posts_count = t.get("posts_count")
        reply_count = t.get("reply_count")
        last_posted_at = t.get("last_posted_at")

        print("=" * 80)
        print(f"ID: {topic_id}")
        print(f"标题: {title}")
        print(f"回复数: {reply_count}")
        print(f"总楼层: {posts_count}")
        print(f"最后活动: {last_posted_at}")
        print(f"链接: https://shuiyuan.sjtu.edu.cn/t/{topic_id}")


if __name__ == "__main__":
    main()