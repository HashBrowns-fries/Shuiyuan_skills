# Shuiyuan Agent — 乌萨奇（咿——呀哈！）

上海交大水源社区（`shuiyuan.sjtu.edu.cn`）AI 助手。基于 Discourse API，支持浏览、搜索、巡帖、AI 自动回复、贴表情等功能。

## 安装

```bash
git clone https://github.com/HashBrowns-fries/Shuiyuan_skills.git
cd Shuiyuan_skills
uv sync
```

环境变量通过 `.env` 文件自动加载，无需手动 export。

## 认证

```bash
# 推荐：User-Api-Key
uv run python auth/user_api_key_auth.py

# 备用：手动 Cookie（贴表情等功能需要）
uv run python auth/manual_cookie_auth.py

# 查看登录状态
uv run python agent.py account
```

## Agent 统一入口

```bash
# 交互式 AI 对话
uv run python agent.py interactive

# 子命令模式
uv run python agent.py browse --count 10       # 浏览最新
uv run python agent.py search "关键词"          # 搜索
uv run python agent.py read 475362             # 阅读帖子
uv run python agent.py summarize "查询"         # 搜索+汇总
uv run python agent.py categories              # 分类列表
uv run python agent.py user <username>         # 用户帖子
uv run python agent.py reply <topic_id>        # AI 辅助回复
uv run python agent.py post                    # 发新帖
uv run python agent.py watch --interval 300    # 持续巡帖
uv run python agent.py notifications --once    # 检查通知
uv run python agent.py images <post_id>        # 图片链接
uv run python agent.py emojis <post_id>        # 表情回应
uv run python agent.py retort <post_id> <emoji> # 贴表情
uv run python agent.py stats <username>        # 表情统计
uv run python agent.py delete <post_id>        # 删除回复
```

完整命令见 `uv run python agent.py --help`。

## 持续监听自动回复

```bash
# 一次性检查
uv run python conversation_loop.py --topic-id 475459 --once --auto

# 持续监听（2 分钟间隔）
uv run python conversation_loop.py --topic-id 475459 --auto --interval 120
```

## 独立脚本

| 脚本 | 功能 |
|------|------|
| `query_summarize.py` | 通用查询与汇总 |
| `get_post_imgs.py` | 获取帖子图片链接 |
| `get_post_votes.py` | 获取投票信息 |
| `get_post_retorts.py` | 获取表情/reaction 详情 |
| `newest_recruit.py` | 获取招募类帖子 |
| `statistic_emoji_usage.py` | emoji 使用统计 |
| `watch_replies.py` | 监控回复/引用/提及 |
| `watch_latest.py` | 持续巡帖 |
| `user_api_key.py` | User-Api-Key 管理 |

## 安全边界

- 读操作直接执行，写操作（reply/post/delete/retort）需人工确认
- 不批量操作，不循环发帖/回复
- 不保存或处理 jAccount 密码
- `.env`、认证文件和 Cookie 不提交 Git

## 项目结构

```text
shuiyuan/
├── agent.py                  # 统一 Agent 入口
├── shuiyuan_client.py        # Discourse API Client
├── ai_reply.py               # AI 回复生成（MiniMax M2.7）
├── conversation_loop.py      # 持续监听 + 自动回复
├── query_summarize.py        # 查询与汇总
├── watch_latest.py           # 最新帖巡查
├── watch_replies.py          # 回复通知监控
├── get_post_imgs.py          # 图片链接提取
├── get_post_votes.py         # 投票信息
├── get_post_retorts.py       # 表情信息
├── newest_recruit.py         # 招募检索
├── statistic_emoji_usage.py  # emoji 统计
├── text_utils.py             # HTML→文本、emoji 提取
├── env_loader.py             # .env 加载
├── auth/
│   ├── user_api_key_auth.py
│   └── manual_cookie_auth.py
├── Workflows/                # Skill 工作流文档
├── SKILL.md
├── CLAUDE.md
├── pyproject.toml
└── .env                      # API Key（gitignore）
```

## 环境变量（.env）

| 变量 | 说明 |
|------|------|
| `MINIMAX_API_KEY` | MiniMax API Key（AI 回复） |
| `SHUIYUAN_BASE_URL` | 水源地址（默认 shuiyuan.sjtu.edu.cn） |
| `SHUIYUAN_USER_API_KEY` | User-Api-Key |
| `SHUIYUAN_USER_API_CLIENT_ID` | Client ID（默认 shuiyuan-agent） |

## 免责声明

本项目仅用于个人学习和社区浏览辅助。使用时请遵守水源社区规则和 Discourse API 限制。
