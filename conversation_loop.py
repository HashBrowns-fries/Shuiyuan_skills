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
    }
    if not STATE_FILE.exists():
        return defaults
    try:
        state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        for k, v in defaults.items():
            state.setdefault(k, v)
        # 清理旧版死字段
        state.pop("last_seen_post_numbers", None)
        state.pop("replied_post_ids", None)
        return state
    except Exception:
        return defaults


def save_state(state: dict):
    STATE_FILE.write_text(
        json.dumps(state, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )



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
    my_username: str,
    all_posts: list[dict] | None = None,
) -> list[dict]:
    """
    拉取所有帖子，返回那些还没被当前用户回复过的楼层。
    通过检查论坛上是否有 reply_to_post_number 指向该楼层的回帖来判断。
    不依赖 state 文件，直接查看论坛实际数据。
    """
    posts = all_posts or client.topic_posts_all(topic_id, limit=200)

    # 找出哪些楼层已被我回复
    replied_post_numbers: set[int] = set()
    for p in posts:
        if p.get("username") == my_username:
            rtp = p.get("reply_to_post_number")
            if rtp:
                replied_post_numbers.add(rtp)

    # 筛值得回复的楼层：不是自己的、没被回复过的、未被删除的
    new_posts = [
        p for p in posts
        if p.get("username") != my_username
        and p.get("post_number", 0) not in replied_post_numbers
        and not _is_deleted(p)
    ]

    return new_posts


def _is_deleted(post: dict) -> bool:
    """判断帖子是否已被删除（作者删除或管理员删除）。"""
    if post.get("deleted_at") or post.get("post_deleted"):
        return True
    cooked = post.get("cooked", "")
    if "（帖子已被作者删除）" in cooked:
        return True
    return False


# ─── 上下文拼装 ───────────────────────────────────────────────────────────────

def build_context(
    client: ShuiyuanClient,
    topic_id: int,
    around_post_number: int,
    all_posts: list[dict] | None = None,
    window: int = 8,
    text_limit: int = 600,
) -> str:
    """
    围绕 around_post_number 取前后各 window/2 楼，拼成上下文。
    all_posts 传入全量帖子列表时直接从内存构建，无需额外 API 调用。
    """
    if all_posts:
        return _build_context_from_posts(
            all_posts, topic_id, around_post_number, window, text_limit
        )

    # 回退：通过 API 获取（用于没有 all_posts 的调用方）
    topic_data = client.topic(topic_id)
    title = topic_data.get("title", "")
    posts = client.topic_posts_all(topic_id, limit=200)
    return _build_context_from_posts(posts, topic_id, around_post_number, window, text_limit, title=title)


def _build_context_from_posts(
    posts: list[dict],
    topic_id: int,
    around_post_number: int,
    window: int = 8,
    text_limit: int = 600,
    title: str = "",
) -> str:
    """从已加载的帖子列表中围绕目标楼层构建上下文。"""
    # 按 post_number 排序
    sorted_posts = sorted(posts, key=lambda p: p.get("post_number", 0))

    # 提取标题（从 #1 楼）
    if not title:
        for p in sorted_posts:
            if p.get("post_number") == 1:
                title = html_to_text(p.get("cooked", "")).split("\n")[0][:100]
                break

    # 找目标楼在 sorted_posts 中的索引
    target_idx = 0
    for i, p in enumerate(sorted_posts):
        if p.get("post_number") == around_post_number:
            target_idx = i
            break
    else:
        # 找不到精确匹配，找最接近的
        best_idx = 0
        best_dist = 10**9
        for i, p in enumerate(sorted_posts):
            dist = abs(p.get("post_number", 10**9) - around_post_number)
            if dist < best_dist:
                best_dist = dist
                best_idx = i
        target_idx = best_idx

    half = window // 2
    start = max(0, target_idx - half)
    end = min(len(sorted_posts), target_idx + half + 1)
    window_posts = sorted_posts[start:end]

    lines = [f"标题: {title}", f"链接: {BASE_URL}/t/{topic_id}", "=" * 80]
    for p in window_posts:
        pnum = p.get("post_number")
        username = p.get("username")
        created = p.get("created_at", "")
        text = shorten(html_to_text(p.get("cooked", "")), text_limit)
        marker = " ◀◀ 目标" if pnum == around_post_number else ""
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
    }
    if post_number is not None:
        data["reply_to_post_number"] = int(post_number)
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

    # 3. --skip-existing：论坛过滤已自动处理，仅打印提示
    if args.skip_existing:
        print("--skip-existing：基于论坛 reply_to_post_number 自动过滤已有回复，无需手动干预。")

    print("按 Ctrl+C 停止。\n")

    while True:
        try:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print("-" * 80)
            print(f"检查时间: {now}")

            sent_count = 0

            # 一次拉取全量帖子，供过滤和上下文共用
            all_posts = client.topic_posts_all(topic_id, limit=200)
            new_posts = fetch_new_posts(
                client=client,
                topic_id=topic_id,
                my_username=my_username,
                all_posts=all_posts,
            )

            if not new_posts:
                print("所有楼层都已回复。")
            else:
                print(f"发现 {len(new_posts)} 个未回复的楼层：", end="")
                print(" ".join(f"#{p.get('post_number')}" for p in new_posts[:10]),
                      "..." if len(new_posts) > 10 else "")

                for post in new_posts:
                    if sent_count >= args.max_replies_per_run:
                        print("已达到本次最大回复数，停止。")
                        break

                    pnum = post.get("post_number", 0)

                    # 构建上下文（使用全量帖子，精准定位目标楼）
                    context = build_context(
                        client=client,
                        topic_id=topic_id,
                        around_post_number=pnum,
                        all_posts=all_posts,
                    )
                    print("\n上下文：")
                    print(context)

                    # 生成草稿
                    should_reply, draft, suggested_emoji = build_reply_draft(post, context)
                    if args.retort and not suggested_emoji:
                        suggested_emoji = args.retort

                    # LLM 决定跳过或返回空
                    if not should_reply:
                        print(f"[AI] 决定跳过 #{pnum}")
                        continue

                    if not draft:
                        print(f"[AI] 生成的回复为空，跳过 #{pnum}")
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

                    if sent:
                        sent_count += 1

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