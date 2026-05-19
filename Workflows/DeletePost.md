# 删除回复

删除自己发布的回复。

## Input

用户提供要删除的帖子 ID。

## Implementation

```python
from shuiyuan_client import ShuiyuanClient

client = ShuiyuanClient()
post = client.post_by_id(post_id)

if not post.get("can_delete"):
    print("无法删除：没有权限")
    return

# 确认后删除
resp = client.session.delete(f"{client.base_url}/posts/{post_id}.json")
```

## Confirmation

必须用户输入"确认删除"才会删除。

## Script

```bash
cd D:\Water\shuiyuan_agent
python delete_post.py <post_id>
```

**注意**：只能删除自己的帖子，且需要版主权限或帖子未被回复。