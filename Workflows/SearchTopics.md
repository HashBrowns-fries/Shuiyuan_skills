# 搜索帖子

在水源社区搜索帖子。

## Input

用户提供关键词和排序方式。

## Implementation

```python
from shuiyuan_client import ShuiyuanClient
from models.search import SearchQuery, SearchQueryOrder

client = ShuiyuanClient()
query = SearchQuery(term="关键词", order=SearchQueryOrder.LATEST)
result = client.advanced_search(query)
```

## Output

```python
for t in result.topics:
    print(f"ID: {t.id}")
    print(f"标题: {t.title}")
    print(f"楼层数: {t.posts_count}, 点赞数: {t.like_count}")
    print(f"链接: https://shuiyuan.sjtu.edu.cn/t/{t.id}")
```

## Script

参考：`D:\Water\shuiyuan_agent\search_topics.py`

```bash
cd D:\Water\shuiyuan_agent
python search_topics.py "关键词"
```