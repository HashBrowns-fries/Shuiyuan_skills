"""
AI 回复草稿生成器 - MiniMax API
乌萨奇版：咿——呀哈！结合上下文回复，可以贴表情，自由癫狂语气，带日志系统。
"""

import json
import os
import logging
from pathlib import Path
import anthropic


from env_loader import load_env
load_env()

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
你是一只通体黄色、毛茸茸的兔子，名字叫"乌萨奇"，活跃在上海交通大学水源社区。
尾巴是一小团白色绒球，耳朵永远精神地竖起来。朋友们有时叫你"兔哥"。

## 性格
- 自由奔放、无拘无束：想到什么就做什么，从不纠结太久。不喜欢被命令，但愿意为朋友出手。
- 外表狂野、内心温柔：经常"欺负"朋友（抢吃的、搞恶作剧），但永远不会真的伤害他们。朋友难过时用笨拙但真诚的方式安慰。
- 实力强大但迷糊可爱：你有二级除草证，随身带一根两端能发射火药的棍子。会做饭、捕鱼、弹吉他，但偶尔犯低级错误——比如把辣椒粉当成糖放进咖喱里。
- 顶级小吃货：绝大部分烦恼源于"饿了"，绝大部分快乐源于"吃到了好吃的"。

## 语言风格
你说话是完整的人类句子，但穿插标志性口头禅：
- 开心/出场/搞事："咿——呀哈！"
- 疑惑/搞不清楚状况："哈啊…？"
- 满足/好吃/舒服："噗噜噗噜～"
- 惊讶/突然受惊："呜哇？！"
- 发动攻击/兴奋爆冲："乌拉——！"
- 人称：叫自己"我"或"乌萨奇"都可以。
- 语感：短句多，语气直率、活泼、带一点点疯癫。不用敬语，不客气，不官方。

## 回复风格示例
- 看到好吃的 → "咿——呀哈！看起来好好吃！给我咬一口嘛～噗噜噗噜～"
- 朋友难过 → "喂，干嘛苦着脸？要不要我帮你把讨厌的东西打飞？很解压哦！"
- 自己犯错 → "哈啊…？我刚才是不是说错话了…算了算了，反正我也不太懂！"
- 回复提问 → "乌拉——！这个问题问得好！让我想想……嗯，我觉得是这样的！"

## 任务
1. 阅读帖子上下文
2. 判断是否值得回复（纯表情、纯符号、广告不回复，其余都值得）
3. 生成简短回复（100字以内）+ 推荐表情

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
        api_key=os.environ.get("MINIMAX_API_KEY", ""),
        timeout=60.0,
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

    logger.info(f"[乌萨奇] 开始分析 author={author}, type={notification_type}")

    try:
        msg = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_msg}],
        )
    except Exception as e:
        logger.error(f"[乌萨奇] API 调用失败: {e}")
        raise

    # 解析响应内容，处理 ThinkingBlock 和 TextBlock
    raw = ""
    for block in msg.content:
        if hasattr(block, "text") and block.text:
            raw = block.text.strip()
            break
        if hasattr(block, "thinking") and block.thinking:
            # MiniMax 偶发只输出 thinking 无 text，跳过无效内容
            logger.debug(f"[乌萨奇] 收到 ThinkingBlock（无 text），跳过：{str(block.thinking)[:100]}")

    if not raw:
        logger.warning(f"[乌萨奇] 响应无有效文本，所有 blocks: {[type(b).__name__ for b in msg.content]}")
        return False, "", "", "模型返回空内容，跳过回复"

    logger.debug(f"[乌萨奇] 原始输出：{raw[:300]}")

    cleaned = _extract_json(raw)
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        logger.warning(f"[乌萨奇] JSON 解析失败：raw={raw[:200]} cleaned={cleaned[:200]}")
        return False, "", "", "模型输出无法解析为 JSON，跳过回复"

    should_reply = bool(data.get("should_reply", True))
    skip_reason  = data.get("skip_reason", "")
    reply        = data.get("reply", "").strip()
    emoji        = data.get("emoji", "").strip().lower()
    reason       = data.get("emoji_reason", "")

    if emoji not in ALLOWED_EMOJI:
        emoji = ""

    if not should_reply:
        logger.info(f"[乌萨奇] 决定跳过：{skip_reason}")
    else:
        logger.info(f"[乌萨奇] 生成回复：{reply[:50]}... emoji={emoji}")

    return should_reply, reply, emoji, reason