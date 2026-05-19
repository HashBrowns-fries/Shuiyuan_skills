import argparse
import json
from bs4 import BeautifulSoup

from shuiyuan_client import BASE_URL, ShuiyuanClient


def extract_polls_from_post(post):
    polls = []

    if post.get("polls"):
        for poll in post.get("polls", []):
            polls.append(
                {
                    "source": "post.polls",
                    "post_id": post.get("id"),
                    "post_number": post.get("post_number"),
                    "poll": poll,
                }
            )

    cooked = post.get("cooked", "") or ""
    soup = BeautifulSoup(cooked, "html.parser")

    for div in soup.select(".poll, [data-poll-name], [data-poll-type]"):
        attrs = dict(div.attrs)
        text = div.get_text("\n", strip=True)
        polls.append(
            {
                "source": "cooked_html",
                "post_id": post.get("id"),
                "post_number": post.get("post_number"),
                "attrs": attrs,
                "text": text,
            }
        )

    return polls


def main():
    parser = argparse.ArgumentParser(description="获取某一主题下投票信息")
    parser.add_argument("topic_id", type=int)
    parser.add_argument("--raw", action="store_true", help="额外输出原始 post 中的 poll 相关字段")
    args = parser.parse_args()

    client = ShuiyuanClient()
    posts = client.topic_posts_all(args.topic_id)

    all_polls = []
    for post in posts:
        all_polls.extend(extract_polls_from_post(post))

    result = {
        "topic_id": args.topic_id,
        "topic_url": f"{BASE_URL}/t/{args.topic_id}",
        "poll_count": len(all_polls),
        "polls": all_polls,
    }

    print(json.dumps(result, ensure_ascii=False, indent=2))

    if len(all_polls) == 0:
        print("\n没有在该主题的公开 JSON/HTML 中发现投票信息。")
        print("可能原因：该主题没有投票；投票信息需前端额外接口加载；或你的账号没有查看权限。")


if __name__ == "__main__":
    main()