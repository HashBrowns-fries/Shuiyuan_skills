import argparse
import json

from shuiyuan_client import BASE_URL, ShuiyuanClient
from text_utils import extract_image_links


def find_post_by_topic_post_number(client: ShuiyuanClient, topic_id: int, post_number: int):
    posts = client.topic_posts_all(topic_id)
    for post in posts:
        if int(post.get("post_number", -1)) == int(post_number):
            return post
    raise RuntimeError(f"在 topic {topic_id} 中找不到 post_number={post_number}")


def main():
    parser = argparse.ArgumentParser(description="获取某一 post 的所有图片链接")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--post-id", type=int, help="Discourse post id")
    group.add_argument("--topic-post", nargs=2, metavar=("TOPIC_ID", "POST_NUMBER"), help="通过 topic_id + 楼层号定位")
    parser.add_argument("--json", action="store_true", help="输出 JSON")
    args = parser.parse_args()

    client = ShuiyuanClient()

    if args.post_id:
        post = client.post_by_id(args.post_id)
    else:
        topic_id = int(args.topic_post[0])
        post_number = int(args.topic_post[1])
        post = find_post_by_topic_post_number(client, topic_id, post_number)

    links = extract_image_links(post.get("cooked", ""), BASE_URL)

    result = {
        "post_id": post.get("id"),
        "topic_id": post.get("topic_id"),
        "post_number": post.get("post_number"),
        "image_count": len(links),
        "images": links,
    }

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"post_id: {result['post_id']}")
        print(f"topic_id: {result['topic_id']}")
        print(f"post_number: {result['post_number']}")
        print(f"图片数量: {len(links)}")
        for link in links:
            print(link)


if __name__ == "__main__":
    main()