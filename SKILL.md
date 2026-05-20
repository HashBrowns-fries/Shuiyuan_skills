---
name: Shuiyuan
description: 上海交大水源社区助手 · 乌萨奇（咿——呀哈！）. USE WHEN shuiyuan, shuiyuan.sjtu.edu.cn, water forum, water yuan, 水源, 电院, 上海交大论坛.
---

# Shuiyuan Skill

上海交大水源社区（shuiyuan.sjtu.edu.cn）Discourse API 工具集。

**工作目录:** `D:\Water\shuiyuan\`

## 认证

```bash
cd D:\Water\shuiyuan

# 推荐：User-Api-Key
python auth/user_api_key_auth.py

# 备用：手动 Cookie
python auth/manual_cookie_auth.py
```

认证优先级：环境变量 > `auth/user_api_key.json` > `auth/manual_cookie.json`

## 读操作（直接执行）

```bash
# Agent 统一入口（推荐）
uv run python agent.py browse --count 10
uv run python agent.py search "关键词"
uv run python agent.py read <topic_id>
uv run python agent.py summarize "查询"
uv run python agent.py categories
uv run python agent.py user <username>
uv run python agent.py watch --interval 300
uv run python agent.py notifications --once

# 独立脚本（特殊功能）
python get_post_imgs.py --post-id <id>     # 图片链接
python get_post_votes.py <topic_id>         # 投票
python get_post_retorts.py --post-id <id> --inspect  # 表情信息
python newest_recruit.py --days 15          # 最新招募
```

## 写操作（需确认）

```bash
python reply_confirmed.py <topic_id>         # 回复
python create_topic_confirmed.py            # 发帖
python delete_post.py <post_id>             # 删除
python retort_post.py <post_id> [emoji]     # 贴表情
```

写操作需输入确认词（`确认发送`/`确认删除`/`确认贴表情`）。Agent 可加 `--yes` 跳过。

## Client API

```python
from shuiyuan_client import ShuiyuanClient

client = ShuiyuanClient()
client.categories()
client.latest_topics()
client.search("关键词")
client.topic(topic_id)
client.topic_posts_all(topic_id)
client.reply_topic(topic_id, raw)
client.retort_post(post_id, emoji)
client.delete_post(post_id)
client.user_posts(username)
client.post_by_id(post_id)
```

## Agent（推荐入口）

```bash
cd D:\Water\shuiyuan

# 交互式 AI 对话（推荐）
uv run python agent.py interactive

# 或直接用子命令
uv run python agent.py browse --count 10
uv run python agent.py search "关键词"
uv run python agent.py read <topic_id>
uv run python agent.py reply <topic_id>
uv run python agent.py watch --interval 300
uv run python agent.py notifications --once
```

Agent 覆盖所有操作，详见 `python agent.py --help`。

## Workflow Routing

| 用户说... | Agent 命令 |
|-----------|-----------|
| 浏览最新帖子 | `agent.py browse --count 10` |
| 持续巡帖 | `agent.py watch --interval 300` |
| 监控回复 | `agent.py notifications --once` |
| 搜索帖子 | `agent.py search "关键词"` |
| 汇总帖子 | `agent.py summarize "查询"` |
| 回复帖子 | `agent.py reply <topic_id>` |
| 发帖 | `agent.py post` |
| 查看分类 | `agent.py categories` |
| 用户帖子 | `agent.py user <username>` |
| 贴表情 | `agent.py retort <post_id>` |
| 删除回复 | `agent.py delete <post_id>` |
| 获取图片 | `agent.py images <post_id>` |
| 查看表情回应 | `agent.py emojis <post_id>` |
| 表情统计 | `agent.py stats <username>` |
| 测试登录 | `agent.py account`

## 安全边界

- 只读优先：浏览、搜索、汇总、导出
- 写操作单次触发：回复/发帖/删除/贴表情均需人工确认
- 不批量操作：不循环发帖/回复/贴表情
- 不处理密码：不保存 jAccount 密码，不绕过验证码或权限