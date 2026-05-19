---
name: Shuiyuan
description: 上海交大水源社区助手. USE WHEN shuiyuan, shuiyuan.sjtu.edu.cn, water forum, water yuan, 水源, 电院, 上海交大论坛.
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
python browse_latest.py --count 10           # 最新帖子
python watch_latest.py --interval 300        # 持续巡帖
python query_summarize.py "招募"            # 搜索+汇总
python query_summarize.py 475362            # topic_id 汇总
python search_topics.py "关键词"             # 搜索
python read_topic.py <topic_id> --limit 5   # 帖子内容
python list_categories.py                    # 分类
python get_user_posts.py <username>         # 用户帖子
python get_post_imgs.py --post-id <id>     # 图片链接
python get_post_votes.py <topic_id>         # 投票
python get_post_retorts.py --post-id <id> --inspect  # 表情信息
python newest_recruit.py --days 15
python watch_replies.py --once                    # 监控回复通知
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

## Workflow Routing

| 用户说... | 执行 |
|-----------|------|
| 浏览最新帖子 | browse_latest.py --count 10 |
| 持续巡帖 | watch_latest.py --interval 300 |
| 监控回复 | watch_replies.py --once |
| 搜索帖子 | search_topics.py "关键词" |
| 汇总帖子 | query_summarize.py （交互输入） |
| 回复帖子 | reply_confirmed.py （交互输入） |
| 发帖 | create_topic_confirmed.py |
| 查看分类 | list_categories.py |
| 用户帖子 | get_user_posts.py username |
| 贴表情 | get_post_retorts.py --inspect → retort_post.py |
| 删除回复 | delete_post.py post_id |
| 生成 API Key | generate_api_key.py |
| 测试登录 | user_api_key.py test |

## 安全边界

- 只读优先：浏览、搜索、汇总、导出
- 写操作单次触发：回复/发帖/删除/贴表情均需人工确认
- 不批量操作：不循环发帖/回复/贴表情
- 不处理密码：不保存 jAccount 密码，不绕过验证码或权限