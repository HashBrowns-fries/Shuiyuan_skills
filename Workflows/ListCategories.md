# 查看分类

列出水源社区的所有分类。

## Input

无

## Implementation

```python
from shuiyuan_client import ShuiyuanClient

client = ShuiyuanClient()
data = client.categories()

categories = data.get("category_list", {}).get("categories", [])
for c in categories:
    print(f"{c.get('id')}\t{c.get('name')}")
```

## Script

参考：`D:\Water\shuiyuan_agent\list_categories.py`

```bash
cd D:\Water\shuiyuan_agent
python list_categories.py
```