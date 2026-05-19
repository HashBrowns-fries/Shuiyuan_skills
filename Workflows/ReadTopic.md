# 查看帖子内容

读取单个帖子的楼层内容。

## Input

用户提供帖子 ID。

## Implementation

```python
from shuiyuan_client import ShuiyuanClient
from models.topic import Topic

client = ShuiyuanClient()
topic = client.get_single_topic(topic_id)

print(f"标题: {topic.title}")
print(f"链接: https://shuiyuan.sjtu.edu.cn/t/{topic_id}")
print(f"回复数: {topic.reply_count}, 点赞数: {topic.like_count}")

for post in topic.post_stream.posts[:limit]:
    print(f"#{post.post_number} {post.username} | {post.created_at}")
    print(post.cooked[:3000])
```

## Script

参考：`D:\Water\shuiyuan_agent\read_topic.py`

```bash
cd D:\Water\shuiyuan_agent
python read_topic.py <topic_id> --limit 10
```