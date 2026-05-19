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
    parser = argparse.ArgumentParser(description="汇总帖子，并可在人工确认后发送单条回复")
    parser.add_argument("topic_id", type=int)
    parser.add_argument("--limit", type=int, default=20, help="汇总前多少楼")
    parser.add_argument("--text-limit", type=int, default=1200)
    parser.add_argument("--digest-output", help="把汇总写入文件")
    parser.add_argument("--prepare-reply", help="生成一个待编辑回复 Markdown 文件")
    parser.add_argument("--reply-file", help="读取该 Markdown 文件作为回复内容")
    parser.add_argument("--send", action="store_true", help="发送回复。仍需输入'确认发送'。")
    args = parser.parse_args()

    client = ShuiyuanClient()
    digest = build_digest(client, args.topic_id, args.limit, args.text_limit)

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
        print("编辑完成后运行：")
        print(f"python summarize_reply_confirmed.py {args.topic_id} --reply-file {path} --send")

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
        print(f"目标帖子: {BASE_URL}/t/{args.topic_id}")

        confirm = input('输入"确认发送"才会发布：').strip()
        if confirm != "确认发送":
            print("已取消，不发送。")
            return

        result = client.reply_topic(args.topic_id, raw)
        print("回复已发送。")
        print(result)


if __name__ == "__main__":
    main()