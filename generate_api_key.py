"""
User-Api-Key 生成工具

使用方法:
    python generate_api_key.py

流程:
1. 生成 RSA 密钥对
2. 在浏览器中完成授权
3. 粘贴服务器返回的 payload
4. 获取 User-Api-Key
"""
from dataclasses import dataclass
from datetime import datetime
import base64
import json
import secrets
import urllib.parse
import uuid
import webbrowser
from collections.abc import Iterable
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa


BASE_URL = "https://shuiyuan.sjtu.edu.cn"
ALL_SCOPES = [
    "read",
    "write",
    "message_bus",
    "push",
    "one_time_password",
    "notifications",
    "session_info",
    "bookmarks_calendar",
    "user_status",
]
DEFAULT_SCOPES = ["read"]


@dataclass
class UserApiKeyPayload:
    key: str
    nonce: str
    push: bool
    api: int


@dataclass
class UserApiKeyRequestResult:
    client_id: str
    payload: UserApiKeyPayload


def generate_user_api_key(
    application_name: str,
    *,
    client_id: str | None = None,
    scopes: Iterable[str] | None = None,
) -> UserApiKeyRequestResult:
    """
    生成 User-Api-Key

    Args:
        application_name: 应用名称
        client_id: 可选，自定义客户端 ID
        scopes: 可选，权限列表，默认 ['read']

    Returns:
        UserApiKeyRequestResult，包含 client_id 和 payload
    """
    # Generate RSA key pair.
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=4096,
    )
    public_key = private_key.public_key()
    public_key_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("ascii")

    # Generate a random client ID if not provided.
    client_id_to_use = str(uuid.uuid4()) if client_id is None else client_id
    nonce = secrets.token_urlsafe(32)

    # Validate scopes.
    scopes_list = DEFAULT_SCOPES if scopes is None else list(scopes)
    if not set(scopes_list) <= set(ALL_SCOPES):
        raise ValueError("Invalid scopes")

    # Build request URL and open in browser.
    params_dict: dict[str, str] = {
        "application_name": application_name,
        "client_id": client_id_to_use,
        "scopes": ",".join(scopes_list),
        "public_key": public_key_pem,
        "nonce": nonce,
    }
    params_str = "&".join(
        f"{k}={urllib.parse.quote(v)}" for k, v in params_dict.items()
    )
    webbrowser.open(f"{BASE_URL}/user-api-key/new?{params_str}")

    # Receive, decrypt and check response payload from server.
    print("请在浏览器中完成授权，然后复制页面上的响应 payload（base64 字符串）")
    print("Paste the response payload here: ", end="", flush=True)
    enc_payload = input().strip()

    dec_payload = UserApiKeyPayload(
        **json.loads(
            private_key.decrypt(
                base64.b64decode(enc_payload),
                padding.PKCS1v15(),
            )
        )
    )

    if dec_payload.nonce != nonce:
        raise ValueError("Nonce mismatch")

    # Return client ID and response payload.
    return UserApiKeyRequestResult(
        client_id=client_id_to_use,
        payload=dec_payload,
    )


def main():
    print("=" * 60)
    print("User-Api-Key 生成工具")
    print("=" * 60)
    print()

    app_name = input("输入应用名称（回车默认: ShuiyuanAssistant）: ").strip()
    if not app_name:
        app_name = "ShuiyuanAssistant"

    print(f"\n将使用应用名称: {app_name}")
    print("权限范围: read, write, notifications, session_info")
    print()

    scopes_input = input("是否使用默认权限范围？（回车/输入 n 自定义）: ").strip().lower()
    if scopes_input == "n":
        print("可用权限:", ALL_SCOPES)
        scopes_str = input("输入权限（逗号分隔）: ").strip()
        scopes = [s.strip() for s in scopes_str.split(",") if s.strip()]
    else:
        scopes = ["read", "write", "notifications", "session_info"]

    print(f"\n使用权限: {scopes}")
    print()
    print("即将打开浏览器，请在浏览器中完成 jAccount 授权...")
    input("按 Enter 继续...")

    result = generate_user_api_key(app_name, scopes=scopes)

    print()
    print("=" * 60)
    print("授权成功！")
    print("=" * 60)
    print(f"Client ID: {result.client_id}")
    print(f"API Key: {result.payload.key}")
    print()
    print("使用方式:")
    print(f"  from shuiyuan_client import ShuiyuanClient")
    print(f"  client = ShuiyuanClient(user_api_key='{result.payload.key}')")
    print()
    print("建议将 API Key 保存到环境变量或配置文件中")


if __name__ == "__main__":
    main()