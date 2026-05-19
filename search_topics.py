import argparse
from shuiyuan_client import ShuiyuanClient


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("keyword", help="搜索关键词")
    parser.add_argument("--page", type=int, default=1, help="页码")
    args = parser.parse_args()

    client = ShuiyuanClient()
    data = client.search(args.keyword)

    topics = data.get("topics", [])

    if not topics:
        print("没有找到相关帖子")
        return

    for t in topics:
        topic_id = t.get("id")
        title = t.get("title")
        posts_count = t.get("posts_count")
        like_count = t.get("like_count")

        print("=" * 80)
        print(f"ID: {topic_id}")
        print(f"标题: {title}")
        print(f"楼层数: {posts_count}")
        print(f"点赞数: {like_count}")
        print(f"链接: https://shuiyuan.sjtu.edu.cn/t/{topic_id}")


if __name__ == "__main__":
    main()