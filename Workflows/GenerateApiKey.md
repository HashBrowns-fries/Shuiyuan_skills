# 生成 API Key

生成 User-Api-Key 用于编程访问。

## Input

- 应用名称（可选，默认 ShuiyuanAssistant）
- 权限范围（可选，默认 read, write, notifications, session_info）

## Implementation

1. 生成 RSA-4096 密钥对
2. 打开浏览器授权页面
3. 用户在浏览器完成授权并复制 payload
4. 使用私钥解密 payload 获取 API Key

## Script

参考：`D:\Water\shuiyuan_agent\generate_api_key.py`

```bash
cd D:\Water\shuiyuan_agent
python generate_api_key.py
```

## Usage

```python
from shuiyuan_client import ShuiyuanClient

client = ShuiyuanClient(user_api_key="your-api-key")
```