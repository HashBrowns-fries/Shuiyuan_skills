import argparse
from shuiyuan_client import ShuiyuanClient


def main():
    parser = argparse.ArgumentParser(description="删除自己的回复")
    parser.add_argument("post_id", type=int, help="要删除的帖子 ID")
    args = parser.parse_args()

    client = ShuiyuanClient()

    # 先获取 post 信息确认是本人的
    try:
        post = client.post_by_id(args.post_id)
    except Exception as e:
        print(f"获取帖子失败: {e}")
        return

    if not post:
        print("帖子不存在")
        return

    username = post.get("username")
    can_delete = post.get("can_delete")

    print(f"帖子 ID: {args.post_id}")
    print(f"发布者: {username}")
    print(f"是否能删除: {can_delete}")

    if not can_delete:
        print("无法删除：你不是发帖者或没有删除权限")
        return

    print("\n即将删除此回复。")
    confirm = input('输入"确认删除"才会删除：').strip()
    if confirm != "确认删除":
        print("已取消，不删除。")
        return

    result = client.delete_post(args.post_id)
    print("删除成功")
    print(result)


if __name__ == "__main__":
    main()