---
name: Shuiyuan
description: 上海交大水源社区助手. USE WHEN shuiyuan, shuiyuan.sjtu.edu.cn, water forum, water yuan, 水源, 电院, 上海交大论坛, browse/post/search forum.
---

# Shuiyuan Skill

上海交大水源社区（shuiyuan.sjtu.edu.cn）助手。

**工作目录:** `D:\Water\shuiyuan_agent\`（所有命令在此目录下执行）

## 快速开始

```bash
cd D:\Water\shuiyuan_agent

# 1. 配置认证（选一种）
python auth/user_api_key_auth.py   # 推荐：保存 User-Api-Key
python auth/manual_cookie_auth.py  # 备用：手动复制 Cookie

# 2. 验证登录
python list_categories.py
```

## 典型任务

### 浏览帖子

```bash
# 最新帖子
python browse_latest.py --count 10

# 搜索并汇总
python query_summarize.py "招募"           # 关键词
python query_summarize.py 475362           # topic_id

# 读取帖子内容
python read_topic.py 475362 --limit 5
```

### 回复/发帖

```bash
# 回复（确认后发送）
python reply_confirmed.py <topic_id>

# 发帖（确认后发送）
python create_topic_confirmed.py

# 贴表情
python retort_post.py --post-id <id> --add <emoji_key>
```

### 查询

```bash
# 分类列表
python list_categories.py

# 搜索帖子
python search_topics.py "关键词"

# 用户帖子
python get_user_posts.py <username> --limit 100
```

## Client API

```python
from shuiyuan_client import ShuiyuanClient

client = ShuiyuanClient()  # 自动加载认证

# 常用方法
client.categories()              # 分类列表
client.latest_topics()           # 最新帖子
client.search("关键词")           # 搜索
client.topic(topic_id)           # 帖子信息
client.topic_posts_all(topic_id)  # 所有回复
client.reply_topic(topic_id, raw) # 回复
client.user_posts(username)      # 用户帖子
client.post_by_id(post_id)        # 单条回复
client.retort_post(post_id, reaction_key)  # 贴表情
client.delete_post(post_id)       # 删除回复
```

## Workflow Routing

| 用户说... | 执行 |
|-----------|------|
| 浏览最新帖子 | browse_latest.py --count 10 |
| 搜索帖子 "关键词" | search_topics.py "关键词" |
| 汇总帖子 | query_summarize.py （交互输入 topic_id） |
| 回复帖子 | reply_confirmed.py （交互输入） |
| 发帖 | create_topic_confirmed.py |
| 查看分类 | list_categories.py |
| 贴表情 | retort_post.py --post-id X --add emoji |
| 删除回复 | delete_post.py --post-id X |
| 获取用户帖子 | get_user_posts.py username |

## 认证（优先级）

1. `SHUIYUAN_USER_API_KEY` 环境变量
2. `auth/user_api_key.json`（User-Api-Key）
3. `auth/manual_cookie.json`（手动 Cookie）

## 脚本列表

| 脚本 | 功能 |
|------|------|
| browse_latest.py | 浏览最新帖子 |
| watch_latest.py | 持续巡查新帖 |
| query_summarize.py | 通用查询-汇总 |
| search_topics.py | 搜索 |
| read_topic.py | 读取帖子 |
| reply_confirmed.py | 回复（确认发送） |
| create_topic_confirmed.py | 发帖（确认发送） |
| list_categories.py | 分类列表 |
| get_user_posts.py | 用户帖子 |
| get_topic_posts.py | 帖子所有回复 |
| get_post_imgs.py | 帖子图片 |
| get_post_retorts.py | 表情/reaction |
| statistic_emoji_usage.py | emoji 统计 |
| newest_recruit.py | 招募帖 |
| delete_post.py | 删除回复 |
| retort_post.py | 贴表情 |