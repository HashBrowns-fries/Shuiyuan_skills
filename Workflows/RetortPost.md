# 贴表情

给帖子贴上 emoji 表情（retort）。

## Input

- post_id：帖子 ID
- emoji：表情名称（如 `like`, `heart`）
- `--remove`：移除表情
- `--yes`：跳过确认

## Implementation

```python
from shuiyuan_client import ShuiyuanClient

client = ShuiyuanClient()
post = client.post_by_id(post_id)

if not post.get("can_retort"):
    print("无法贴表情")
    return

# 贴表情
client.retort_post(post_id, emoji_name)
```

## Workflow

1. 先查看帖子表情信息：
   ```bash
   python get_post_retorts.py --post-id <id> --inspect
   ```

2. 确认后贴表情（需输入"确认贴表情"）：
   ```bash
   python retort_post.py <post_id> <emoji>
   python retort_post.py <post_id> <emoji> --remove  # 移除
   ```

3. 跳过确认（agent 使用）：
   ```bash
   python retort_post.py <post_id> <emoji> --yes
   ```

## Notes

- 只能贴自己已有的表情（在水源设置中添加的）
- 回复需要输入"确认贴表情"才会执行，agent 加 `--yes` 跳过