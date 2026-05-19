# 登录水源

**不推荐使用浏览器登录**，推荐使用 User-Api-Key 或手动 Cookie。

## 方式 A：User-Api-Key（推荐）

```bash
# 如果已有 key
python auth/user_api_key_auth.py

# 如果需要生成新 key
python generate_api_key.py
```

## 方式 B：手动 Cookie

```bash
python auth/manual_cookie_auth.py
```

步骤：
1. 在浏览器登录水源
2. 打开开发者工具（F12）→ Network → 找到任意请求 → 复制 Cookie 请求头
3. 运行脚本粘贴

## 验证登录

```bash
cd D:\Water\shuiyuan_agent
python list_categories.py
```

成功则显示分类列表。