# 最新帖子

查看水源社区最新帖子列表。

## Input

```python
from shuiyuan_client import ShuiyuanClient
client = ShuiyuanClient()
data = client.latest_topics()
```

## Output

遍历并显示帖子信息：

```python
topics = data.get("topic_list", {}).get("topics", [])
for t in topics[:20]:
    topic_id = t.get("id")
    title = t.get("title")
    reply_count = t.get("reply_count")
    posts_count = t.get("posts_count")
    last_posted_at = t.get("last_posted_at")
    print(f"ID: {topic_id}")
    print(f"标题: {title}")
    print(f"回复数: {reply_count}, 总楼层: {posts_count}")
    print(f"最后活动: {last_posted_at}")
    print(f"链接: https://shuiyuan.sjtu.edu.cn/t/{topic_id}")
```

## Script

参考：`D:\Water\shuiyuan_agent\latest_topics.py`

```bash
cd D:\Water\shuiyuan_agent
python latest_topics.py
```