import argparse
from bs4 import BeautifulSoup
from shuiyuan_client import BASE_URL, ShuiyuanClient


def html_to_text(html: str) -> str:
    return BeautifulSoup(html or "", "html.parser").get_text("\n", strip=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("topic_id", type=int, help="帖子 ID")
    parser.add_argument("--limit", type=int, default=10, help="最多显示楼层数")
    args = parser.parse_args()

    client = ShuiyuanClient()
    topic = client.topic(args.topic_id)

    title = topic.get("title")
    posts = topic.get("post_stream", {}).get("posts", [])

    print(f"标题: {title}")
    print(f"链接: https://shuiyuan.sjtu.edu.cn/t/{args.topic_id}")
    print("=" * 80)

    for post in posts[: args.limit]:
        username = post.get("username")
        post_number = post.get("post_number")
        created_at = post.get("created_at")
        text = html_to_text(post.get("cooked", ""))

        print(f"\n#{post_number} {username} | {created_at}")
        print("-" * 80)
        print(text[:3000])


if __name__ == "__main__":
    main()