# 发布新帖

在水源社区发布新主题帖。

## Input

- 标题
- 正文内容（文本或文件路径）
- 分类 ID

## Implementation

```python
from shuiyuan_client import ShuiyuanClient

client = ShuiyuanClient()
result = client.create_topic(title=title, raw=raw, category_id=category_id)
```

## Confirmation

必须用户输入"确认发送"才会发布。

## Script

参考：`D:\Water\shuiyuan_agent\create_topic_confirmed.py`

```bash
cd D:\Water\shuiyuan_agent
python create_topic_confirmed.py --title "标题" --category 1
# 或从文件读取
python create_topic_confirmed.py --title "标题" --category 1 --file post.md
```