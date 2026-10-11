# -*- coding: utf-8 -*-
"""麦麦活动雷达助手 —— 本地计算模块单元测试（无第三方依赖）。"""

import sys
import unittest
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from mai_radar import (  # noqa: E402
    build_report,
    classify_activity,
    filter_active,
    format_points,
    match_tags,
    parse_datetime,
)

NOW = datetime(2026, 10, 11, 12, 0, 0)

ACT_RUNNING = {
    "id": "A001",
    "title": "麦麦学生早餐特惠",
    "start_time": "2026-10-01",
    "end_time": "2026-10-31",
    "description": "工作日早餐时段优惠",
    "condition": "学生身份凭证 / 工作日 6:00-10:30",
    "tags": ["学生", "早餐"],
}

ACT_UPCOMING = {
    "id": "A002",
    "title": "新品上市尝鲜周",
    "start_time": "2026-10-13",
    "end_time": "2026-10-19",
    "description": "新品免费试吃",
    "condition": "无消费门槛",
    "tags": ["新品"],
}

ACT_ENDED = {
    "id": "A003",
    "title": "麦麦夜市专属优惠",
    "start_time": "2026-09-20",
    "end_time": "2026-09-30",
    "description": "已结束活动",
    "condition": "20:00 后",
    "tags": ["夜间"],
}

ACT_DESSERT = {
    "id": "A004",
    "title": "甜品站第二份半价",
    "start_time": "2026-10-08",
    "end_time": "2026-10-20",
    "description": "指定冰淇淋、派类第二份半价",
    "condition": "无消费门槛",
    "tags": ["甜品"],
}

# 字段名与官方 query-my-account 返回对齐
ACCOUNT = {
    "available_point": "2850",
    "total_points": "12000",
    "frozen_points": "0",
    "expiring_this_month": "200",
    "expiring_next_month": "0",
    "expired_points": "0",
}

# 字段名与官方 query-lottery-info 返回对齐
LOTTERY = {
    "activity_name": "麦麦积分抽奖",
    "activity_status_text": "进行中",
    "draw_type_text": "消耗积分抽奖",
    "draw_point": "24",
    "available_times": 10,
    "available_point": "2850",
    "resource_eligible": True,
    "reason": None,
    "prizes": [
        {"name": "下单立减3元券", "typeText": "优惠券"},
        {"name": "下单立减2元券", "typeText": "优惠券"},
    ],
}


class TestParseDatetime(unittest.TestCase):
    def test_datetime_format(self):
        self.assertEqual(
            parse_datetime("2026-10-11 12:00:00"), datetime(2026, 10, 11, 12, 0, 0)
        )

    def test_date_only_format(self):
        self.assertEqual(parse_datetime("2026-10-11"), datetime(2026, 10, 11, 0, 0, 0))

    def test_invalid_raises(self):
        with self.assertRaises(ValueError):
            parse_datetime("not-a-date")


class TestClassifyActivity(unittest.TestCase):
    def test_running(self):
        self.assertEqual(classify_activity(ACT_RUNNING, NOW), "进行中")

    def test_upcoming(self):
        self.assertEqual(classify_activity(ACT_UPCOMING, NOW), "即将开始")

    def test_ended(self):
        self.assertEqual(classify_activity(ACT_ENDED, NOW), "已结束")


class TestFilterActive(unittest.TestCase):
    def test_removes_ended_and_sorts(self):
        # 按结束时间升序：A002 结束 10-19 早于 A004 结束 10-20
        result = filter_active([ACT_ENDED, ACT_DESSERT, ACT_UPCOMING], NOW)
        statuses = [st for st, _ in result]
        self.assertEqual(statuses, ["即将开始", "进行中"])
        self.assertEqual([act["id"] for _, act in result], ["A002", "A004"])

    def test_all_ended_returns_empty(self):
        self.assertEqual(filter_active([ACT_ENDED], NOW), [])


class TestMatchTags(unittest.TestCase):
    def test_no_tags_matches_all(self):
        self.assertTrue(match_tags(ACT_RUNNING, []))

    def test_tag_set_intersection(self):
        self.assertTrue(match_tags(ACT_RUNNING, ["学生"]))
        self.assertFalse(match_tags(ACT_RUNNING, ["甜品"]))

    def test_keyword_in_text(self):
        self.assertTrue(match_tags(ACT_DESSERT, ["冰淇淋"]))

    def test_free_condition_semantic(self):
        self.assertTrue(match_tags(ACT_UPCOMING, ["只看免消费活动"]))
        self.assertFalse(match_tags(ACT_RUNNING, ["只看免消费活动"]))

    def test_student_semantic(self):
        self.assertTrue(match_tags(ACT_RUNNING, ["学生党"]))


class TestFormatPoints(unittest.TestCase):
    def test_with_expiring(self):
        text = format_points(ACCOUNT)
        self.assertIn("2,850", text)
        self.assertIn("200", text)
        self.assertIn("本月将过期", text)

    def test_without_expiring(self):
        text = format_points(
            {
                "available_point": "100",
                "expiring_this_month": "0",
                "expiring_next_month": "0",
            }
        )
        self.assertIn("100", text)
        self.assertNotIn("将过期", text)


class TestBuildReport(unittest.TestCase):
    def test_full_report_sections(self):
        report = build_report(
            [ACT_RUNNING, ACT_UPCOMING, ACT_ENDED, ACT_DESSERT],
            ACCOUNT,
            LOTTERY,
            NOW,
            tags=["学生", "甜品"],
        )
        self.assertIn("活动雷达", report)
        self.assertIn("积分状态", report)
        self.assertIn("可参与积分抽奖", report)
        self.assertIn("麦麦学生早餐特惠", report)  # 学生标签命中
        self.assertIn("甜品站第二份半价", report)  # 甜品标签命中
        self.assertNotIn("麦麦夜市专属优惠", report)  # 已结束剔除
        self.assertIn("即将开始", report)  # 即将开始活动保留并标注

    def test_lottery_insufficient_points_hint(self):
        lottery_no_points = dict(LOTTERY, resource_eligible=False, reason="积分不足")
        report = build_report([ACT_RUNNING], ACCOUNT, lottery_no_points, NOW)
        self.assertIn("无法抽奖", report)
        self.assertIn("积分不足", report)
        self.assertNotIn("帮我抽一次", report)

    def test_no_match_message(self):
        report = build_report([ACT_RUNNING], ACCOUNT, LOTTERY, NOW, tags=["宠物"])
        self.assertIn("没有匹配到活动", report)

    def test_official_field_names_accepted(self):
        """模拟数据使用官方 camelCase 字段名时，报告仍能正确生成。"""
        account_official = {
            "availablePoint": "2850",
            "accumulativePoint": "12000",
            "frozenPoint": "0",
            "currentMouthExpirePoint": "200",
            "nextMouthExpirePoint": "0",
            "expiredPoint": "0",
        }
        lottery_official = {
            "activityName": "麦麦积分抽奖",
            "activityStatusText": "进行中",
            "drawTypeText": "消耗积分抽奖",
            "drawPoint": "24",
            "availableTimes": 10,
            "availablePoint": "2850",
            "drawDecision": {
                "resourceEligible": True,
                "reason": None,
                "nextConsumption": {"type": "POINTS", "points": "24"},
            },
            "prizes": [{"name": "下单立减3元券", "typeText": "优惠券"}],
        }
        report = build_report([ACT_DESSERT], account_official, lottery_official, NOW)
        self.assertIn("2,850", report)
        self.assertIn("200", report)
        self.assertIn("单次消耗：24 积分", report)
        self.assertIn("下单立减3元券", report)
        self.assertIn("帮我抽一次", report)


if __name__ == "__main__":
    unittest.main(verbosity=2)
