import argparse
import json
import time
from pathlib import Path
from datetime import datetime

from shuiyuan_client import BASE_URL, ShuiyuanClient


SEEN_FILE = Path("./seen_notifications.json")

# Discourse Notification.types
# mentioned=1, replied=2, quoted=3
NOTIFICATION_TYPES = {
    "mentioned": 1,
    "replied": 2,
    "quoted": 3,
}


def load_seen() -> set[int]:
    if not SEEN_FILE.exists():
        return set()

    try:
        data = json.loads(SEEN_FILE.read_text(encoding="utf-8"))
        return {int(x) for x in data}
    except Exception:
        return set()


def save_seen(seen: set[int]):
    SEEN_FILE.write_text(
        json.dumps(sorted(seen), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def get_notifications(client: ShuiyuanClient):
    data = client.get("/notifications.json")
    return data.get("notifications", [])


def get_author(notification: dict) -> str:
    data = notification.get("data") or {}
    return (
        data.get("display_username")
        or data.get("username")
        or data.get("original_username")
        or data.get("mentioned_by_username")
        or "unknown"
    )


def get_title(notification: dict) -> str:
    data = notification.get("data") or {}
    return (
        notification.get("fancy_title")
        or data.get("topic_title")
        or data.get("original_title")
        or "无标题"
    )


def notification_url(notification: dict) -> str | None:
    topic_id = notification.get("topic_id")
    post_number = notification.get("post_number")

    if not topic_id:
        return None

    if post_number:
        return f"{BASE_URL}/t/{topic_id}/{post_number}"

    return f"{BASE_URL}/t/{topic_id}"


def print_notification(notification: dict):
    ntype = notification.get("notification_type")
    type_name = next(
        (name for name, value in NOTIFICATION_TYPES.items() if value == ntype),
        str(ntype),
    )

    print("\n" + "=" * 100)
    print(f"通知 ID: {notification.get('id')}")
    print(f"类型: {type_name}")
    print(f"作者: {get_author(notification)}")
    print(f"标题: {get_title(notification)}")
    print(f"时间: {notification.get('created_at')}")
    print(f"已读: {notification.get('read')}")
    print(f"链接: {notification_url(notification)}")
    print("=" * 100)


def read_multiline_reply() -> str:
    print("请输入回复内容，输入 END 单独一行结束：")
    lines = []

    while True:
        line = input()
        if line.strip() == "END":
            break
        lines.append(line)

    return "\n".join(lines).strip()


def reply_to_notification(client: ShuiyuanClient, notification: dict):
    topic_id = notification.get("topic_id")
    post_number = notification.get("post_number")
    author = get_author(notification)

    if not topic_id:
        print("这个通知没有 topic_id，无法回复。")
        return

    raw = read_multiline_reply()

    if not raw:
        print("回复为空，已取消。")
        return

    print("\n即将发送以下回复：")
    print("=" * 100)
    print(raw)
    print("=" * 100)
    print(f"目标主题: {BASE_URL}/t/{topic_id}")
    if post_number:
        print(f"针对楼层: #{post_number}")
    print(f"对方用户: {author}")

    confirm = input('输入"确认发送"才会发布：').strip()
    if confirm != "确认发送":
        print("已取消，不发送。")
        return

    data = {
        "topic_id": int(topic_id),
        "raw": raw,
    }

    # reply_to_post_number 让 Discourse 知道你是在回复具体楼层
    if post_number:
        data["reply_to_post_number"] = int(post_number)

    result = client.post("/posts.json", data=data)
    print("回复已发送：")
    print(json.dumps(result, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(
        description="循环检查是否有人回复、引用或提到我，并可人工确认后回复"
    )
    parser.add_argument("--interval", type=int, default=180, help="轮询间隔秒数，最低 60")
    parser.add_argument("--once", action="store_true", help="只检查一次")
    parser.add_argument("--reply", action="store_true", help="发现通知后询问是否回复")
    parser.add_argument(
        "--include-read",
        action="store_true",
        help="默认只看未读通知；加这个参数后也显示已读但本地未记录的通知",
    )
    parser.add_argument(
        "--types",
        default="replied,quoted,mentioned",
        help="通知类型，逗号分隔：replied,quoted,mentioned",
    )
    args = parser.parse_args()

    interval = max(args.interval, 60)
    selected_types = {
        NOTIFICATION_TYPES[name.strip()]
        for name in args.types.split(",")
        if name.strip() in NOTIFICATION_TYPES
    }

    if not selected_types:
        raise ValueError("没有有效通知类型。可用：replied,quoted,mentioned")

    client = ShuiyuanClient()
    seen = load_seen()

    print("开始检查别人是否回复 / 引用 / 提到你。")
    print(f"轮询间隔: {interval} 秒")
    print(f"通知类型: {args.types}")
    print("按 Ctrl+C 停止。")

    while True:
        try:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print("\n" + "-" * 100)
            print(f"检查时间: {now}")

            notifications = get_notifications(client)
            new_items = []

            for n in notifications:
                nid = n.get("id")
                ntype = n.get("notification_type")

                if nid is None:
                    continue

                nid = int(nid)

                if nid in seen:
                    continue

                if ntype not in selected_types:
                    continue

                if not args.include_read and n.get("read"):
                    continue

                new_items.append(n)

            if not new_items:
                print("没有新的回复 / 引用 / 提及。")
            else:
                print(f"发现 {len(new_items)} 条新通知。")

            for n in new_items:
                print_notification(n)

                if args.reply:
                    answer = input("要回复这条通知对应的主题吗？输入 y 回复，其他键跳过：").strip().lower()
                    if answer == "y":
                        reply_to_notification(client, n)

                seen.add(int(n["id"]))

            save_seen(seen)

            if args.once:
                break

        except KeyboardInterrupt:
            print("\n已停止。")
            break

        except Exception as e:
            print(f"检查失败: {e}")

        time.sleep(interval)


if __name__ == "__main__":
    main()