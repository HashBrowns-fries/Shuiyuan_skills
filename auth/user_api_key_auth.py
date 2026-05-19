"""
User-Api-Key 认证方式（推荐）

如果已有 key，直接运行：
    python -c "from auth.user_api_key_auth import save_key; save_key()"
然后按提示输入 key 和 client_id。

或在环境变量中设置：
    SHUIYUAN_USER_API_KEY=your-key
    SHUIYUAN_USER_API_CLIENT_ID=shuiyuan-agent
"""
import json
from pathlib import Path

KEY_FILE = Path("shuiyuan_user_api_key.json")


def save_key(key: str = None, client_id: str = "shuiyuan-agent"):
    """保存 User-Api-Key 到文件"""
    if key is None:
        key = input("User-Api-Key: ").strip()
    if not key:
        raise ValueError("key 不能为空")

    client_id = input(f"Client ID [{client_id}]: ").strip() or client_id

    KEY_FILE.write_text(
        json.dumps({"key": key, "client_id": client_id}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"已保存到 {KEY_FILE.resolve()}")


def load_key():
    """从文件加载 key"""
    if not KEY_FILE.exists():
        return None, None
    data = json.loads(KEY_FILE.read_text(encoding="utf-8"))
    return data.get("key"), data.get("client_id", "shuiyuan-agent")


def exists():
    """检查是否已配置"""
    return KEY_FILE.exists()


if __name__ == "__main__":
    save_key()