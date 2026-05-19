# 贴表情

给帖子贴上 emoji 表情（retort）。

## Input

- post_id：帖子 ID
- emoji：表情名称（如 `like`, `heart`, `distorted_face`）
- `--remove`：移除表情

## Implementation

```python
from shuiyuan_client import ShuiyuanClient

client = ShuiyuanClient()
post = client.post_by_id(post_id)

if not post.get("can_retort"):
    print("无法贴表情")
    return

# 贴表情
url = f"{client.base_url}/posts/{post_id}/retort"
data = {"emoji": emoji_name}
resp = client.session.post(url, json=data, headers={"X-CSRF-Token": csrf})
```

## Examples

```bash
# 查看当前帖子有哪些表情
python retort_post.py 9033310

# 贴一个表情
python retort_post.py 9033310 distorted_face

# 移除一个表情
python retort_post.py 9033310 distorted_face --remove
```

## Notes

- 只能贴自己已有的表情（在水源设置中添加的）
- 不同站点的 emoji 列表可能不同
- `my_retorts` 字段显示已贴的表情