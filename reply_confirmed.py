import argparse
from shuiyuan_client import ShuiyuanClient


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("topic_id", type=int, help="要回复的帖子 ID")
    parser.add_argument("--file", help="从 Markdown 文件读取回复内容")
    args = parser.parse_args()

    if args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            raw = f.read().strip()
    else:
        print("请输入回复内容，输入 END 单独一行结束：")
        lines = []
        while True:
            line = input()
            if line == "END":
                break
            lines.append(line)
        raw = "\n".join(lines).strip()

    if not raw:
        raise ValueError("回复内容不能为空")

    print("\n即将发送以下回复：")
    print("=" * 80)
    print(raw)
    print("=" * 80)
    print(f"目标帖子: https://shuiyuan.sjtu.edu.cn/t/{args.topic_id}")

    confirm = input('输入"确认发送"才会发布：').strip()

    if confirm != "确认发送":
        print("已取消，不发送。")
        return

    client = ShuiyuanClient()
    result = client.reply_topic(topic_id=args.topic_id, raw=raw)

    print("回复已发送。")
    print(result)


if __name__ == "__main__":
    main()