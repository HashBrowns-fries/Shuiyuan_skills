"""
直接轮询帖子列表，回复所有未回复的新楼层。

探测机制：直接轮询 /t/{topic_id}.json，不依赖 @提及/引用/通知，
任何新楼层都能捕获。
"""

import argparse
import json
import time
from pathlib import Path
from datetime import datetime

from shuiyuan_client import BASE_URL, ShuiyuanClient
from text_utils import html_to_text, shorten
from ai_reply import build_ai_draft

STATE_FILE = Path("./conversation_loop_state.json")


# ─── state ────────────────────────────────────────────────────────────────────

def load_state() -> dict:
    defaults = {
        "topic_id": None,
        "last_seen_post_numbers": {},   # {str(topic_id): int(post_number)}
        "replied_post_ids": [],          # ["topic_id:post_number", ...]
        "sent_reply_count": 0,
    }
    if not STATE_FILE.exists():
        return defaults
    try:
        state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        for k, v in defaults.items():
            state.setdefault(k, v)
        return state
    except Exception:
        return defaults


def save_state(state: dict):
    STATE_FILE.write_text(
        json.dumps(state, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def post_key(topic_id: int, post_number: int) -> str:
    return f"{topic_id}:{post_number}"


# ─── 用户身份 ──────────────────────────────────────────────────────────────────

def get_my_username(client: ShuiyuanClient) -> str:
    try:
        data = client.current_user()
        return data.get("current_user", {}).get("username", "")
    except Exception:
        return ""


# ─── 拉取新楼层 ───────────────────────────────────────────────────────────────

def fetch_new_posts(
    client: ShuiyuanClient,
    topic_id: int,
    last_seen_post_number: int,
    my_username: str,
    replied_ids: set[str],
    tail_size: int = 30,
) -> tuple[list[dict], int]:
    """
    只拉取 last_seen_post_number 之后的楼层，过滤掉自己的帖子和已回复的楼层。
    返回 (待处理帖子列表, 本轮见到的最大 post_number)。
    """
    topic_data = client.topic(topic_id)
    post_stream = topic_data.get("post_stream", {})
    stream_ids: list[int] = post_stream.get("stream", [])
    loaded: dict[int, dict] = {
        p["id"]: p for p in post_stream.get("posts", []) if p.get("id")
    }

    if not stream_ids:
        return [], last_seen_post_number

    # 补拉尾部（保证最新楼层都在）
    tail_ids = stream_ids[-tail_size:]
    missing = [pid for pid in tail_ids if pid not in loaded]
    if missing:
        chunk = client.topic_posts_chunk(topic_id, missing)
        extra = (
            chunk.get("post_stream", {}).get("posts")
            or chunk.get("posts")
            or []
        )
        for p in extra:
            if p.get("id"):
                loaded[p["id"]] = p

    all_posts = sorted(loaded.values(), key=lambda p: p.get("post_number", 0))
    max_pnum = max(
        (p.get("post_number", 0) for p in all_posts),
        default=last_seen_post_number,
    )

    new_posts = [
        p for p in all_posts
        if p.get("post_number", 0) > last_seen_post_number
        and p.get("username") != my_username
        and post_key(topic_id, p.get("post_number", 0)) not in replied_ids
    ]

    return new_posts, max_pnum


# ─── 上下文拼装 ───────────────────────────────────────────────────────────────

def build_context(
    client: ShuiyuanClient,
    topic_id: int,
    around_post_number: int,
    window: int = 6,
    text_limit: int = 600,
) -> str:
    """
    拉取 around_post_number 附近若干楼，拼成供 AI 阅读的上下文字符串。
    """
    topic_data = client.topic(topic_id)
    title = topic_data.get("title", "")
    stream_ids: list[int] = topic_data.get("post_stream", {}).get("stream", [])
    loaded: dict[int, dict] = {
        p["id"]: p
        for p in topic_data.get("post_stream", {}).get("posts", [])
        if p.get("id")
    }

    # 找到目标楼在 stream 中的位置，取前后各 window/2 个 ID
    target_ids_near: list[int] = []
    for i, pid in enumerate(stream_ids):
        p = loaded.get(pid)
        if p and p.get("post_number") == around_post_number:
            start = max(0, i - window // 2)
            end = min(len(stream_ids), i + window // 2 + 1)
            target_ids_near = stream_ids[start:end]
            break
    if not target_ids_near:
        target_ids_near = stream_ids[-window:]

    # 补拉缺失
    missing = [pid for pid in target_ids_near if pid not in loaded]
    if missing:
        chunk = client.topic_posts_chunk(topic_id, missing)
        extra = (
            chunk.get("post_stream", {}).get("posts")
            or chunk.get("posts")
            or []
        )
        for p in extra:
            if p.get("id"):
                loaded[p["id"]] = p

    window_posts = sorted(
        [loaded[pid] for pid in target_ids_near if pid in loaded],
        key=lambda p: p.get("post_number", 0),
    )

    lines = [f"标题: {title}", f"链接: {BASE_URL}/t/{topic_id}", "=" * 80]
    for p in window_posts:
        pnum = p.get("post_number")
        username = p.get("username")
        created = p.get("created_at", "")
        text = shorten(html_to_text(p.get("cooked", "")), text_limit)
        marker = " ◀ 新楼层" if pnum == around_post_number else ""
        lines.append(f"\n#{pnum} @{username} | {created}{marker}")
        lines.append("-" * 60)
        lines.append(text)

    return "\n".join(lines)


# ─── AI 草稿（MiniMax API）────────────────────────────────────────────────────

def build_reply_draft(post: dict, context: str) -> tuple[bool, str, str]:
    """
    生成回复草稿。使用 MiniMax API 判断是否回复并生成内容。
    返回 (should_reply, reply_text, emoji_name)。
    """
    author = post.get("username", "unknown")
    post_number = post.get("post_number", "?")

    print(f"[AI] 正在分析 #{post_number} @{author}...")

    should_reply, reply, emoji, reason = build_ai_draft(context, "replied", author)

    if should_reply and emoji:
        print(f"[AI] 表情建议：:{emoji}:  原因：{reason}")
    elif not should_reply:
        print(f"[AI] 决定跳过：{reason}")

    return should_reply, reply, emoji


# ─── 确认并发送 ───────────────────────────────────────────────────────────────

def confirm_or_cancel(prompt: str, confirm_text: str) -> bool:
    print(prompt)
    value = input(f'输入"{confirm_text}"继续：').strip()
    return value == confirm_text


def send_reply_confirmed(
    client: ShuiyuanClient,
    post: dict,
    topic_id: int,
    draft: str,
    suggested_emoji: str = "",
    auto: bool = True,
) -> bool:
    post_number = post.get("post_number")
    author = post.get("username", "unknown")
    post_id = post.get("id")

    print("\n" + "=" * 80)
    print(f"楼层: #{post_number}  作者: @{author}")
    print(f"链接: {BASE_URL}/t/{topic_id}/{post_number}")
    print("=" * 80)

    if not auto:
        print("\n回复草稿：")
        print("-" * 80)
        print(draft)
        print("-" * 80)

        edit = input("是否编辑草稿？输入 y 编辑，其他键直接确认：").strip().lower()
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
            print("已取消。")
            return False
    else:
        print(f"\n自动回复：{draft}")

    data: dict = {
        "topic_id": int(topic_id),
        "raw": draft,
        "reply_to_post_number": int(post_number),
    }
    result = client.post("/posts.json", data=data)
    print("回复已发送：")
    print(json.dumps(result, ensure_ascii=False, indent=2)[:1000])

    # 贴表情
    if suggested_emoji and post_id:
        try:
            client.retort_post(int(post_id), suggested_emoji)
            print(f"已贴表情 :{suggested_emoji}:")
        except Exception as e:
            err_msg = str(e)
            if "HTTP" in err_msg:
                err_msg = err_msg.split("HTTP")[0].strip()
            print(f"贴表情失败：{err_msg[:100]}")

    return True


# ─── 发帖（可选，首次建帖后监听） ─────────────────────────────────────────────

def create_topic_confirmed(
    client: ShuiyuanClient,
    title: str,
    raw: str,
    category_id: int,
) -> int:
    print("\n即将发布主题：")
    print("=" * 80)
    print(f"标题: {title}  分类 ID: {category_id}")
    print("-" * 80)
    print(raw)
    print("=" * 80)
    if not confirm_or_cancel("确认发布？", "确认发帖"):
        raise RuntimeError("已取消发帖。")
    result = client.create_topic(title=title, raw=raw, category_id=category_id)
    topic_id = result.get("topic_id") or result.get("id")
    if not topic_id:
        raise RuntimeError("发帖成功但未解析到 topic_id。")
    print(f"主题已发布: {BASE_URL}/t/{int(topic_id)}")
    return int(topic_id)


# ─── main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="直接轮询帖子列表，回复所有未回复的新楼层"
    )
    parser.add_argument("--topic-id", type=int, help="监听的 topic ID")
    parser.add_argument("--title", help="新帖标题（可选，先发帖再监听）")
    parser.add_argument("--category", type=int, help="新帖分类 ID")
    parser.add_argument("--post-file", help="新帖正文 Markdown 文件")
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="首次运行跳过已有楼层，只处理启动后的新楼层",
    )
    parser.add_argument("--interval", type=int, default=180, help="轮询间隔秒数（最低 60）")
    parser.add_argument("--max-replies-per-run", type=int, default=5, help="本次最多回复几条")
    parser.add_argument("--once", action="store_true", help="只检查一次")
    parser.add_argument("--auto", action="store_true", default=True, help="自动回复，不询问确认（默认开启）")
    parser.add_argument("--no-auto", action="store_true", help="关闭自动回复，需要人工确认")
    parser.add_argument("--retort", help="回复后自动贴的表情（如 heart, like）")
    args = parser.parse_args()

    if args.no_auto:
        args.auto = False

    interval = max(args.interval, 60)
    client = ShuiyuanClient()
    state = load_state()

    # 1. 确定 topic_id
    topic_id: int | None = args.topic_id or state.get("topic_id")

    if args.title and args.category and args.post_file:
        raw = Path(args.post_file).read_text(encoding="utf-8").strip()
        if not raw:
            raise ValueError("post-file 内容为空。")
        topic_id = create_topic_confirmed(
            client=client, title=args.title, raw=raw, category_id=args.category
        )
        state["topic_id"] = topic_id
        save_state(state)

    if not topic_id:
        raise ValueError("请用 --topic-id 指定要监听的主题 ID。")

    # 2. 获取自己的用户名（防止自我回复）
    my_username = get_my_username(client)
    print(f"当前用户: @{my_username or '（未获取到）'}")
    print(f"监听主题: {BASE_URL}/t/{topic_id}")
    print(f"轮询间隔: {interval} 秒")

    # 3. 首次运行：--skip-existing 则把当前最大楼层号记入 state，跳过已有内容
    key = str(topic_id)
    if key not in state["last_seen_post_numbers"] or state["last_seen_post_numbers"][key] == 0:
        if args.skip_existing:
            topic_data = client.topic(topic_id)
            stream = topic_data.get("post_stream", {}).get("stream", [])
            posts_loaded = topic_data.get("post_stream", {}).get("posts", [])
            if posts_loaded:
                current_max = max(p.get("post_number", 0) for p in posts_loaded)
                last_ids = stream[-5:] if len(stream) >= 5 else stream
                missing = [pid for pid in last_ids if pid not in {p["id"]: p for p in posts_loaded}]
                if missing:
                    chunk = client.topic_posts_chunk(topic_id, last_ids)
                    extra = chunk.get("post_stream", {}).get("posts") or chunk.get("posts") or []
                    if extra:
                        current_max = max(p.get("post_number", 0) for p in extra)
                state["last_seen_post_numbers"][key] = current_max
                save_state(state)
                print(f"--skip-existing：跳过已有楼层，从 #{current_max} 之后开始监听。")

    print("按 Ctrl+C 停止。\n")

    while True:
        try:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print("-" * 80)
            print(f"检查时间: {now}")

            last_seen = int(state["last_seen_post_numbers"].get(key, 0))
            replied_ids = set(state.get("replied_post_ids", []))
            sent_count = int(state.get("sent_reply_count", 0))

            new_posts, max_pnum = fetch_new_posts(
                client=client,
                topic_id=topic_id,
                last_seen_post_number=last_seen,
                my_username=my_username,
                replied_ids=replied_ids,
            )

            # 更新最大楼层号（即使没有需要回复的帖子也要推进）
            if max_pnum > last_seen:
                state["last_seen_post_numbers"][key] = max_pnum
                save_state(state)

            if not new_posts:
                print(f"没有新楼层（当前最高楼: #{max_pnum}）。")
            else:
                print(f"发现 {len(new_posts)} 个未回复的新楼层。")

                for post in new_posts:
                    if sent_count >= args.max_replies_per_run:
                        print("已达到本次最大回复数，停止。")
                        break

                    pnum = post.get("post_number", 0)
                    pkey = post_key(topic_id, pnum)

                    # 构建上下文
                    context = build_context(
                        client=client,
                        topic_id=topic_id,
                        around_post_number=pnum,
                    )
                    print("\n上下文：")
                    print(context)

                    # 生成草稿
                    should_reply, draft, suggested_emoji = build_reply_draft(post, context)
                    if args.retort and not suggested_emoji:
                        suggested_emoji = args.retort

                    # LLM 决定跳过或返回空
                    if not should_reply:
                        replied_ids.add(pkey)
                        state["replied_post_ids"] = sorted(replied_ids)
                        save_state(state)
                        continue

                    if not draft:
                        print("[AI] 生成的回复为空，跳过此楼层")
                        replied_ids.add(pkey)
                        state["replied_post_ids"] = sorted(replied_ids)
                        save_state(state)
                        continue

                    # 确认发送
                    sent = send_reply_confirmed(
                        client=client,
                        post=post,
                        topic_id=topic_id,
                        draft=draft,
                        suggested_emoji=suggested_emoji,
                        auto=args.auto,
                    )

                    # 无论是否发送，都标记这个楼层为已处理（防止下轮重复询问）
                    replied_ids.add(pkey)
                    state["replied_post_ids"] = sorted(replied_ids)

                    if sent:
                        sent_count += 1
                        state["sent_reply_count"] = sent_count

                    save_state(state)

            if args.once:
                break

        except KeyboardInterrupt:
            print("\n已停止。")
            break
        except Exception as e:
            print(f"出错: {e}")

        time.sleep(interval)


if __name__ == "__main__":
    main()