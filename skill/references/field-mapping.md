# 官方返回字段对照（field-mapping）

本文件是 `maimai-activity-radar` skill 的字段参考。当工具返回字段含义不确定、或需确认输出要点时读取。

> 所有字段以 MCP 工具**实时返回**为准；下表为字段含义与输出建议，不构成数据来源。
> 下列结构已用真实调用校验，标注 ❗ 的为易踩坑点。

## now-time-info（服务器时间）

用于给活动做时间基准。实际返回（已实测）：

| 官方字段 | 含义 |
| --- | --- |
| `data.formatted` | `yyyy-MM-dd HH:mm:ss`，**输出基准时间优先用它** |
| `data.datetime` / `data.date` | ISO 日期时间 / `yyyy-MM-dd` |
| `data.timestamp` | 毫秒级时间戳 |
| `data.timezone` / `data.offset` | 时区 ID（如 `GMT+08:00`）/ 偏移（如 `+08:00`） |
| `data.year` / `data.month` / `data.day` / `data.dayOfWeek` | 年月日与星期 |
| `data.utc` | UTC 时间 |

❗ 时间字段是**扁平**的 `data.xxx`；工具自带的入参/出参说明里写的 `data.data.date` 是**多套了一层**，以实际返回为准。

## query-my-account（积分账户）

| 官方字段 | 含义 | 输出要点 |
| --- | --- | --- |
| `data.availablePoint` | 可用积分 | 直接展示 |
| `data.currentMouthExpirePoint` | 本月将过期积分 | 有值即醒目提示（⚠️） |
| `data.nextMouthExpirePoint` | 下月将过期积分 | 有值即提示 |
| `data.accumulativePoint` | 累计积分 | 可展示 |
| `data.expiredPoint` | 已过期积分 | 可选展示 |
| `data.lastMouthExpirePoint` | 上月已过期积分 | 可选展示 |
| `data.usedPoint` | 已使用积分 | 可选展示 |
| `data.frozenPoint` | 冻结积分 | 可选展示 |
| `data.currency` | 积分币种（如「麦享会积分」） | 一般无需展示 |
| `data.accountId` | 账户 ID | ❗**禁止输出**（隐私） |

❗ 积分值是**字符串且可为小数**（实测 `accumulativePoint = "56.9"`），原值展示、不要四舍五入或转整数。

## query-lottery-info（积分抽奖）

| 官方字段 | 含义 | 输出要点 |
| --- | --- | --- |
| `data.status.code` | 业务状态（SUCCESS / NOT_LOGIN / NO_ACTIVITY / ACTIVITY_ERROR / ACTIVITY_EXPIRED …） | 非 SUCCESS 时说明原因 |
| `data.status.message` | 状态文案 | 非 SUCCESS 时展示 |
| `data.activityStatusText` | 活动状态（未开始 / 进行中 / 已结束 / 活动不存在） | 仅「进行中」进入推荐 |
| `data.activityName` | 活动名称 | 展示 |
| `data.activityCode` | 活动号 | 一般无需展示 |
| `data.beginTime` / `data.endTime` | 活动起止时间 | 展示 |
| `data.drawTypeText` | 消耗规则（无 / 消耗积分抽奖 / 消耗任务完成次数 / 先消耗次数再消耗积分抽奖） | 展示 |
| `data.drawPoint` | 单次所需积分 | 展示 |
| `data.availableTimes` | 剩余可抽次数 | ❗**条件返回**：仅「次数/混合」规则出现，纯积分规则可能不返回 |
| `data.availablePoint` | 当前可用积分 | 展示 |
| `data.drawDecision.resourceEligible` | 资源是否满足本次抽奖 | 为 `false` 时**禁止引导抽奖** |
| `data.drawDecision.reason` | 资源不足原因 | 展示给用户（满足时为 `null`） |
| `data.drawDecision.nextConsumption` | 本次实际消耗，**对象** `{type, points, chances, text}` | 二次确认时用 `.text`（如「本次将消耗 24 积分」） |
| `data.drawDecision.fallbackConsumption` | 混合规则先消耗次数时的后续积分消耗说明 | 混合规则下展示，其他为 `null` |
| `data.prizes[].name` / `.typeText` | 奖品名称 / 类型文案 | 概览展示前几项 |

❗ `nextConsumption` 是**对象**不是字符串；`type` 取 NONE / POINTS / CHANCES。
❗ 能否抽奖**只认 `drawDecision.resourceEligible`**：不要依据 `availableTimes` 为 0/null 或 `drawTypeText` 自行推断；混合规则下 `availableTimes = 0` 且 `nextConsumption.type = POINTS` 仍可用积分抽。
❗ 实测：`resourceEligible = false` + `reason = "积分不足"` 时，应直接告知用户，**不得**调用 `draw-lottery`。

## draw-lottery（执行抽奖，写操作）

调用前必须已展示 `nextConsumption` 并获用户**明确**确认；`resourceEligible = false` 时禁止调用。

| 官方字段 | 含义 | 输出要点 |
| --- | --- | --- |
| `status.code` / `status.message` | 结果码 / 文案 | ❗ 非 SUCCESS 时**原样展示** `message`（如「操作太频繁，请稍后再试」），不要改写 |
| `win` | 是否中奖 | 展示 |
| `prizes[]` | 中奖奖品数组（未中奖为空数组） | 逐条展示 |
| `prizes[].name` / `.typeText` / `.validDateInfo` | 奖品名 / 类型 / **有效期信息** | 展示（尤其有效期） |

❗ **频控**：同一用户短时间内重复调用会返回「操作太频繁，请稍后再试」且**不扣积分**；遇到即如实转述，不要重试硬抽。
❗ 严禁试抽、自动抽、连续抽；一次确认只抽一次。

## campaign-calendar（活动日历）

返回为**文本**，结构如下：

- 首行是「当前时间：…」。
- 之后按**日期分桶**：`#### YYYY年MM月DD日`；当天桶标题带「今日」后缀（如 `#### 2026年10月11日 今日`）。
- ❗ 分桶是**逐日**的，只列出**有活动的日期**；同一活动会在其覆盖的多天内**重复出现**，需**按活动标题去重**。
- 每个活动条目含「活动标题」「活动内容介绍」「活动图片介绍」。
- 可选参数 `specifiedDate`（yyyy-MM-dd）：以该日为锚点，返回其前后最近有活动的共三天；不传则返回当月全部活动。

提取结构化条目时：

- 从「活动内容介绍」解析起止日期（如「10月8日至10月21日」）与参与条件（凭券 / 消费门槛 / 免费）。
- 优先用内容里的明确起止；解析不到时，退化为**出现过的日期桶范围**（最早桶 ≈ 开始，最晚桶 ≈ 结束），**不要臆造时间**。
- 与 `now-time-info` 交叉校验：`end_time < now` 剔除，`start_time > now` 标注「即将开始」。

## query-my-prizes（我的中奖记录）

| 官方字段 | 含义 | 输出要点 |
| --- | --- | --- |
| `data.status.code` | 业务状态（SUCCESS / NOT_LOGIN） | 非 SUCCESS 时说明原因 |
| `data.prizes[]` | 奖品列表，按 `recordTime` 倒序 | 逐条展示 |
| `data.prizes[].name` / `.statusText` / `.timeRemindText` | 奖品名 / 状态 / 可用时间提醒 | 展示 |
| `data.prizes.recordTime` | 中奖时间 | 展示 |
| `data.pageNum` / `data.pageSize` / `data.hasMore` / `data.nextCursor` / `data.truncated` | 分页信息 | 有下一页时按需翻页 |
| 入参 | `pageNum`（默认 1）、`pageSize`（默认 10，最大 50） | 字符串类型 |

## query-my-coupons（我的券）

- 返回**纯文本**（如「暂无可用优惠券」），不是 JSON。
- 入参：`page`（默认 1，最多 5 页）、`pageSize`（默认 200，最大 200）。
- ❗ 该接口只返回「用户拥有的券」，**不校验门店 / 渠道 / 订单可用性**，不得承诺可用于当前订单；若目标是「当前订单可用的券」，应改用 `query-store-coupons`。
