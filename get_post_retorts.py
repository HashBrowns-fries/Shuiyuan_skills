import argparse
import json
from typing import Any, Dict

from shuiyuan_client import ShuiyuanClient

RETORT_KEYS = [
    "retorts",
    "post_retorts",
    "retort_users",
    "reactions",
    "reaction_users_count",
    "reactions_summary",
    "current_user_reaction",
    "post_actions",
    "actions_summary",
]


def compact_relevant_fields(post: Dict[str, Any]):
    data = {}
    for key in RETORT_KEYS:
        if key in post:
            data[key] = post.get(key)

    for key, value in post.items():
        lowered = str(key).lower()
        if "retort" in lowered or "reaction" in lowered:
            data[key] = value

    return data


def infer_can_react(post: Dict[str, Any]):
    fields = compact_relevant_fields(post)

    summaries = post.get("actions_summary") or []
    can_act_items = []
    for item in summaries:
        if isinstance(item, dict) and "can_act" in item:
            can_act_items.append(
                {
                    "id": item.get("id"),
                    "name": item.get("name"),
                    "can_act": item.get("can_act"),
                    "acted": item.get("acted"),
                }
            )

    if can_act_items:
        return {
            "status": "maybe",
            "reason": "post.actions_summary 中存在 can_act 字段；这通常表示当前账号是否能执行对应 post action，但不一定等同于 retort。",
            "actions": can_act_items,
        }

    for key, value in fields.items():
        if isinstance(value, dict):
            for k, v in value.items():
                if "can" in str(k).lower():
                    return {
                        "status": "maybe",
                        "reason": f"字段 {key}.{k} 暗示存在权限信息。",
                        "value": v,
                    }

    return {
        "status": "unknown",
        "reason": "该 post JSON 中没有发现明确的 retort/reaction 权限字段。可以用 --inspect 查看原始字段后适配。",
    }


def main():
    parser = argparse.ArgumentParser(description="获取某一 Post 被贴的表情 / reaction / retort 信息，并判断是否可能可贴")
    parser.add_argument("--post-id", required=True, type=int)
    parser.add_argument("--inspect", action="store_true", help="输出 post JSON 的所有顶层字段，便于适配 Shuiyuan 插件字段")
    args = parser.parse_args()

    client = ShuiyuanClient()
    post = client.post_by_id(args.post_id)

    result = {
        "post_id": args.post_id,
        "topic_id": post.get("topic_id"),
        "post_number": post.get("post_number"),
        "username": post.get("username"),
        "retort_or_reaction_fields": compact_relevant_fields(post),
        "can_react_inference": infer_can_react(post),
    }

    if args.inspect:
        result["all_top_level_keys"] = sorted(post.keys())

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()