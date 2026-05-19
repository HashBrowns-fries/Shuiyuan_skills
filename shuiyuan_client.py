"""
Shuiyuan / Discourse client.

认证优先级（按顺序）：
1. User-Api-Key（推荐）：环境变量 SHUIYUAN_USER_API_KEY 或 auth/user_api_key.json
2. 手动 Cookie：auth/manual_cookie.json
3. 旧版 Cookie：shuiyuan_cookies.json（兼容）

不保存 jAccount 密码，不使用浏览器模拟登录。
"""
import json
import os
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple, Union

import requests

from auth.user_api_key_auth import load_key as load_user_api_key
from auth.manual_cookie_auth import load_cookie as load_manual_cookie

BASE_URL = os.getenv("SHUIYUAN_BASE_URL", "https://shuiyuan.sjtu.edu.cn").rstrip("/")

ParamsType = Optional[Union[Dict[str, Any], List[Tuple[str, Any]]]]


class AuthError(Exception):
    """认证失败"""
    pass


class ShuiyuanClient:
    """
    Shuiyuan / Discourse client.

    自动按优先级加载认证：
    1. User-Api-Key（推荐）
    2. 手动复制 Cookie
    3. 旧版 Cookie 文件（兼容）
    """

    def __init__(
        self,
        base_url: str = BASE_URL,
        user_api_key: str | None = None,
        user_api_client_id: str = "shuiyuan-agent",
    ):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 ShuiyuanAgent/0.3",
                "Accept": "application/json, text/plain, */*",
                "Referer": self.base_url + "/",
            }
        )

        self.auth_type = None

        if user_api_key:
            self.session.headers.update(
                {
                    "User-Api-Key": user_api_key,
                    "User-Api-Client-Id": user_api_client_id,
                }
            )
            self.auth_type = "user_api_key"
        else:
            self._init_auth()

    def _init_auth(self):
        """按优先级初始化认证"""
        # 1. 尝试 User-Api-Key
        key = os.getenv("SHUIYUAN_USER_API_KEY")
        client_id = os.getenv("SHUIYUAN_USER_API_CLIENT_ID", "shuiyuan-agent")

        if not key:
            key, client_id = load_user_api_key()

        if key:
            self.session.headers.update({
                "User-Api-Key": key,
                "User-Api-Client-Id": client_id,
            })
            self.auth_type = "user_api_key"
            return

        # 2. 尝试手动 Cookie
        cookies = load_manual_cookie()
        if cookies:
            self.session.cookies.update(cookies)
            self.auth_type = "manual_cookie"
            return

        # 3. 尝试旧版 Cookie 文件（兼容）
        cookie_file = Path("./shuiyuan_cookies.json")
        if cookie_file.exists():
            self._load_playwright_cookies(cookie_file)
            self.auth_type = "legacy_cookie"
            return

        # 无认证
        raise AuthError(
            "未配置认证。请选择以下方式之一：\n"
            "1. 配置 User-Api-Key：运行 python auth/user_api_key_auth.py\n"
            "2. 手动复制 Cookie：运行 python auth/manual_cookie_auth.py"
        )

    def _load_playwright_cookies(self, cookie_file: Path):
        """加载旧版 cookies 文件（兼容）"""
        raw = cookie_file.read_text(encoding="utf-8")
        # Playwright 格式是列表
        if raw.startswith("["):
            cookies = json.loads(raw)
            for c in cookies:
                self.session.cookies.set(
                    name=c["name"],
                    value=c["value"],
                    domain=c.get("domain", "shuiyuan.sjtu.edu.cn"),
                    path=c.get("path", "/"),
                )
        else:
            # 手动 Cookie 格式是 dict
            cookies = json.loads(raw)
            self.session.cookies.update(cookies)

    def url(self, path: str) -> str:
        if path.startswith("http"):
            return path
        return self.base_url + path

    def get(self, path: str, params: ParamsType = None):
        r = self.session.get(self.url(path), params=params, timeout=30)
        return self._handle_response(r)

    def post(self, path: str, data: Optional[Dict[str, Any]] = None):
        headers = {"Content-Type": "application/json"}

        # 非 User-Api-Key 模式需要 CSRF
        if self.auth_type != "user_api_key":
            headers["X-CSRF-Token"] = self.get_csrf_token()

        r = self.session.post(
            self.url(path),
            json=data or {},
            headers=headers,
            timeout=30,
        )
        return self._handle_response(r)

    def get_csrf_token(self) -> str:
        result = self.get("/session/csrf.json")
        csrf = result.get("csrf")
        if not csrf:
            raise RuntimeError("没有获取到 CSRF token，可能登录态已失效。")
        return csrf

    def current_user(self):
        return self.get("/session/current.json")

    def latest_topics(self, page: Optional[int] = None):
        path = "/latest.json" if page is None else f"/latest.json?page={page}"
        return self.get(path)

    def categories(self):
        return self.get("/categories.json")

    def search(self, keyword: str):
        return self.get("/search.json", params={"q": keyword})

    def topic(self, topic_id: int):
        return self.get(f"/t/{topic_id}.json")

    def post_by_id(self, post_id: int):
        return self.get(f"/posts/{post_id}.json")

    def topic_posts_chunk(self, topic_id: int, post_ids: Iterable[int]):
        params: List[Tuple[str, Any]] = []
        for pid in post_ids:
            params.append(("post_ids[]", int(pid)))
        return self.get(f"/t/{topic_id}/posts.json", params=params)

    def topic_posts_all(self, topic_id: int, chunk_size: int = 20, limit: Optional[int] = None):
        topic = self.topic(topic_id)
        post_stream = topic.get("post_stream", {})
        stream_ids = post_stream.get("stream", []) or []
        initial_posts = post_stream.get("posts", []) or []

        if not stream_ids:
            return initial_posts[:limit] if limit else initial_posts

        if limit:
            stream_ids = stream_ids[:limit]

        by_id: Dict[int, Dict[str, Any]] = {}
        for p in initial_posts:
            if p.get("id") is not None:
                by_id[int(p["id"])] = p

        missing_ids = [int(pid) for pid in stream_ids if int(pid) not in by_id]

        for i in range(0, len(missing_ids), chunk_size):
            chunk = missing_ids[i : i + chunk_size]
            data = self.topic_posts_chunk(topic_id, chunk)
            posts = data.get("post_stream", {}).get("posts", []) or data.get("posts", []) or []
            for p in posts:
                if p.get("id") is not None:
                    by_id[int(p["id"])] = p

        posts = [by_id[pid] for pid in stream_ids if int(pid) in by_id]
        posts.sort(key=lambda p: p.get("post_number", 10**9))
        return posts

    def user_actions(self, username: str, filter_type: int, offset: int = 0):
        return self.get(
            "/user_actions.json",
            params={"username": username, "filter": filter_type, "offset": offset},
        )

    def user_posts(
        self,
        username: str,
        include_topics: bool = True,
        include_replies: bool = True,
        limit: int = 200,
    ):
        """获取用户主题帖和回复。Discourse filter: 4=topics, 5=replies"""
        filters = []
        if include_topics:
            filters.append(4)
        if include_replies:
            filters.append(5)

        all_actions = []
        seen_keys = set()

        for filter_type in filters:
            offset = 0
            while len(all_actions) < limit:
                data = self.user_actions(username, filter_type=filter_type, offset=offset)
                actions = data.get("user_actions", []) or []
                if not actions:
                    break

                for a in actions:
                    key = (a.get("post_id"), a.get("topic_id"), a.get("created_at"), filter_type)
                    if key in seen_keys:
                        continue
                    seen_keys.add(key)
                    a["_filter_type"] = filter_type
                    all_actions.append(a)
                    if len(all_actions) >= limit:
                        break

                offset += len(actions)
                if len(actions) == 0:
                    break

        all_actions.sort(key=lambda x: x.get("created_at") or "", reverse=True)
        return all_actions[:limit]

    def create_topic(self, title: str, raw: str, category_id: int):
        return self.post("/posts.json", data={"title": title, "raw": raw, "category": category_id})

    def reply_topic(self, topic_id: int, raw: str):
        return self.post("/posts.json", data={"topic_id": topic_id, "raw": raw})

    def retort_post(self, post_id: int, emoji: str, remove: bool = False):
        """贴/移除表情"""
        data: Dict[str, Any] = {"emoji": emoji}
        if remove:
            data["remove"] = True
        return self.post(f"/posts/{post_id}/retort", data=data)

    def delete_post(self, post_id: int):
        """删除回复"""
        result = self.post(f"/posts/{post_id}/destroy.json", data={"id": post_id})
        return result

    @staticmethod
    def _handle_response(r: requests.Response):
        if r.status_code in (401, 403):
            raise AuthError(
                f"未登录或无权限，HTTP {r.status_code}。"
                "请重新配置认证（User-Api-Key 或 Cookie）。"
            )
        if r.status_code >= 400:
            raise RuntimeError(f"请求失败 HTTP {r.status_code}: {r.text[:1000]}")

        content_type = r.headers.get("content-type", "")
        if "application/json" in content_type:
            return r.json()
        try:
            return r.json()
        except Exception:
            return r.text