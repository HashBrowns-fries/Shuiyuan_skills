import argparse
from shuiyuan_client import ShuiyuanClient


def main():
    parser = argparse.ArgumentParser(description="给帖子贴表情")
    parser.add_argument("post_id", type=int, help="帖子 ID")
    parser.add_argument("emoji", nargs="?", help="表情名称（如 like, heart）")
    parser.add_argument("--remove", action="store_true", help="移除表情")
    parser.add_argument("--yes", action="store_true", help="跳过确认")
    args = parser.parse_args()

    client = ShuiyuanClient()

    # 获取帖子信息
    post = client.post_by_id(args.post_id)
    if not post:
        print("帖子不存在")
        return

    print(f"帖子: {post.get('title', 'Untitled')}")
    print(f"ID: {args.post_id}, 用户: {post.get('username')}")
    print(f"can_retort: {post.get('can_retort')}")

    if not post.get("can_retort"):
        print("无法贴表情：没有权限")
        return

    if args.remove:
        emoji_to_use = args.emoji
    elif args.emoji:
        emoji_to_use = args.emoji
    else:
        print("\n当前表情:")
        my_retorts = post.get("my_retorts", [])
        if my_retorts:
            for r in my_retorts:
                print(f"  - {r.get('emoji')}")
        else:
            print("  (无)")

        emoji_to_use = input("\n输入要贴的表情名称: ").strip()

    if not emoji_to_use:
        print("未提供表情名称")
        return

    print("\n即将执行:")
    print(f"  post_id: {args.post_id}")
    print(f"  emoji: {emoji_to_use}")
    print(f"  remove: {args.remove}")

    if not args.yes:
        confirm = input('\n输入"确认贴表情"才会继续: ').strip()
        if confirm != "确认贴表情":
            print("已取消")
            return

    result = client.retort_post(
        post_id=args.post_id,
        emoji=emoji_to_use,
        remove=args.remove,
    )

    print("操作成功")
    post = client.post_by_id(args.post_id)
    my_retorts = post.get("my_retorts", [])
    print("当前表情:")
    for r in my_retorts:
        print(f"  - {r.get('emoji')}")


if __name__ == "__main__":
    main()