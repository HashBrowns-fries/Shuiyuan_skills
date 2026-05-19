import argparse
from shuiyuan_client import ShuiyuanClient


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--title", required=True, help="主题标题")
    parser.add_argument("--category", required=True, type=int, help="分类 ID")
    parser.add_argument("--file", help="从 Markdown 文件读取正文")
    args = parser.parse_args()

    if args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            raw = f.read().strip()
    else:
        print("请输入正文，输入 END 单独一行结束：")
        lines = []
        while True:
            line = input()
            if line == "END":
                break
            lines.append(line)
        raw = "\n".join(lines).strip()

    if not args.title.strip():
        raise ValueError("标题不能为空")

    if not raw:
        raise ValueError("正文不能为空")

    print("\n即将发布主题：")
    print("=" * 80)
    print(f"标题: {args.title}")
    print(f"分类 ID: {args.category}")
    print("-" * 80)
    print(raw)
    print("=" * 80)

    confirm = input('输入"确认发送"才会发布：').strip()

    if confirm != "确认发送":
        print("已取消，不发送。")
        return

    client = ShuiyuanClient()
    result = client.create_topic(
        title=args.title.strip(),
        raw=raw,
        category_id=args.category,
    )

    topic_id = result.get("topic_id")

    print("主题已发布。")
    print(result)

    if topic_id:
        print(f"链接: https://shuiyuan.sjtu.edu.cn/t/{topic_id}")


if __name__ == "__main__":
    main()