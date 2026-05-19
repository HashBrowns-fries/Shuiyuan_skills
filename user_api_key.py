import argparse
import base64
import json
import os
import uuid
import webbrowser
from pathlib import Path
from urllib.parse import urlencode, urlparse, parse_qs

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

from shuiyuan_client import BASE_URL, ShuiyuanClient

PRIVATE_KEY_FILE = Path("./.shuiyuan_user_api_private.pem")
PUBLIC_KEY_FILE = Path("./.shuiyuan_user_api_public.pem")
STATE_FILE = Path("./shuiyuan_user_api_state.json")
KEY_FILE = Path("./shuiyuan_user_api_key.json")


def b64decode_padded(s: str) -> bytes:
    s = s.strip().replace(" ", "+")
    padding_needed = (-len(s)) % 4
    s += "=" * padding_needed
    try:
        return base64.urlsafe_b64decode(s.encode())
    except Exception:
        return base64.b64decode(s.encode())


def generate_keypair():
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()

    PRIVATE_KEY_FILE.write_bytes(
        private_key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
    )
    PUBLIC_KEY_FILE.write_bytes(
        public_key.public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        )
    )

    return private_key, public_key


def load_private_key():
    return serialization.load_pem_private_key(PRIVATE_KEY_FILE.read_bytes(), password=None)


def make_auth_url(application_name: str, scopes: list[str], auth_redirect: str, open_browser: bool):
    if not PRIVATE_KEY_FILE.exists() or not PUBLIC_KEY_FILE.exists():
        generate_keypair()

    public_key_pem = PUBLIC_KEY_FILE.read_text(encoding="utf-8")
    client_id = f"shuiyuan-agent-{uuid.uuid4().hex[:12]}"
    nonce = uuid.uuid4().hex

    state = {
        "client_id": client_id,
        "nonce": nonce,
        "application_name": application_name,
        "scopes": scopes,
        "auth_redirect": auth_redirect,
    }
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

    params = {
        "application_name": application_name,
        "client_id": client_id,
        "scopes": ",".join(scopes),
        "public_key": public_key_pem,
        "nonce": nonce,
        "auth_redirect": auth_redirect,
    }

    url = f"{BASE_URL}/user-api-key/new?{urlencode(params)}"
    print("打开下面的 URL 授权：")
    print(url)
    print("\n授权后，如果浏览器跳到一个打不开的 localhost/custom URL，复制地址栏完整 URL，再运行：")
    print('python user_api_key.py decrypt --redirect-url "复制的完整URL"')

    if open_browser:
        webbrowser.open(url)


def try_decrypt_payload(payload: str):
    encrypted = b64decode_padded(payload)
    private_key = load_private_key()

    errors = []

    for alg_name, pad in [
        ("PKCS1v15", padding.PKCS1v15()),
        ("OAEP-SHA1", padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA1()), algorithm=hashes.SHA1(), label=None)),
        ("OAEP-SHA256", padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)),
    ]:
        try:
            decrypted = private_key.decrypt(encrypted, pad)
            text = decrypted.decode("utf-8")
            return alg_name, json.loads(text)
        except Exception as e:
            errors.append(f"{alg_name}: {e}")

    raise RuntimeError("无法解密 payload。可能站点返回格式不同，或复制的 URL 不完整。\n" + "\n".join(errors))


def decrypt_redirect_url(redirect_url: str):
    query = parse_qs(urlparse(redirect_url).query)
    payload = None
    for key in ["payload", "encrypted_payload"]:
        if key in query and query[key]:
            payload = query[key][0]
            break

    if not payload:
        fragment = parse_qs(urlparse(redirect_url).fragment)
        for key in ["payload", "encrypted_payload"]:
            if key in fragment and fragment[key]:
                payload = fragment[key][0]
                break

    if not payload:
        raise ValueError("URL 中没有找到 payload / encrypted_payload 参数。")

    alg_name, data = try_decrypt_payload(payload)

    state = {}
    if STATE_FILE.exists():
        state = json.loads(STATE_FILE.read_text(encoding="utf-8"))

    nonce_expected = state.get("nonce")
    nonce_got = data.get("nonce")
    if nonce_expected and nonce_got and nonce_expected != nonce_got:
        raise RuntimeError("nonce 不匹配，拒绝保存 key。")

    key = data.get("key") or data.get("user_api_key") or data.get("api_key")
    if not key:
        raise RuntimeError(f"解密成功但没有找到 key 字段。解密内容：{data}")

    output = {
        "key": key,
        "client_id": state.get("client_id") or data.get("client_id") or "shuiyuan-agent",
        "scopes": state.get("scopes"),
        "username": data.get("username"),
        "decryption": alg_name,
    }
    KEY_FILE.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"User-Api-Key 已保存到 {KEY_FILE.resolve()}")
    print("可以运行：python user_api_key.py test")


def save_existing_key(key: str, client_id: str):
    KEY_FILE.write_text(
        json.dumps({"key": key, "client_id": client_id}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"已保存到 {KEY_FILE.resolve()}")


def test_key():
    client = ShuiyuanClient()
    data = client.current_user()
    print(json.dumps(data, ensure_ascii=False, indent=2)[:3000])


def main():
    parser = argparse.ArgumentParser(description="获取并使用 Discourse User-Api-Key")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_auth = sub.add_parser("auth-url", help="生成授权 URL")
    p_auth.add_argument("--application-name", default="Shuiyuan Agent")
    p_auth.add_argument("--scopes", nargs="+", default=["read"], help="例如: read write")
    p_auth.add_argument("--auth-redirect", default="http://localhost:8765/callback")
    p_auth.add_argument("--open-browser", action="store_true")

    p_dec = sub.add_parser("decrypt", help="解密授权回跳 URL 中的 payload 并保存 key")
    p_dec.add_argument("--redirect-url", required=True)

    p_save = sub.add_parser("save", help="保存已有 User-Api-Key")
    p_save.add_argument("--key", required=True)
    p_save.add_argument("--client-id", default="shuiyuan-agent")

    sub.add_parser("test", help="测试当前 key/cookie 是否可用")

    args = parser.parse_args()

    if args.cmd == "auth-url":
        make_auth_url(args.application_name, args.scopes, args.auth_redirect, args.open_browser)
    elif args.cmd == "decrypt":
        decrypt_redirect_url(args.redirect_url)
    elif args.cmd == "save":
        save_existing_key(args.key, args.client_id)
    elif args.cmd == "test":
        test_key()


if __name__ == "__main__":
    main()