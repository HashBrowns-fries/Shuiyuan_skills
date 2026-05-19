import argparse
from pathlib import Path

from shuiyuan_client import BASE_URL, ShuiyuanClient
from text_utils import html_to_text, shorten


def build_digest(client: ShuiyuanClient, topic_id: int, limit: int = 20, text_limit: int = 1200):
    topic = client.topic(topic_id)
    title = topic.get("title")
    posts = client.topic_posts_all(topic_id, limit=limit)

    lines = []
    lines.append(f"标题: {title}")
    lines.append(f"链接: {BASE_URL}/t/{topic_id}")
    lines.append("=" * 100)

    for post in posts:
        username = post.get("username")
        post_number = post.get("post_number")
        created_at = post.get("created_at")
        text = shorten(html_to_text(post.get("cooked", "")), text_limit)

        lines.append("")
        lines.append(f"#{post_number} {username} | {created_at}")
        lines.append("-" * 80)
        lines.append(text)

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="查询并汇总帖子")
    parser.add_argument("query", help="搜索关键词，或 topic_id 直接查看")
    parser.add_argument("--limit", type=int, default=20, help="汇总前多少楼")
    parser.add_argument("--text-limit", type=int, default=1200, help="每楼最多显示字数")
    parser.add_argument("--digest-output", help="把汇总写入文件")
    parser.add_argument("--prepare-reply", help="生成回复草稿文件")
    parser.add_argument("--reply-file", help="读取该文件作为回复内容")
    parser.add_argument("--send", action="store_true", help="发送回复")
    args = parser.parse_args()

    client = ShuiyuanClient()

    # 判断是 topic_id 还是搜索关键词
    if args.query.isdigit():
        topic_id = int(args.query)
    else:
        # 搜索取第一个结果
        data = client.search(args.query)
        topics = data.get("topics", [])
        if not topics:
            print("没有找到相关帖子")
            return
        topic_id = topics[0].get("id")
        matched_title = topics[0].get("title")
        print(f"搜索「{args.query}」→ 选用帖子 #{topic_id}: {matched_title}")

    digest = build_digest(client, topic_id, args.limit, args.text_limit)
    print(digest)

    if args.digest_output:
        Path(args.digest_output).write_text(digest, encoding="utf-8")
        print(f"\n汇总已写入: {Path(args.digest_output).resolve()}")

    if args.prepare_reply:
        path = Path(args.prepare_reply)
        if not path.exists():
            path.write_text(
                "<!-- 在这里写回复内容。确认真实、相关、礼貌后再发送。 -->\n\n",
                encoding="utf-8",
            )
        print(f"\n已准备回复草稿文件: {path.resolve()}")

    if args.send:
        if not args.reply_file:
            raise ValueError("--send 必须配合 --reply-file 使用")

        raw = Path(args.reply_file).read_text(encoding="utf-8").strip()
        raw = "\n".join(
            line for line in raw.splitlines()
            if not line.strip().startswith("<!--")
        ).strip()

        if not raw:
            raise ValueError("回复内容为空")

        print("\n即将发送以下回复：")
        print("=" * 100)
        print(raw)
        print("=" * 100)
        print(f"目标帖子: {BASE_URL}/t/{topic_id}")

        confirm = input('输入"确认发送"才会发布：').strip()
        if confirm != "确认发送":
            print("已取消，不发送。")
            return

        result = client.reply_topic(topic_id, raw)
        print("回复已发送。")
        print(result)


if __name__ == "__main__":
    main()