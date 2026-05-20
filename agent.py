"""
Shuiyuan Agent — 水源社区统一智能助手。

单入口，覆盖所有操作：浏览、搜索、阅读、回复、发帖、巡帖、通知等。
支持子命令模式和交互式 AI 对话模式。

Usage:
    python agent.py browse --count 10          # 浏览最新帖子
    python agent.py search "关键词"             # 搜索帖子
    python agent.py read 475362                # 阅读帖子
    python agent.py reply 475362               # 回复帖子（AI 辅助）
    python agent.py post                       # 发新帖
    python agent.py watch --interval 300       # 持续巡帖
    python agent.py notifications --once       # 检查通知
    python agent.py interactive                # 交互式 AI 对话
"""

import argparse
import json
import os
import sys
import textwrap
from datetime import datetime
from pathlib import Path
from typing import Optional

from shuiyuan_client import BASE_URL, AuthError, ShuiyuanClient
from text_utils import html_to_text, shorten

# ─── Banner ──────────────────────────────────────────────────────────────────────

BANNER = r"""
  ╔══════════════════════════════════════════╗
  ║     🐰 水源 Agent · 乌萨奇 Usagi         ║
  ║     咿——呀哈！Shuiyuan Assistant         ║
  ╚══════════════════════════════════════════╝
"""

# ─── Helpers ────────────────────────────────────────────────────────────────────

def _confirm(action: str) -> bool:
    """要求用户输入确认词。"""
    prompt = f"\n⚠️  {action}\n输入「{keyword}」继续，其他键取消："
    try:
        value = input(prompt).strip()
        return value == keyword
    except (EOFError, KeyboardInterrupt):
        print("\n已取消。")
        return False


def _print_topic(t: dict, index: Optional[int] = None):
    """格式化打印一个主题摘要。"""
    tid = t.get("id", "?")
    title = t.get("title", "无标题")
    replies = t.get("reply_count", 0)
    views = t.get("views", 0)
    last = t.get("last_posted_at", "")
    prefix = f"[{index}] " if index is not None else ""
    print(f"{prefix}📌 [{tid}] {title}")
    print(f"    💬 {replies} 回复  👁 {views} 浏览  🕐 {last}")
    print(f"    🔗 {BASE_URL}/t/{tid}")


def _print_post(p: dict, highlight: bool = False):
    """格式化打印一个楼层。"""
    pnum = p.get("post_number", "?")
    author = p.get("username", "unknown")
    created = p.get("created_at", "")
    text = html_to_text(p.get("cooked", ""))
    marker = " ◀◀◀" if highlight else ""
    print(f"\n{'─' * 70}")
    print(f"#{pnum} @{author} | {created}{marker}")
    print(f"{'─' * 70}")
    print(shorten(text, 1200))


# ─── Agent ──────────────────────────────────────────────────────────────────────

class ShuiyuanAgent:
    """水源社区 Agent，封装所有操作。"""

    def __init__(self):
        self.client: Optional[ShuiyuanClient] = None
        self.my_username: str = ""

    def _ensure_client(self):
        if self.client is None:
            try:
                self.client = ShuiyuanClient()
                user = self.client.current_user()
                self.my_username = user.get("current_user", {}).get("username", "")
            except AuthError as e:
                print(f"❌ 认证失败: {e}")
                sys.exit(1)

    # ── 读操作 ──────────────────────────────────────────────────────────────

    def cmd_browse(self, args):
        """浏览最新帖子。"""
        self._ensure_client()
        data = self.client.latest_topics()
        topics = data.get("topic_list", {}).get("topics", [])
        count = min(args.count, len(topics))
        print(f"\n📋 最新 {count} 条帖子：\n")
        for i, t in enumerate(topics[:count], 1):
            _print_topic(t, index=i)

    def cmd_search(self, args):
        """搜索帖子。"""
        self._ensure_client()
        data = self.client.search(args.keyword)
        topics = data.get("topics", []) or data.get("grouped_search_result", {}).get("topic_results", [])
        posts = data.get("posts", [])
        if topics:
            count = min(args.count, len(topics))
            print(f"\n🔍 搜索「{args.keyword}」结果 ({count}/{len(topics)} 条)：\n")
            for i, t in enumerate(topics[:count], 1):
                _print_topic(t, index=i)
        elif posts:
            count = min(args.count, len(posts))
            print(f"\n🔍 搜索「{args.keyword}」结果 ({count}/{len(posts)} 条)：\n")
            for i, p in enumerate(posts[:count], 1):
                _print_post(p)
        else:
            print(f"\n🔍 未找到「{args.keyword}」相关结果。")

    def cmd_read(self, args):
        """阅读帖子内容。"""
        self._ensure_client()
        topic = self.client.topic(args.topic_id)
        title = topic.get("title", "无标题")
        print(f"\n📖 {title}")
        print(f"🔗 {BASE_URL}/t/{args.topic_id}\n")

        posts = self.client.topic_posts_all(args.topic_id, limit=args.limit)
        for p in posts:
            highlight = p.get("post_number") == 1
            _print_post(p, highlight=highlight)

    def cmd_summarize(self, args):
        """搜索并汇总帖子。"""
        self._ensure_client()
        query = args.query
        # Try as topic_id first
        try:
            topic_id = int(query)
            self.cmd_read(argparse.Namespace(topic_id=topic_id, limit=args.limit))
            return
        except ValueError:
            pass

        # Search and summarize
        data = self.client.search(query)
        topics = data.get("topics", []) or data.get("grouped_search_result", {}).get("topic_results", [])
        if not topics:
            print(f"未找到与「{query}」相关的帖子。")
            return

        count = min(args.limit, len(topics))
        print(f"\n📊 搜索「{query}」汇总 ({count} 条)：\n")
        print("=" * 80)
        for i, t in enumerate(topics[:count], 1):
            title = t.get("title", "无标题")
            excerpt = t.get("excerpt", "") or t.get("blurb", "")
            excerpt_text = html_to_text(excerpt) if excerpt else ""
            print(f"\n[{i}] {title}")
            print(f"    ID: {t.get('id')} | 回复: {t.get('reply_count', 0)}")
            if excerpt_text:
                print(f"    {shorten(excerpt_text, 200)}")
            print(f"    🔗 {BASE_URL}/t/{t.get('id')}")
        print("\n" + "=" * 80)
        print(f"使用 `python agent.py read <topic_id>` 查看详细内容。")
        print(f"使用 `python agent.py reply <topic_id>` 回复帖子。")

    def cmd_categories(self, args):
        """列出所有分类。"""
        self._ensure_client()
        data = self.client.categories()
        cats = data.get("category_list", {}).get("categories", [])
        if not cats:
            print("未找到分类。")
            return
        print(f"\n📂 分类列表 ({len(cats)} 个)：\n")
        for c in cats:
            cid = c.get("id", "?")
            name = c.get("name", "?")
            slug = c.get("slug", "?")
            desc = c.get("description_text", "") or c.get("description", "")
            desc_text = html_to_text(desc) if desc else ""
            topic_count = c.get("topic_count", 0)
            print(f"  [{cid}] {name} ({slug})")
            print(f"      帖子数: {topic_count}")
            if desc_text:
                print(f"      简介: {shorten(desc_text, 120)}")
            print()

    def cmd_user(self, args):
        """查看用户帖子。"""
        self._ensure_client()
        posts = self.client.user_posts(args.username, limit=args.count)
        if not posts:
            print(f"用户 @{args.username} 没有帖子或不存在。")
            return
        print(f"\n👤 @{args.username} 的帖子 ({min(args.count, len(posts))} 条)：\n")
        for i, action in enumerate(posts[:args.count], 1):
            title = action.get("title", "无标题")
            tid = action.get("topic_id", "?")
            filter_type = action.get("_filter_type")
            kind = "📝 发帖" if filter_type == 4 else "💬 回复"
            excerpt = shorten(html_to_text(action.get("excerpt", "")), 150)
            created = action.get("created_at", "")
            print(f"[{i}] {kind} | {created}")
            print(f"    {title}")
            if excerpt:
                print(f"    {excerpt}")
            print(f"    🔗 {BASE_URL}/t/{tid}/{action.get('post_number', '')}")
            print()

    def cmd_images(self, args):
        """获取帖子中的图片链接。"""
        self._ensure_client()
        post = self.client.post_by_id(args.post_id)
        from text_utils import extract_image_links
        cooked = post.get("cooked", "")
        links = extract_image_links(cooked, BASE_URL)
        if not links:
            print("该帖子没有图片。")
            return
        print(f"\n🖼️  帖子 {args.post_id} 中的图片 ({len(links)} 张)：\n")
        for link in links:
            print(f"  {link}")

    def cmd_emojis(self, args):
        """查看帖子的表情回应。"""
        self._ensure_client()
        data = self.client.get(f"/retorts/{args.post_id}")
        retorts = data.get("retorts", [])
        if not retorts:
            print("该帖子没有表情回应。")
            return
        print(f"\n😊 帖子 {args.post_id} 的表情回应：\n")
        for r in retorts:
            emoji = r.get("retort", r.get("emoji", "?"))
            username = r.get("username", "unknown")
            print(f"  :{emoji}:  @{username}")

    # ── 写操作 ──────────────────────────────────────────────────────────────

    def cmd_reply(self, args):
        """回复帖子（AI 辅助生成草稿）。"""
        self._ensure_client()

        if not args.no_auto:
            # AI 辅助生成回复
            from ai_reply import build_ai_draft

            topic = self.client.topic(args.topic_id)
            title = topic.get("title", "")
            posts = self.client.topic_posts_all(args.topic_id, limit=200)
            stream = topic.get("post_stream", {}).get("stream", [])

            # 找到目标楼层，构建围绕它的上下文窗口
            target_pn = args.reply_to
            if target_pn and stream:
                # 找到目标在 stream 中的位置，取前后各 4 个 ID
                by_id = {int(p["id"]): p for p in posts if p.get("id")}
                window_ids = stream[-8:]  # fallback: last 8
                for i, pid in enumerate(stream):
                    p = by_id.get(int(pid))
                    if p and p.get("post_number") == target_pn:
                        start = max(0, i - 4)
                        end = min(len(stream), i + 5)
                        window_ids = stream[start:end]
                        break
                # 按 post_number 排序
                window_posts = sorted(
                    [by_id[int(pid)] for pid in window_ids if int(pid) in by_id],
                    key=lambda p: p.get("post_number", 0),
                )
            else:
                window_posts = posts[-8:]

            # 构建上下文
            lines = [f"标题: {title}", f"链接: {BASE_URL}/t/{args.topic_id}", "=" * 80]
            for p in window_posts:
                pnum = p.get("post_number", "?")
                author = p.get("username", "unknown")
                text = shorten(html_to_text(p.get("cooked", "")), 600)
                marker = " ◀◀ 目标" if target_pn and pnum == target_pn else ""
                lines.append(f"\n#{pnum} @{author}{marker}")
                lines.append(text)
            context = "\n".join(lines)

            print(f"\n📖 {title}")
            print(f"🔗 {BASE_URL}/t/{args.topic_id}")

            # 获取目标楼层作者（作为通知触发者）
            target_author = "unknown"
            if target_pn:
                for p in window_posts:
                    if p.get("post_number") == target_pn:
                        target_author = p.get("username", "unknown")
                        break

            should_reply, draft, emoji, reason = build_ai_draft(
                context, "manual_reply", target_author
            )
        else:
            should_reply = True
            draft = args.message or ""
            emoji = args.emoji or ""
            reason = ""

        if not should_reply:
            print(f"AI 不建议回复：{reason}")
            return

        if args.message:
            draft = args.message

        print(f"\n💬 AI 回复草稿：")
        print("─" * 60)
        print(draft)
        print("─" * 60)
        if emoji:
            print(f"表情建议: :{emoji}: — {reason}")

        if not _confirm("发送这条回复到水源社区？", "确认发送"):
            return

        data = {
            "topic_id": int(args.topic_id),
            "raw": draft,
        }
        if args.reply_to:
            data["reply_to_post_number"] = int(args.reply_to)

        result = self.client.post("/posts.json", data=data)
        print("✅ 回复已发送！")
        new_post_id = result.get("id")
        if new_post_id:
            print(f"🔗 {BASE_URL}/t/{args.topic_id}/{result.get('post_number', '')}")

        # 贴表情
        if emoji and new_post_id:
            target_id = args.reply_to or new_post_id
            try:
                self.client.retort_post(int(target_id), emoji)
                print(f"✅ 已贴表情 :{emoji}:")
            except Exception as e:
                print(f"⚠️  贴表情失败: {str(e)[:100]}")

    def cmd_post(self, args):
        """发布新主题帖。"""
        self._ensure_client()

        # Title
        title = args.title
        if not title:
            title = input("标题：").strip()
        if not title:
            print("标题不能为空。")
            return

        # Category
        category_id = args.category
        if not category_id:
            self.cmd_categories(args=None)
            try:
                category_id = int(input("\n选择分类 ID：").strip())
            except ValueError:
                print("请输入有效的分类 ID。")
                return

        # Body
        raw = ""
        if args.file:
            raw = Path(args.file).read_text(encoding="utf-8").strip()
        elif not sys.stdin.isatty():
            raw = sys.stdin.read().strip()
        else:
            print("请输入正文（Markdown 格式），输入 END 单独一行结束：")
            lines = []
            while True:
                try:
                    line = input()
                except EOFError:
                    break
                if line.strip() == "END":
                    break
                lines.append(line)
            raw = "\n".join(lines)

        if not raw:
            print("正文不能为空。")
            return

        print(f"\n📝 新帖预览：")
        print("=" * 60)
        print(f"标题: {title}")
        print(f"分类: {category_id}")
        print("─" * 60)
        print(raw)
        print("=" * 60)

        if not _confirm("发布此主题帖到水源社区？", "确认发帖"):
            return

        result = self.client.create_topic(title=title, raw=raw, category_id=int(category_id))
        topic_id = result.get("topic_id") or result.get("id")
        print(f"✅ 主题已发布！")
        if topic_id:
            print(f"🔗 {BASE_URL}/t/{int(topic_id)}")

    def cmd_delete(self, args):
        """删除回复。"""
        self._ensure_client()

        try:
            post = self.client.post_by_id(int(args.post_id))
        except Exception as e:
            print(f"❌ 无法获取帖子: {e}")
            return

        author = post.get("username", "unknown")
        text = shorten(html_to_text(post.get("cooked", "")), 300)
        print(f"\n📌 帖子 #{args.post_id} @{author}:")
        print(f"{text}")

        if not _confirm(f"删除帖子 #{args.post_id}？此操作不可撤销！", "确认删除"):
            return

        self.client.delete_post(int(args.post_id))
        print("✅ 帖子已删除。")

    def cmd_retort(self, args):
        """贴表情。"""
        self._ensure_client()

        from ai_reply import ALLOWED_EMOJI

        emoji = args.emoji
        if not emoji:
            print(f"可用表情: {', '.join(sorted(ALLOWED_EMOJI))}")
            emoji = input("选择表情：").strip().lower()
        if not emoji or emoji not in ALLOWED_EMOJI:
            print(f"无效表情，可用: {', '.join(sorted(ALLOWED_EMOJI))}")
            return

        if not _confirm(f"对帖子 #{args.post_id} 贴 :{emoji}:？", "确认贴表情"):
            return

        self.client.retort_post(int(args.post_id), emoji)
        print(f"✅ 已对帖子 #{args.post_id} 贴表情 :{emoji}:")

    # ── 监控操作 ────────────────────────────────────────────────────────────

    def cmd_watch(self, args):
        """持续巡帖。"""
        import time
        from seen_store import load_seen, mark_seen

        self._ensure_client()
        interval = max(args.interval, 60)
        print(f"🔭 开始巡帖，间隔 {interval} 秒，按 Ctrl+C 停止。\n")

        try:
            while True:
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"\n{'─' * 60}")
                print(f"🕐 {now}")

                data = self.client.latest_topics()
                topics = data.get("topic_list", {}).get("topics", [])
                seen = load_seen()
                new_count = 0

                for t in topics[:args.count]:
                    tid = t.get("id")
                    if not tid or int(tid) in seen:
                        continue
                    if args.keyword and args.keyword not in t.get("title", ""):
                        continue
                    new_count += 1
                    mark_seen(int(tid))
                    print()
                    _print_topic(t)

                if new_count == 0:
                    print("没有新帖。")
                else:
                    print(f"\n共 {new_count} 条新帖。")

                if args.once:
                    break
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\n已停止巡帖。")

    def cmd_notifications(self, args):
        """检查通知（回复/引用/提及）。"""
        import time

        self._ensure_client()
        interval = max(args.interval, 60)

        seen_file = Path("./seen_notifications.json")
        seen: set[int] = set()
        if seen_file.exists():
            try:
                seen = {int(x) for x in json.loads(seen_file.read_text(encoding="utf-8"))}
            except Exception:
                pass

        selected_types = {1, 2, 3}  # mentioned, replied, quoted

        print(f"🔔 检查通知，间隔 {interval} 秒，按 Ctrl+C 停止。\n")

        try:
            while True:
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"\n{'─' * 60}")
                print(f"🕐 {now}")

                notifications = self.client.get("/notifications.json").get("notifications", [])
                new_items = [
                    n for n in notifications
                    if n.get("id") and int(n["id"]) not in seen
                    and n.get("notification_type") in selected_types
                    and (args.include_read or not n.get("read"))
                ]

                if not new_items:
                    print("没有新通知。")
                else:
                    print(f"📬 {len(new_items)} 条新通知：")
                    for n in new_items:
                        nid = int(n["id"])
                        ntype = n.get("notification_type")
                        type_names = {1: "提及", 2: "回复", 3: "引用"}
                        data = n.get("data", {}) or {}
                        author = data.get("display_username") or data.get("username") or "unknown"
                        title = data.get("topic_title") or n.get("fancy_title", "无标题")
                        topic_id = n.get("topic_id", "")
                        post_num = n.get("post_number", "")

                        print(f"\n  [{type_names.get(ntype, str(ntype))}] @{author}")
                        print(f"  标题: {title}")
                        print(f"  🔗 {BASE_URL}/t/{topic_id}/{post_num}")
                        seen.add(nid)

                if args.once:
                    break

                seen_file.write_text(json.dumps(sorted(seen), ensure_ascii=False, indent=2), encoding="utf-8")
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\n已停止。")

    def cmd_stats(self, args):
        """统计表情使用情况。"""
        self._ensure_client()
        from text_utils import count_emojis_from_texts

        posts = self.client.user_posts(args.username, limit=args.count)
        texts = [html_to_text(p.get("excerpt", "")) for p in posts]
        counter = count_emojis_from_texts(texts)

        if not counter:
            print(f"用户 @{args.username} 的帖子中没找到 emoji。")
            return

        print(f"\n📊 @{args.username} 表情使用统计 (基于 {len(texts)} 条帖子)：\n")
        for emoji_char, count in counter.most_common(args.top or 20):
            print(f"  {emoji_char}  {count} 次")

    # ── 交互式 AI 模式 ──────────────────────────────────────────────────────

    def cmd_interactive(self, args):
        """交互式 AI 对话模式。"""
        self._ensure_client()

        print(BANNER)
        print(f"  已登录: @{self.my_username}")
        print(f"  输入 help 查看命令，输入 quit 退出。\n")

        while True:
            try:
                user_input = input("🦾 水源> ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n再见！👋")
                break

            if not user_input:
                continue

            if user_input.lower() in ("quit", "exit", "q"):
                print("再见！👋")
                break

            if user_input.lower() in ("help", "h", "?"):
                self._show_interactive_help()
                continue

            if user_input.lower() == "categories":
                self.cmd_categories(None)
                continue

            if user_input.lower().startswith("browse") or user_input.lower() == "latest":
                parts = user_input.split()
                count = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 10
                self.cmd_browse(argparse.Namespace(count=count))
                continue

            if user_input.lower().startswith("search "):
                keyword = user_input[7:].strip()
                self.cmd_search(argparse.Namespace(keyword=keyword, count=10))
                continue

            if user_input.lower().startswith("read "):
                try:
                    tid = int(user_input[5:].strip())
                    self.cmd_read(argparse.Namespace(topic_id=tid, limit=50))
                except ValueError:
                    print("请输入有效的帖子 ID。")
                continue

            if user_input.lower().startswith("user ") or user_input.lower().startswith("who "):
                username = user_input.split(maxsplit=1)[1].strip()
                self.cmd_user(argparse.Namespace(username=username, count=20))
                continue

            if user_input.lower().startswith("reply ") or user_input.lower().startswith("回复 "):
                parts = user_input.split()
                tid = None
                msg = None
                for i, p in enumerate(parts[1:], 1):
                    try:
                        tid = int(p.strip("，,"))
                        if i + 1 < len(parts):
                            msg = " ".join(parts[i + 1:])
                        break
                    except ValueError:
                        continue
                if tid:
                    self.cmd_reply(argparse.Namespace(
                        topic_id=tid, message=msg, emoji="", auto=msg is None,
                        reply_to=None,
                    ))
                else:
                    print("用法: reply <topic_id> [回复内容]")
                continue

            if user_input.lower().startswith("watch"):
                parts = user_input.split()
                interval = 300
                for p in parts:
                    if p.isdigit():
                        interval = int(p)
                self.cmd_watch(argparse.Namespace(interval=interval, count=20, keyword=None, once=False))
                continue

            if user_input.lower().startswith("notif"):
                self.cmd_notifications(argparse.Namespace(interval=300, once=True, include_read=False))
                continue

            if user_input.lower().startswith("post") or user_input.lower().startswith("发帖"):
                self.cmd_post(argparse.Namespace(title=None, category=None, file=None))
                continue

            # Fallback: try as search query
            print(f"🤔 未识别的命令，当作搜索处理：「{user_input}」")
            self.cmd_search(argparse.Namespace(keyword=user_input, count=10))

    def _show_interactive_help(self):
        print("""
  📋 可用命令：
  ──────────────────────────────────────────────
  browse [count]     浏览最新帖子
  search <关键词>     搜索帖子
  read <topic_id>    阅读帖子内容
  user <username>    查看用户帖子
  reply <topic_id>   回复帖子（AI 辅助）
  post / 发帖         发布新主题帖
  categories         查看分类列表
  watch [间隔秒]      持续巡帖（默认 300s）
  notifications      检查通知
  help / ?           显示此帮助
  quit / exit        退出
  ──────────────────────────────────────────────
  也可以直接输入问题或关键词，会自动搜索。
""")


# ─── CLI ────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="水源社区 Agent — 乌萨奇（咿——呀哈！）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
        示例:
          python agent.py browse --count 10
          python agent.py search "关键词"
          python agent.py read 475362
          python agent.py reply 475362
          python agent.py post
          python agent.py interactive
        """),
    )
    sub = parser.add_subparsers(dest="command", help="可用命令")

    # browse
    p = sub.add_parser("browse", help="浏览最新帖子")
    p.add_argument("--count", type=int, default=10)

    # search
    p = sub.add_parser("search", help="搜索帖子")
    p.add_argument("keyword", help="搜索关键词")
    p.add_argument("--count", type=int, default=10)

    # read
    p = sub.add_parser("read", help="阅读帖子")
    p.add_argument("topic_id", type=int)
    p.add_argument("--limit", type=int, default=50)

    # summarize
    p = sub.add_parser("summarize", help="搜索并汇总帖子（支持 topic_id 或关键词）")
    p.add_argument("query", help="topic_id 或搜索关键词")
    p.add_argument("--limit", type=int, default=10)

    # categories
    sub.add_parser("categories", help="列出所有分类")

    # user
    p = sub.add_parser("user", help="查看用户帖子")
    p.add_argument("username")
    p.add_argument("--count", type=int, default=20)

    # images
    p = sub.add_parser("images", help="获取帖子图片链接")
    p.add_argument("post_id", type=int)

    # emojis
    p = sub.add_parser("emojis", help="查看帖子表情回应")
    p.add_argument("post_id", type=int)

    # reply
    p = sub.add_parser("reply", help="回复帖子")
    p.add_argument("topic_id", type=int)
    p.add_argument("--message", "-m", help="回复内容（留空则 AI 生成）")
    p.add_argument("--emoji", "-e", help="同时贴表情")
    p.add_argument("--reply-to", type=int, help="回复特定楼层号")
    p.add_argument("--no-auto", action="store_true", help="不使用 AI 生成草稿")

    # post
    p = sub.add_parser("post", help="发布新主题帖")
    p.add_argument("--title", "-t", help="标题")
    p.add_argument("--category", "-c", type=int, help="分类 ID")
    p.add_argument("--file", "-f", help="正文 Markdown 文件路径")

    # delete
    p = sub.add_parser("delete", help="删除回复")
    p.add_argument("post_id", type=int)

    # retort
    p = sub.add_parser("retort", help="贴表情")
    p.add_argument("post_id", type=int)
    p.add_argument("emoji", nargs="?", help="表情名称")

    # watch
    p = sub.add_parser("watch", help="持续巡帖")
    p.add_argument("--interval", type=int, default=300)
    p.add_argument("--count", type=int, default=20)
    p.add_argument("--keyword", help="关键词过滤")
    p.add_argument("--once", action="store_true")

    # notifications
    p = sub.add_parser("notifications", help="检查通知")
    p.add_argument("--interval", type=int, default=300)
    p.add_argument("--once", action="store_true")
    p.add_argument("--include-read", action="store_true")

    # stats
    p = sub.add_parser("stats", help="表情使用统计")
    p.add_argument("username")
    p.add_argument("--count", type=int, default=200)
    p.add_argument("--top", type=int, default=20)

    # interactive
    sub.add_parser("interactive", help="交互式 AI 对话模式")

    # account
    p = sub.add_parser("account", help="查看当前登录用户信息")
    # (no extra args needed)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    agent = ShuiyuanAgent()

    if args.command == "account":
        agent._ensure_client()
        user = agent.client.current_user().get("current_user", {})
        print(f"\n👤 当前用户: @{user.get('username', '?')}")
        print(f"   ID: {user.get('id', '?')}")
        print(f"   邮箱: {user.get('email', '?')}")
        print(f"   管理员: {user.get('admin', False)}")
        return

    # Route to handler
    method = getattr(agent, f"cmd_{args.command}", None)
    if method is None:
        print(f"未知命令: {args.command}")
        return

    try:
        method(args)
    except AuthError as e:
        print(f"❌ 认证失败: {e}")
        print("请运行: python auth/user_api_key_auth.py")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n已取消。")
    except Exception as e:
        print(f"❌ 错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
