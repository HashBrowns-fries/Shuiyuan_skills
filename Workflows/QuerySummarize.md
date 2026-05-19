# 汇总帖子

通用查询-汇总流程，支持搜索关键词或直接指定 topic_id。

## Input

用户输入搜索关键词或 topic_id。

## Implementation

```python
from shuiyuan_client import ShuiyuanClient

client = ShuiyuanClient()

# 如果是数字，直接查 topic
if query.isdigit():
    topic_id = int(query)
else:
    # 搜索取第一个结果
    data = client.search(query)
    topic_id = data['topics'][0]['id']

# 汇总帖子内容
posts = client.topic_posts_all(topic_id, limit=limit)
```

## Usage

```bash
# 搜索关键词并汇总
python query_summarize.py "招募"

# 直接查看帖子
python query_summarize.py 475362

# 汇总并准备回复
python query_summarize.py 475362 --limit 10 --prepare-reply reply.md

# 确认后发送回复
python query_summarize.py 475362 --reply-file reply.md --send
```

## Reply Confirmation

发送回复必须输入"确认发送"才会发布。

## Generalize Pattern

此脚本体现了"查询-汇总"通用逻辑：
1. 用户输入可以是关键词或 ID
2. 搜索找到目标帖子
3. 汇总前 N 楼内容
4. 可选：准备回复草稿
5. 可选：确认后发送