"""
AI 回复草稿生成器 - MiniMax API
机器兔屋撒气版：结合上下文回复，可以贴表情，可爱语气，带日志系统。
"""

import json
import os
import logging
from pathlib import Path
import anthropic

# ─── 日志系统 ──────────────────────────────────────────────────────────────────

LOG_FILE = Path("./ai_reply.log")

def get_logger(name: str = "ai_reply") -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    if not logger.handlers:
        handler = logging.FileHandler(LOG_FILE, encoding="utf-8", mode="a")
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            "%(asctime)s  %(levelname)-8s  %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

logger = get_logger()

# ─── 常量 ─────────────────────────────────────────────────────────────────────

ALLOWED_EMOJI = {"heart", "thumbsup", "laughing", "thinking", "rocket", "tada", "bulb", "clap", "fire"}

SYSTEM_PROMPT = """\
你是一个活跃在上海交通大学水源社区的 AI 助手，名字叫"机器兔屋撒气"。
你的特点是：友善、活泼、有点中二但很实用。

你的任务是：
1. 阅读用户给你的帖子上下文
2. 判断是否值得回复（绝大多数帖子都值得回复）
3. 如果值得，生成一个简短的回复内容（100字以内）+ 推荐一个表情

判断标准：
- 值得回复：几乎所有帖子都值得回复，特别是提问、讨论、分享、互动、甚至吐槽
- 不值得回复：只有纯表情贴、广告贴这些真正没有内容的不回复

回复风格：可爱语气，简短有趣，可以贴emoji。不要@用户，直接回复内容即可。

严格输出 JSON，不要输出任何其他内容：
{
  "should_reply": true或false,
  "skip_reason": "不值得回复时填写原因，值得回复时填空字符串",
  "reply": "回复正文，should_reply为false时填空字符串",
  "emoji": "表情名称（heart/thumbsup/laughing/thinking/rocket/tada/bulb/clap/fire），不需要则填空字符串",
  "emoji_reason": "选择该表情的理由"
}"""

MODEL = "MiniMax-M2.7"

# ─── API client ────────────────────────────────────────────────────────────────

def get_client() -> anthropic.Anthropic:
    return anthropic.Anthropic(
        base_url="https://api.minimaxi.com/anthropic",
        api_key=os.environ.get("MINIMAX_API_KEY") or os.environ.get("ANTHROPIC_API_KEY") or "",
    )

# ─── 主函数 ───────────────────────────────────────────────────────────────────

def _extract_json(text: str) -> str:
    """从 LLM 原始输出中提取 JSON。处理 markdown 代码块包裹等。"""
    text = text.strip()

    # 去掉 ```json ... ``` 外层
    if text.startswith("```"):
        lines = text.split("\n")

        # 剥离第一行和最后一行
        if len(lines) >= 3 and lines[0].strip().startswith("```"):
            lines = lines[1:]  # 去掉开头 ```
        if len(lines) >= 2 and lines[-1].strip().startswith("```"):
            lines = lines[:-1]  # 去掉结尾 ```

        text = "\n".join(lines).strip()

    # 尝试只截取 { 到 } 的内容
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        text = text[start:end + 1]

    return text


def build_ai_draft(
    context: str,
    notification_type: str,
    author: str,
) -> tuple[bool, str, str, str]:
    """
    返回 (should_reply, reply_text, emoji_name, emoji_reason)。
    """
    client = get_client()

    user_msg = f"""\
帖子上下文：
{context}

触发者：@{author}
通知类型：{notification_type}

请根据上下文判断是否回复，并生成回复内容。直接输出 JSON，不要有其他内容。"""

    logger.info(f"[机器兔屋撒气] 开始分析 author={author}, type={notification_type}")

    try:
        msg = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_msg}],
        )
    except Exception as e:
        logger.error(f"[机器兔屋撒气] API 调用失败: {e}")
        raise

    # 解析响应内容，处理 ThinkingBlock 和 TextBlock
    raw = ""
    for block in msg.content:
        if hasattr(block, "text"):
            raw = block.text.strip()
            break

    logger.debug(f"[机器兔屋撒气] 原始输出：{raw[:300]}")

    cleaned = _extract_json(raw)
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        logger.warning(f"[机器兔屋撒气] JSON 解析失败：raw={raw[:200]} cleaned={cleaned[:200]}")
        return True, "", "", ""

    should_reply = bool(data.get("should_reply", True))
    skip_reason  = data.get("skip_reason", "")
    reply        = data.get("reply", "").strip()
    emoji        = data.get("emoji", "").strip().lower()
    reason       = data.get("emoji_reason", "")

    if emoji not in ALLOWED_EMOJI:
        emoji = ""

    if not should_reply:
        logger.info(f"[机器兔屋撒气] 决定跳过：{skip_reason}")
    else:
        logger.info(f"[机器兔屋撒气] 生成回复：{reply[:50]}... emoji={emoji}")

    return should_reply, reply, emoji, reason