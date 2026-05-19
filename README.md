# Shuiyuan Skills

面向上海交通大学水源社区（`shuiyuan.sjtu.edu.cn`）的 Discourse API 工具集。

本项目把"刷水源"做成可被 Agent 调用的技能：看帖、巡帖、搜索、汇总、导出帖子内容、提取图片/投票/表情信息，并在人工确认后进行单条回复、发帖、删除或贴表情。

> 这里的"刷帖"指浏览、巡查、整理帖子；不指灌水、批量发帖、批量回复或模拟真人活跃。

## 特性

- 不使用 Playwright / Selenium / Chromium 自动化登录
- 支持 User-Api-Key、手动 Cookie、环境变量三种认证方式
- 支持最新帖浏览、持续巡帖、关键词搜索
- 支持导出主题下所有 posts
- 支持提取 post 图片链接
- 支持读取投票信息
- 支持读取 reaction / retort / 表情信息
- 支持用户 posts 导出和 emoji 使用统计
- 支持近半个月招募信息检索
- 支持帖子汇总与回复草稿
- 涉及写操作的脚本默认需要人工确认

## 安全边界

本项目不会也不应当用于：

- 自动灌水
- 批量回复
- 批量发帖
- 自动顶帖
- 自动贴表情
- 绕过验证码、风控、权限或频率限制
- 保存或处理 jAccount 密码
- 抓取无权限访问的内容

允许的写操作仅限用户明确触发的单次操作，例如确认后回复一条帖子、发布一个主题、删除自己的回复，或给某个 post 贴/取消一个表情。

## 安装

```bash
git clone https://github.com/HashBrowns-fries/Shuiyuan_skills.git
cd Shuiyuan_skills

pip install -r requirements.txt
```

如果使用 `uv`：

```bash
uv sync
```

## 认证方式

项目不做 jAccount 用户名密码自动登录。推荐使用 User-Api-Key。

### 方式 A：User-Api-Key，推荐

如果已经有 User-Api-Key：

```bash
python user_api_key.py save --key "YOUR_KEY" --client-id "shuiyuan-agent"
python user_api_key.py test
```

也可以通过环境变量配置：

```bash
export SHUIYUAN_USER_API_KEY="YOUR_KEY"
export SHUIYUAN_USER_API_CLIENT_ID="shuiyuan-agent"
python user_api_key.py test
```

如果需要生成新的 User-Api-Key：

```bash
python generate_api_key.py
```

或使用更细分的授权流程：

```bash
python user_api_key.py auth-url --scopes read write --open-browser
python user_api_key.py decrypt --redirect-url "授权后的完整回跳 URL"
python user_api_key.py test
```

说明：生成或授权 User-Api-Key 时可能需要你手动打开浏览器完成授权，但项目本身不使用浏览器内核模拟登录。

### 方式 B：手动 Cookie

在浏览器中手动登录水源，然后复制请求头中的 Cookie：

```bash
python auth/manual_cookie_auth.py
```

之后再运行任意脚本。

### 方式 C：环境变量

```bash
export SHUIYUAN_BASE_URL="https://shuiyuan.sjtu.edu.cn"
export SHUIYUAN_USER_API_KEY="YOUR_KEY"
export SHUIYUAN_USER_API_CLIENT_ID="shuiyuan-agent"
```

## 快速开始

### 查看登录状态

```bash
python user_api_key.py test
```

### 看最新帖子

```bash
python latest_topics.py
python browse_latest.py --count 10 --unseen-only
```

### 持续巡帖

```bash
python watch_latest.py --interval 300 --count 20
```

### 搜索帖子

```bash
python search_topics.py "招募"
```

### 读取某个帖子

```bash
python read_topic.py 475362
```

### 通用查询与汇总

```bash
python query_summarize.py "招募"
python query_summarize.py 475362
```

## 常用工作流

### 1. 自动看帖 / 巡帖

只读，不发帖、不回复。

```bash
python browse_latest.py --count 20 --unseen-only
python watch_latest.py --interval 300 --count 20
```

按关键词巡帖：

```bash
python watch_latest.py --interval 300 --count 30 --keyword "招募"
```

### 2. 汇总帖子并准备回复

先生成摘要和回复草稿：

```bash
python summarize_reply_confirmed.py 475362 --prepare-reply reply.md
```

编辑 `reply.md` 后，再确认发送：

```bash
python summarize_reply_confirmed.py 475362 --reply-file reply.md --send
```

脚本仍会要求输入确认词，避免误发。

### 3. 导出主题所有 posts

```bash
python get_topic_posts.py 475362 --output topic_475362.json
python get_topic_posts.py 475362 --output topic_475362.csv
python get_topic_posts.py 475362 --output topic_475362.txt
```

### 4. 获取某个 post 的图片

```bash
python get_post_imgs.py --post-id 987654
python get_post_imgs.py --topic-post 475362 1
```

### 5. 获取投票信息

```bash
python get_post_votes.py 475362
```

只会输出 API 正常返回的公开投票信息，不绕过权限。

### 6. 获取 post 的表情 / reaction / retort 信息

```bash
python get_post_retorts.py --post-id 987654 --inspect
```

贴表情前建议先检查字段：

```bash
python get_post_retorts.py --post-id 987654 --inspect
python retort_post.py 987654 heart
```

### 7. 获取某用户 posts

```bash
python get_user_posts.py username --limit 300 --output user_posts.json
```

只看主题：

```bash
python get_user_posts.py username --topics-only --limit 100
```

只看回复：

```bash
python get_user_posts.py username --replies-only --limit 100
```

### 8. 统计 emoji 使用

```bash
python statistic_emoji_usage.py --username username --limit 500
python statistic_emoji_usage.py --topic-id 475362 --limit 500
```

### 9. 获取近半个月招募信息

```bash
python newest_recruit.py --days 15
```

自定义关键词：

```bash
python newest_recruit.py --days 15 --keywords "招募,招新,实习,内推,课题组"
```

### 10. 发布、回复、删除

这些属于写操作，默认需要人工确认。

```bash
python reply_confirmed.py 475362
python create_topic_confirmed.py --title "标题" --category 1 --file post.md
python delete_post.py --post-id 987654
```

## 脚本说明

| 脚本 | 功能 | 类型 |
|---|---|---|
| `latest_topics.py` | 查看最新帖子列表 | 读 |
| `browse_latest.py` | 浏览最新帖子，支持 `--unseen-only` | 读 |
| `watch_latest.py` | 持续巡查新帖子 | 读 |
| `search_topics.py` | 搜索帖子 | 读 |
| `read_topic.py` | 读取帖子内容 | 读 |
| `query_summarize.py` | 通用查询与汇总，支持关键词或 topic id | 读 |
| `get_topic_posts.py` | 导出某主题所有 posts | 读 |
| `get_post_imgs.py` | 获取 post 中的图片链接 | 读 |
| `get_post_votes.py` | 获取主题中的投票信息 | 读 |
| `get_post_retorts.py` | 获取 post 的 reaction / retort / 表情信息 | 读 |
| `get_user_posts.py` | 获取某用户公开 posts | 读 |
| `statistic_emoji_usage.py` | 统计 emoji 使用 | 读 |
| `newest_recruit.py` | 获取招募类帖子 | 读 |
| `list_categories.py` | 查看分类 ID | 读 |
| `summarize_reply_confirmed.py` | 汇总帖子并确认后回复 | 读 / 写 |
| `reply_confirmed.py` | 确认后回复帖子 | 写 |
| `create_topic_confirmed.py` | 确认后发布新帖 | 写 |
| `delete_post.py` | 删除自己的 post | 写 |
| `retort_post.py` | 给 post 贴/取消表情 | 写 |
| `user_api_key.py` | User-Api-Key 管理 | 认证 |
| `generate_api_key.py` | 生成 User-Api-Key | 认证 |

## 环境变量

| 变量 | 默认值 | 说明 |
|---|---|---|
| `SHUIYUAN_BASE_URL` | `https://shuiyuan.sjtu.edu.cn` | 水源站点地址 |
| `SHUIYUAN_USER_API_KEY` | 无 | 直接提供 User-Api-Key |
| `SHUIYUAN_USER_API_CLIENT_ID` | `shuiyuan-agent` | User API Client ID |
| `SHUIYUAN_COOKIE_FILE` | `./shuiyuan_cookies_manual.json` | 手动 Cookie 文件 |
| `SHUIYUAN_USER_API_KEY_FILE` | `./shuiyuan_user_api_key.json` | User-Api-Key 文件 |

## 项目结构

```text
Shuiyuan_skills/
├── auth/
│   ├── manual_cookie_auth.py
│   └── user_api_key_auth.py
├── models/
│   ├── common.py
│   ├── search.py
│   └── topic.py
├── shuiyuan_client.py
├── browse_latest.py
├── watch_latest.py
├── query_summarize.py
├── summarize_reply_confirmed.py
├── get_topic_posts.py
├── get_post_imgs.py
├── get_post_votes.py
├── get_post_retorts.py
├── get_user_posts.py
├── statistic_emoji_usage.py
├── newest_recruit.py
├── reply_confirmed.py
├── create_topic_confirmed.py
├── delete_post.py
├── retort_post.py
├── user_api_key.py
├── generate_api_key.py
├── SKILL.md
├── requirements.txt
└── pyproject.toml
```

## Agent 使用建议

当 Agent 调用本项目时，建议遵循以下规则：

1. 默认只读：优先使用看帖、搜索、汇总、导出脚本。
2. 写操作必须单次触发：不要循环发帖、循环回复、批量贴表情。
3. 写操作前展示内容：回复、发帖、删除、贴表情前应显示目标和内容。
4. 需要用户明确确认：例如输入"确认发送"或"确认贴表情"。
5. 遇到 401 / 403 / 429 时停止，不要高频重试。
6. 不处理 jAccount 密码，不绕过验证码或权限。

## 常见问题

### 这个项目需要浏览器内核吗？

不需要 Playwright / Selenium / Chromium 自动化登录。User-Api-Key 首次授权时可能需要你手动打开浏览器完成授权，但脚本本身通过 `requests` 调用 Discourse API。

### 可以自动回复吗？

不建议，也不作为默认能力。项目支持"汇总 + 生成草稿 + 人工确认后发送单条回复"。

### 可以贴表情吗？

可以。建议先运行：

```bash
python get_post_retorts.py --post-id 987654 --inspect
```

确认字段后再执行：

```bash
python retort_post.py 987654 heart
```

### Cookie / API Key 可以提交到 Git 吗？

不可以。请确保本地密钥文件在 `.gitignore` 中，例如：

```text
shuiyuan_user_api_key.json
shuiyuan_cookies_manual.json
.env
```

## 开发建议

后续可以优先改进：

- 增加统一 CLI：`python sy.py latest / watch / topic / recruit`
- 增加 `config.yaml`
- 增加 SQLite 缓存与历史记录
- 增加请求限速、重试与 429 处理
- 增加 Markdown / CSV / JSON 统一输出格式
- 增加结构化招募信息提取

## 免责声明

本项目仅用于个人学习、信息整理和已授权的社区浏览辅助。使用时请遵守水源社区规则、Discourse API 限制以及学校相关规定。用户应自行承担使用脚本产生的后果。