# -*- coding: utf-8 -*-
"""
麦麦活动雷达助手 —— 本地计算模块（Skill 的辅助逻辑）

设计原则：
  - MCP 只负责提供真实数据（活动日历 / 积分 / 抽奖 / 时间），本模块只做
    「时间过滤 + 标签匹配 + 报告排版」等确定性计算，离线可验证。
  - 仅依赖 Python 标准库，无第三方依赖，可直接 `python src/mai_radar.py` 以
    模拟数据演示完整流程。
  - 字段名与麦当劳官方 MCP 返回结构对齐（见各函数 docstring 的映射说明）。

字段映射说明（官方返回 → 本模块归一化字段，两者均可直接传入，函数自动识别）：
  - query-my-account: availablePoint↔available_point, accumulativePoint↔total_points,
    frozenPoint↔frozen_points, currentMouthExpirePoint↔expiring_this_month,
    nextMouthExpirePoint↔expiring_next_month, expiredPoint↔expired_points
  - query-lottery-info: activityName↔activity_name, drawPoint↔draw_point,
    drawTypeText↔draw_type_text, availableTimes↔available_times,
    availablePoint↔available_point, drawDecision.resourceEligible↔resource_eligible,
    drawDecision.reason↔reason, prizes[].name↔prizes[].name
  - campaign-calendar：官方返回为按日期分组的活动文本，由 Skill 层提取为
    结构化活动条目后，再交给本模块做过滤与排版。
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def _pick(mapping: Dict[str, Any], *names: str) -> Any:
    """按优先级取第一个存在的字段（支持官方 camelCase 与归一化 snake_case）。"""
    for name in names:
        if name in mapping and mapping[name] is not None:
            return mapping[name]
    return None

# ---------------------------------------------------------------------------
# 数据结构约定（Skill 层从官方返回中提取/归一化后的形态）
# ---------------------------------------------------------------------------
# activity = {
#     "id": str,
#     "title": str,
#     "start_time": "YYYY-MM-DD" 或 "YYYY-MM-DD HH:MM:SS",
#     "end_time":  同上,
#     "description": str,
#     "condition": str,          # 参与门槛，如 "学生身份凭证 / 工作日 6:00-10:30"
#     "tags": [str, ...],        # 如 ["学生", "早餐"]，可为空
# }
#
# account = {
#     "available_point": str/int,        # data.availablePoint 可用积分
#     "total_points": str/int,           # data.accumulativePoint 累计积分
#     "frozen_points": str/int,          # data.frozenPoint 冻结积分
#     "expiring_this_month": str/int,    # data.currentMouthExpirePoint 本月将过期
#     "expiring_next_month": str/int,    # data.nextMouthExpirePoint 下月将过期
#     "expired_points": str/int,         # data.expiredPoint 已过期
# }
#
# lottery = {
#     "activity_name": str,              # data.activityName
#     "activity_status_text": str,       # data.activityStatusText 未开始/进行中/已结束
#     "draw_type_text": str,             # data.drawTypeText 消耗规则文案
#     "draw_point": str/int,             # data.drawPoint 单次所需积分
#     "available_times": int,            # data.availableTimes 剩余可抽次数
#     "available_point": str/int,        # data.availablePoint 当前可用积分
#     "resource_eligible": bool,         # data.drawDecision.resourceEligible
#     "reason": Optional[str],           # data.drawDecision.reason 资源不足原因
#     "prizes": [{"name": str}, ...],    # data.prizes[].name
# }

DATE_FORMATS = ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d")
# 「只看免消费活动」等语义标签对应的参与条件关键词
FREE_CONDITION_KEYWORDS = ("无消费门槛", "免费", "无门槛", "不消费", "0元")


def parse_datetime(value: str) -> datetime:
    """解析活动起止时间。"""
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(value.strip(), fmt)
        except ValueError:
            continue
    raise ValueError(f"无法解析时间字段: {value!r}")


def classify_activity(activity: Dict[str, Any], now: datetime) -> str:
    """返回活动状态：进行中 / 即将开始 / 已结束。"""
    start = parse_datetime(activity["start_time"])
    end = parse_datetime(activity["end_time"])
    if end < now:
        return "已结束"
    if start > now:
        return "即将开始"
    return "进行中"


def filter_active(
    activities: List[Dict[str, Any]], now: datetime
) -> List[Tuple[str, Dict[str, Any]]]:
    """剔除已结束活动，返回 [(状态, 活动), ...]，按结束时间升序。"""
    result = []
    for act in activities:
        status = classify_activity(act, now)
        if status != "已结束":
            result.append((status, act))
    result.sort(key=lambda item: parse_datetime(item[1]["end_time"]))
    return result


def match_tags(activity: Dict[str, Any], tags: List[str]) -> bool:
    """
    判断活动是否命中用户标签。
    规则：
      1) 用户标签与活动 tags 集合有交集 → 命中；
      2) 用户标签出现在 title / description / condition 中（子串匹配，忽略大小写）→ 命中；
      3) 语义标签：「免消费」类标签匹配无消费门槛的活动；「学生」匹配含学生的参与条件。
    """
    if not tags:
        return True

    title_desc = (
        f"{activity.get('title', '')} {activity.get('description', '')} "
        f"{activity.get('condition', '')}"
    )
    act_tags = [str(t).lower() for t in activity.get("tags", [])]

    for tag in tags:
        t = tag.strip().lower()
        if not t:
            continue
        # 语义标签优先判断
        if "免消费" in tag or "免费" in tag or "不花钱" in tag:
            if any(k in activity.get("condition", "") for k in FREE_CONDITION_KEYWORDS):
                return True
            continue
        if "学生" in tag and "学生" in activity.get("condition", ""):
            return True
        # 常规匹配：标签集合 或 文本子串
        if t in act_tags or t in title_desc.lower():
            return True
    return False


def _fmt_date(value: str) -> str:
    """把 'YYYY-MM-DD HH:MM:SS' 缩略为 'M月D日'，便于报告展示。"""
    dt = parse_datetime(value)
    return f"{dt.month}月{dt.day}日"


def format_points(account: Dict[str, Any]) -> str:
    """格式化积分状态（兼容 query-my-account 官方字段名）。"""
    available = int(float(_pick(account, "available_point", "availablePoint") or 0))
    exp_this = int(float(_pick(account, "expiring_this_month", "currentMouthExpirePoint") or 0))
    exp_next = int(float(_pick(account, "expiring_next_month", "nextMouthExpirePoint") or 0))
    lines = [f"可用积分：{available:,} 分"]
    if exp_this > 0:
        lines.append(f"本月将过期：{exp_this:,} 分（记得用掉！⚠️）")
    if exp_next > 0:
        lines.append(f"下月将过期：{exp_next:,} 分")
    return "\n".join(lines)


def _lottery_decision(lottery: Dict[str, Any], key: str) -> Any:
    """读取抽奖资源决策字段（支持 drawDecision 嵌套结构与归一化扁平字段）。"""
    direct = _pick(lottery, key)
    if direct is not None:
        return direct
    decision = lottery.get("drawDecision")
    if isinstance(decision, dict):
        mapping = {
            "resource_eligible": "resourceEligible",
            "reason": "reason",
        }
        return decision.get(mapping.get(key, key))
    return None


def format_lottery(lottery: Dict[str, Any]) -> str:
    """格式化抽奖信息（兼容 query-lottery-info 官方字段名）。"""
    name = _pick(lottery, "activity_name", "activityName") or "积分抽奖"
    lines = [f"活动：{name}"]
    draw_type = str(_pick(lottery, "draw_type_text", "drawTypeText") or "")
    draw_point = _pick(lottery, "draw_point", "drawPoint")
    if "积分" in draw_type and draw_point is not None:
        lines.append(f"单次消耗：{draw_point} 积分")
    times = _pick(lottery, "available_times", "availableTimes")
    if times is not None:
        lines.append(f"剩余可抽：{times} 次")
    prizes = _pick(lottery, "prizes") or []
    if prizes:
        names = "、".join(p.get("name", "") for p in prizes[:6])
        lines.append(f"奖品概览：{names}……")
    eligible = _lottery_decision(lottery, "resource_eligible")
    if eligible is False:
        reason = _lottery_decision(lottery, "reason")
        lines.append(f"⚠️ 当前无法抽奖：{reason or '资源不足'}")
    return "\n".join(lines)


def build_report(
    activities: List[Dict[str, Any]],
    account: Dict[str, Any],
    lottery: Dict[str, Any],
    now: datetime,
    tags: Optional[List[str]] = None,
) -> str:
    """生成完整的「活动雷达报告」。"""
    tags = tags or []
    active = filter_active(activities, now)
    matched = [(st, act) for st, act in active if match_tags(act, tags)]

    lines: List[str] = []
    lines.append("📡 活动雷达（进行中 / 即将开始）")
    if not matched:
        lines.append("（没有匹配到活动，试试放宽标签，或稍后再来看～）")
    for idx, (status, act) in enumerate(matched, 1):
        lines.append(
            f"{idx}. [{status}] {act['title']}\n"
            f"   时间：{_fmt_date(act['start_time'])} – {_fmt_date(act['end_time'])}\n"
            f"   参与门槛：{act.get('condition', '无')}\n"
            f"   标签：{' / '.join(act.get('tags', [])) or '—'}"
        )

    lines.append("")
    lines.append("💰 积分状态")
    lines.append(format_points(account))

    status_text = _pick(lottery, "activity_status_text", "activityStatusText")
    if status_text == "进行中":
        lines.append("")
        lines.append("🎰 可参与积分抽奖")
        lines.append(format_lottery(lottery))
        if _lottery_decision(lottery, "resource_eligible") is not False:
            lines.append("如需抽奖，直接告诉我「帮我抽一次」。")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 演示入口（使用 examples/mock-data 下的模拟数据）
# ---------------------------------------------------------------------------
def _load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="麦麦活动雷达助手（模拟数据演示）")
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "examples" / "mock-data",
        help="模拟数据目录（包含 campaign-calendar.json 等）",
    )
    parser.add_argument(
        "--tags",
        nargs="*",
        default=["学生", "甜品", "积分抽奖"],
        help="用户偏好标签，例如：学生 甜品 积分抽奖",
    )
    args = parser.parse_args(argv)

    calendar = _load_json(args.data_dir / "campaign-calendar.json")
    account = _load_json(args.data_dir / "query-my-account.json")["account"]
    lottery = _load_json(args.data_dir / "query-lottery-info.json")["lottery"]
    # 模拟数据中 now 以 now-time-info 返回为准；演示时固定为示例时间
    now = parse_datetime(calendar["_now"])

    print(build_report(calendar["activities"], account, lottery, now, args.tags))
    return 0


if __name__ == "__main__":
    sys.exit(main())
