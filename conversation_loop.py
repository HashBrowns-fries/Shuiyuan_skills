import argparse
import json
import time
from pathlib import Path
from datetime import datetime

from shuiyuan_client import BASE_URL, ShuiyuanClient
from text_utils import html_to_text, shorten


STATE_FILE = Path("./conversation_loop_state.json")

NOTIFICATION_TYPES = {
    "mentioned": 1,
    "replied": 2,
    "quoted": 3,
}


def load_state() -> dict:
    defaults = {
        "topic_id": None,
        "seen_notification_ids": [],
        "sent_reply_count": 0,
        "replied_post_numbers": [],
    }

    if not STATE_FILE.exists():
        return defaults

    try:
        data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        # Ensure all keys exist
        for k, v in defaults.items():
            if k not in data:
                data[k] = v
        return data
    except Exception:
        return defaults


def save_state(state: dict):
    STATE_FILE.write_text(
        json.dumps(state, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def confirm_or_cancel(prompt: str, confirm_text: str) -> bool:
    print(prompt)
    value = input(f'输入"{confirm_text}"继续：').strip()
    return value == confirm_text


def create_topic_confirmed(
    client: ShuiyuanClient,
    title: str,
    raw: str,
    category_id: int,
) -> int:
    print("\n即将发布主题：")
    print("=" * 100)
    print(f"标题: {title}")
    print(f"分类 ID: {category_id}")
    print("-" * 100)
    print(raw)
    print("=" * 100)

    if not confirm_or_cancel("确认发布这个主题吗？", "确认发帖"):
        raise RuntimeError("已取消发帖。")

    result = client.create_topic(
        title=title,
        raw=raw,
        category_id=category_id,
    )

    topic_id = result.get("topic_id") or result.get("topic_slug") or result.get("id")

    if not topic_id:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        raise RuntimeError("发帖成功但没有解析到 topic_id，请检查返回值。")

    topic_id = int(topic_id)

    print(f"主题已发布: {BASE_URL}/t/{topic_id}")
    return topic_id


def get_notifications(client: ShuiyuanClient):
    data = client.get("/notifications.json")
    return data.get("notifications", [])


def notification_type_name(notification: dict) -> str:
    ntype = notification.get("notification_type")
    for name, value in NOTIFICATION_TYPES.items():
        if value == ntype:
            return name
    return str(ntype)


def get_notification_author(notification: dict) -> str:
    data = notification.get("data") or {}
    return (
        data.get("display_username")
        or data.get("username")
        or data.get("original_username")
        or data.get("mentioned_by_username")
        or "unknown"
    )


def get_notification_title(notification: dict) -> str:
    data = notification.get("data") or {}
    return (
        notification.get("fancy_title")
        or data.get("topic_title")
        or data.get("original_title")
        or "无标题"
    )


def notification_url(notification: dict) -> str:
    topic_id = notification.get("topic_id")
    post_number = notification.get("post_number")

    if not topic_id:
        return BASE_URL

    if post_number:
        return f"{BASE_URL}/t/{topic_id}/{post_number}"

    return f"{BASE_URL}/t/{topic_id}"


def should_handle_notification(
    notification: dict,
    target_topic_id: int | None,
    seen_ids: set[int],
    include_all_topics: bool,
) -> bool:
    nid = notification.get("id")
    if nid is None:
        return False

    if int(nid) in seen_ids:
        return False

    if notification.get("read"):
        return False

    if notification.get("notification_type") not in {
        NOTIFICATION_TYPES["replied"],
        NOTIFICATION_TYPES["quoted"],
        NOTIFICATION_TYPES["mentioned"],
    }:
        return False

    if include_all_topics:
        return True

    if target_topic_id is None:
        return True

    return int(notification.get("topic_id") or -1) == int(target_topic_id)


def fetch_topic_context(
    client: ShuiyuanClient,
    topic_id: int,
    post_limit: int = 10,
    text_limit: int = 800,
) -> str:
    topic = client.topic(topic_id)
    title = topic.get("title")
    posts = topic.get("post_stream", {}).get("posts", [])

    lines = []
    lines.append(f"标题: {title}")
    lines.append(f"链接: {BASE_URL}/t/{topic_id}")
    lines.append("=" * 100)

    for post in posts[-post_limit:]:
        username = post.get("username")
        post_number = post.get("post_number")
        created_at = post.get("created_at")
        text = shorten(html_to_text(post.get("cooked", "")), text_limit)

        lines.append("")
        lines.append(f"#{post_number} {username} | {created_at}")
        lines.append("-" * 80)
        lines.append(text)

    return "\n".join(lines)


def build_reply_draft(
    notification: dict,
    context: str,
    auto: bool = False,
) -> str:
    """
    生成回复草稿。

    如果接入 LLM，可以在这里调用：
        draft = call_llm(notification, context)
    但仍建议保留人工确认步骤（除非 --auto 模式）。
    """
    author = get_notification_author(notification)
    post_number = notification.get("post_number")
    type_name = notification_type_name(notification)

    if auto:
        # 自动回复模式：更自然的草稿
        if type_name == "replied":
            draft = f"@{author} 谢谢回复！🐰"
        elif type_name == "quoted":
            draft = f"@{author} 引用收到～"
        elif type_name == "mentioned":
            draft = f"@{author} 被 tag 了！有什么事？"
        else:
            draft = f"@{author} 你好呀～"
        return draft
    else:
        # 人工确认模式
        return f"@{author} 谢谢回复，我看到了。\n\n我这边再补充一下：\n\n"


def send_reply_confirmed(
    client: ShuiyuanClient,
    notification: dict,
    draft: str,
    auto: bool = False,
    retort_emoji: str | None = None,
):
    topic_id = notification.get("topic_id")
    post_number = notification.get("post_number")

    if not topic_id:
        print("该通知没有 topic_id，无法回复。")
        return False

    print("\n检测到新回复 / 引用 / 提及：")
    print("=" * 100)
    print(f"通知 ID: {notification.get('id')}")
    print(f"类型: {notification_type_name(notification)}")
    print(f"作者: {get_notification_author(notification)}")
    print(f"标题: {get_notification_title(notification)}")
    print(f"链接: {notification_url(notification)}")
    print("=" * 100)

    if not auto:
        print("\n回复草稿：")
        print("=" * 100)
        print(draft)
        print("=" * 100)

        edit = input("是否编辑草稿？输入 y 编辑，其他键直接进入确认：").strip().lower()

        if edit == "y":
            print("请输入新的回复内容，输入 END 单独一行结束：")
            lines = []
            while True:
                line = input()
                if line.strip() == "END":
                    break
                lines.append(line)
            draft = "\n".join(lines).strip()

        if not draft:
            print("回复为空，已跳过。")
            return False

        if not confirm_or_cancel("确认发送这条回复吗？", "确认发送"):
            print("已取消发送。")
            return False
    else:
        print(f"\n自动回复：{draft}")

    data = {
        "topic_id": int(topic_id),
        "raw": draft,
    }

    if post_number:
        data["reply_to_post_number"] = int(post_number)

    result = client.post("/posts.json", data=data)

    print("回复已发送：")
    print(json.dumps(result, ensure_ascii=False, indent=2)[:2000])

    # 记录已回复的楼层
    if post_number:
        state = load_state()
        replied = state.get("replied_post_numbers", [])
        if post_number not in replied:
            replied.append(int(post_number))
            state["replied_post_numbers"] = replied
            save_state(state)

    # 自动贴表情
    if retort_emoji:
        try:
            new_post_id = result.get("id")
            if new_post_id:
                client.retort_post(new_post_id, retort_emoji)
                print(f"已贴表情: {retort_emoji}")
        except Exception as e:
            print(f"贴表情失败: {e}")

    return True


def main():
    parser = argparse.ArgumentParser(
        description="发帖 → 监听回复 → 草稿回复 → 人工确认发送 的安全自动化流程"
    )

    parser.add_argument("--title", help="要发布的新主题标题")
    parser.add_argument("--category", type=int, help="分类 ID")
    parser.add_argument("--post-file", help="新主题正文 Markdown 文件")

    parser.add_argument(
        "--topic-id",
        type=int,
        help="不发新帖，直接监听已有 topic_id",
    )

    parser.add_argument(
        "--all-topics",
        action="store_true",
        help="监听所有回复/引用/提及，而不是只监听当前 topic",
    )

    parser.add_argument(
        "--interval",
        type=int,
        default=180,
        help="轮询间隔秒数，最低 60",
    )

    parser.add_argument(
        "--max-replies-per-run",
        type=int,
        default=5,
        help="本次运行最多回复几条，避免误操作",
    )

    parser.add_argument(
        "--once",
        action="store_true",
        help="只检查一次，不循环",
    )

    parser.add_argument(
        "--auto",
        action="store_true",
        default=True,
        help="自动回复，不询问确认（默认开启）",
    )

    parser.add_argument(
        "--no-auto",
        action="store_true",
        help="关闭自动回复，需要人工确认",
    )

    parser.add_argument(
        "--retort",
        help="回复后自动贴的表情（如 heart, like）",
    )

    args = parser.parse_args()

    if args.no_auto:
        args.auto = False
    else:
        args.auto = True

    interval = max(args.interval, 60)

    client = ShuiyuanClient()
    state = load_state()

    # 1. 确定 topic_id：新发帖，或监听已有主题，或恢复上次状态。
    topic_id = args.topic_id or state.get("topic_id")

    if args.title and args.category and args.post_file:
        raw = Path(args.post_file).read_text(encoding="utf-8").strip()

        if not raw:
            raise ValueError("post-file 内容为空。")

        topic_id = create_topic_confirmed(
            client=client,
            title=args.title,
            raw=raw,
            category_id=args.category,
        )

        state["topic_id"] = topic_id
        save_state(state)

    if not topic_id and not args.all_topics:
        raise ValueError(
            "没有 topic_id。请用 --topic-id 监听已有主题，"
            "或用 --title --category --post-file 先发帖，"
            "或加 --all-topics 监听所有通知。"
        )

    print("\n工作流启动。")
    if topic_id:
        print(f"监听主题: {BASE_URL}/t/{topic_id}")
    if args.all_topics:
        print("监听范围: 所有回复 / 引用 / 提及")
    print(f"轮询间隔: {interval} 秒")
    print("按 Ctrl+C 停止。")

    # 2. loop 检查回复。
    while True:
        try:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print("\n" + "-" * 100)
            print(f"检查时间: {now}")

            seen_ids = {int(x) for x in state.get("seen_notification_ids", [])}
            sent_reply_count = int(state.get("sent_reply_count", 0))

            notifications = get_notifications(client)

            candidates = [
                n for n in notifications
                if should_handle_notification(
                    notification=n,
                    target_topic_id=topic_id,
                    seen_ids=seen_ids,
                    include_all_topics=args.all_topics,
                )
            ]

            if not candidates:
                print("没有新的回复 / 引用 / 提及。")
            else:
                print(f"发现 {len(candidates)} 条新通知。")

            for n in candidates:
                if sent_reply_count >= args.max_replies_per_run:
                    print("已达到本次运行最大回复数，停止处理更多通知。")
                    break

                n_topic_id = int(n.get("topic_id"))
                context = fetch_topic_context(client, n_topic_id)
                print("\n最近上下文：")
                print(context)

                draft = build_reply_draft(n, context, auto=args.auto)

                sent = send_reply_confirmed(
                    client=client,
                    notification=n,
                    draft=draft,
                    auto=args.auto,
                    retort_emoji=args.retort,
                )

                seen_ids.add(int(n["id"]))

                if sent:
                    sent_reply_count += 1

                state["seen_notification_ids"] = sorted(seen_ids)
                state["sent_reply_count"] = sent_reply_count
                save_state(state)

            if args.once:
                break

        except KeyboardInterrupt:
            print("\n已停止。")
            break

        except Exception as e:
            print(f"流程出错: {e}")

        time.sleep(interval)


if __name__ == "__main__":
    main()