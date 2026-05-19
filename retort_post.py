import argparse
from shuiyuan_client import ShuiyuanClient


def main():
    parser = argparse.ArgumentParser(description="给帖子贴表情")
    parser.add_argument("post_id", type=int, help="帖子 ID")
    parser.add_argument("emoji", nargs="?", help="表情名称（如 like, heart, warped_face）")
    parser.add_argument("--remove", action="store_true", help="移除表情")
    args = parser.parse_args()

    client = ShuiyuanClient()

    # 获取帖子信息
    post = client.post_by_id(args.post_id)
    if not post:
        print("帖子不存在")
        return

    print(f"帖子: {post.get('title', 'Untitled')}")
    print(f"ID: {args.post_id}, 楼主: {post.get('username')}")
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

        emoji_to_use = input("\n输入要贴的表情名称（或 new 安装新表情）: ").strip()

    if not emoji_to_use:
        print("未提供表情名称")
        return

    # 贴表情 API
    # Discourse retort endpoint: POST /posts/:id/retort
    csrf = client.get_csrf_token()
    url = f"{client.base_url}/posts/{args.post_id}/retort"

    if args.remove:
        data = {"emoji": emoji_to_use, "remove": True}
    else:
        data = {"emoji": emoji_to_use}

    resp = client.session.post(url, json=data, headers={"X-CSRF-Token": csrf}, timeout=30)

    if resp.ok or resp.status_code == 200:
        print("操作成功")
        # 刷新显示
        post = client.post_by_id(args.post_id)
        my_retorts = post.get("my_retorts", [])
        print("当前表情:")
        for r in my_retorts:
            print(f"  - {r.get('emoji')}")
    else:
        print(f"操作失败: {resp.status_code}")
        print(resp.text[:300])


if __name__ == "__main__":
    main()