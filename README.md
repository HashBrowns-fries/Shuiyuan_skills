# Shuiyuan Agent

上海交大水源社区（shuiyuan.sjtu.edu.cn）助手，基于 Discourse API。

**不依赖浏览器内核**，支持多种认证方式。

## 安装

```bash
pip install -r requirements.txt
```

## 认证方式

### 方式 A：User-Api-Key（推荐）

```bash
# 如果已有 key，直接保存
python auth/user_api_key_auth.py
# 或
python user_api_key.py save --key "YOUR_KEY" --client-id "shuiyuan-agent"

# 如果需要生成新 key
python generate_api_key.py
```

### 方式 B：手动 Cookie

```bash
python auth/manual_cookie_auth.py
```

### 方式 C：环境变量

```bash
export SHUIYUAN_USER_API_KEY=your-key
export SHUIYUAN_USER_API_CLIENT_ID=shuiyuan-agent
```

## 常用脚本

```bash
# 看最新帖子
python browse_latest.py --count 10 --unseen-only

# 持续巡帖（每隔 5 分钟检查新帖）
python watch_latest.py --interval 300 --count 20

# 导出某主题所有 posts
python get_topic_posts.py 123456 --output topic_123456.json

# 获取某 post 的图片链接
python get_post_imgs.py --post-id 987654

# 获取 post 被贴的表情 / reaction / retort 信息
python get_post_retorts.py --post-id 987654 --inspect

# 统计某用户 emoji 使用
python statistic_emoji_usage.py --username someone --limit 500

# 获取某用户所有 posts
python get_user_posts.py someone --limit 300 --output user_posts.json

# 获取近半个月招募信息
python newest_recruit.py --days 15

# 汇总帖子并准备回复文件
python summarize_reply_confirmed.py 123456 --prepare-reply reply.md

# 人工确认后发送回复
python summarize_reply_confirmed.py 123456 --reply-file reply.md --send

# 通用查询-汇总（支持关键词或 topic_id）
python query_summarize.py "招募"
python query_summarize.py 475362
```

## 脚本列表

| 脚本 | 功能 |
|------|------|
| `browse_latest.py` | 浏览最新帖子，支持 --unseen-only |
| `watch_latest.py` | 持续巡查新帖子 |
| `get_topic_posts.py` | 导出主题所有 posts |
| `get_post_imgs.py` | 获取帖子图片链接 |
| `get_post_votes.py` | 获取投票信息 |
| `get_post_retorts.py` | 获取表情/reaction 信息 |
| `get_user_posts.py` | 获取用户所有 posts |
| `statistic_emoji_usage.py` | 统计用户 emoji 使用 |
| `newest_recruit.py` | 获取招募类帖子 |
| `summarize_reply_confirmed.py` | 汇总帖子 + 确认回复 |
| `latest_topics.py` | 查看最新帖子列表 |
| `list_categories.py` | 查看分类 |
| `search_topics.py` | 搜索帖子 |
| `read_topic.py` | 读取帖子内容 |
| `reply_confirmed.py` | 回复帖子（确认后发送） |
| `create_topic_confirmed.py` | 发布新帖（确认后发送） |
| `query_summarize.py` | 通用查询-汇总脚本 |
| `delete_post.py` | 删除回复 |
| `retort_post.py` | 贴表情/反应 |
| `generate_api_key.py` | 生成 User-Api-Key（需要浏览器） |
| `user_api_key.py` | User-Api-Key 管理（auth-url/decrypt/save/test） |

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `SHUIYUAN_BASE_URL` | `https://shuiyuan.sjtu.edu.cn` | 站点地址 |
| `SHUIYUAN_USER_API_KEY` | - | 直接设置 API Key |
| `SHUIYUAN_USER_API_CLIENT_ID` | `shuiyuan-agent` | API Client ID |

## 项目结构

```
shuiyuan_agent/
├── shuiyuan_client.py     # 核心 Client
├── auth/
│   ├── user_api_key_auth.py   # User-Api-Key 认证
│   └── manual_cookie_auth.py  # 手动 Cookie 认证
├── models/               # 数据模型
│   ├── topic.py
│   ├── search.py
│   └── common.py
├── browse_latest.py       # 浏览脚本
├── watch_latest.py        # 巡帖脚本
├── query_summarize.py     # 通用汇总脚本
└── ...
```