# 回复帖子

向指定帖子发送回复。

## Input

- 帖子 ID
- 回复内容（文本或文件路径）

## Implementation

```python
from shuiyuan_client import ShuiyuanClient

client = ShuiyuanClient()
result = client.reply_topic(topic_id=topic_id, raw=reply_content)
```

## Confirmation

必须用户输入"确认发送"才会发布。

## Script

参考：`D:\Water\shuiyuan_agent\reply_confirmed.py`

```bash
cd D:\Water\shuiyuan_agent
python reply_confirmed.py <topic_id>
# 或从文件读取
python reply_confirmed.py <topic_id> --file reply.md
```