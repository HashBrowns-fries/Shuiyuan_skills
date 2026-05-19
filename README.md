# Shuiyuan

上海交大水源社区（shuiyuan.sjtu.edu.cn）CLI 工具集。

不使用 Playwright / Selenium / Chromium 自动化登录。
User-Api-Key 首次授权需要用户用浏览器手动完成一次授权，之后脚本通过 requests 调用 Discourse API。

## 快速开始

```bash
cd shuiyuan

# 配置认证
python auth/user_api_key_auth.py

# 验证
python list_categories.py
```

## 认证

| 方式 | 命令 |
|------|------|
| User-Api-Key（推荐） | `python auth/user_api_key_auth.py` |
| 手动 Cookie | `python auth/manual_cookie_auth.py` |
| 环境变量 | `SHUIYUAN_USER_API_KEY=xxx` |

## 常用命令

```bash
# 浏览
python browse_latest.py --count 10           # 最新帖子
python query_summarize.py "招募"            # 搜索+汇总
python search_topics.py "关键词"             # 搜索

# 查看
python read_topic.py <topic_id> --limit 5    # 帖子内容
python list_categories.py                    # 分类
python get_user_posts.py <username>         # 用户帖子

# 交互操作（确认后执行）
python reply_confirmed.py <topic_id>         # 回复
python create_topic_confirmed.py            # 发帖
python retort_post.py <post_id> [emoji]      # 贴表情
python delete_post.py --post-id <id>        # 删除回复
```

## 贴表情流程

```bash
# 1. 查看帖子有哪些表情可用
python get_post_retorts.py --post-id 987654 --inspect

# 2. 确认后贴表情（需输入"确认贴表情"）
python retort_post.py 987654 heart
python retort_post.py 987654 like --remove  # 移除
```

## 脚本索引

| 脚本 | 功能 |
|------|------|
| browse_latest.py | 浏览最新帖子 |
| watch_latest.py | 持续巡查新帖 |
| query_summarize.py | 搜索+汇总（支持 topic_id 或关键词） |
| search_topics.py | 搜索 |
| read_topic.py | 读取帖子 |
| list_categories.py | 分类列表 |
| reply_confirmed.py | 回复（确认发送） |
| create_topic_confirmed.py | 发帖（确认发送） |
| get_user_posts.py | 用户帖子 |
| get_topic_posts.py | 帖子所有回复 |
| get_post_imgs.py | 帖子图片 |
| get_post_retorts.py | 表情/reaction |
| get_post_votes.py | 投票 |
| statistic_emoji_usage.py | emoji 统计 |
| newest_recruit.py | 招募帖 |
| retort_post.py | 贴表情 |
| delete_post.py | 删除回复 |

## API Client

```python
from shuiyuan_client import ShuiyuanClient

client = ShuiyuanClient()
client.categories()
client.latest_topics()
client.search("关键词")
client.topic(topic_id)
client.topic_posts_all(topic_id)
client.reply_topic(topic_id, raw)
client.retort_post(post_id, emoji)      # 贴表情
client.delete_post(post_id)             # 删除回复
```

## 项目结构

```
shuiyuan/
├── shuiyuan_client.py     # API Client
├── auth/                   # 认证模块
├── models/                 # 数据模型
├── browse_latest.py       # 浏览脚本
├── watch_latest.py         # 巡帖脚本
├── query_summarize.py      # 查询汇总
└── ...
```
