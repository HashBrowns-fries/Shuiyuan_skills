"""
手动复制 Cookie 认证方式（备用）

步骤：
1. 在浏览器登录水源
2. 打开开发者工具（F12）→ Network → 找到任意请求 → 复制 Cookie 请求头
3. 运行脚本粘贴

示例 Cookie 格式：
    _ga=GA1.2.xxx; _gat=1; __cfduid=xxx; _forum_session=xxx; ...
"""
import json
import os
from pathlib import Path

COOKIE_FILE = Path("shuiyuan_cookies_manual.json")


def save_cookie_from_header():
    """从粘贴的 Cookie 字符串解析并保存"""
    cookie_header = input("粘贴 Cookie 请求头（不要加 Cookie: 前缀）：\n").strip()

    cookies = {}
    for item in cookie_header.split(";"):
        item = item.strip()
        if not item or "=" not in item:
            continue
        k, v = item.split("=", 1)
        cookies[k.strip()] = v.strip()

    if not cookies:
        raise ValueError("没有解析到有效的 cookie")

    COOKIE_FILE.write_text(
        json.dumps(cookies, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"已保存到 {COOKIE_FILE.resolve()}，共 {len(cookies)} 条")


def load_cookie():
    """从文件加载 cookie dict"""
    if not COOKIE_FILE.exists():
        return None
    return json.loads(COOKIE_FILE.read_text(encoding="utf-8"))


def exists():
    """检查是否已配置"""
    return COOKIE_FILE.exists()


if __name__ == "__main__":
    save_cookie_from_header()