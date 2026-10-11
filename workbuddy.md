# 开发实录 · maimai-activity-radar（麦麦活动雷达助手）

> 本文档完整记录「麦麦活动雷达助手」skill 从需求到交付的全过程：方案讨论、连接器排查、真实工具联调、问题与修正、最终 Skill 说明。
>
> - 会话时间：2026-10-11 17:16 – 17:38（GMT+8）
> - 技能位置：`C:\Users\hp\.workbuddy\skills\maimai-activity-radar\`
> - 依赖连接器：`mcd-mcp`
> - 交付结论：**核心链路已跑通、可交付**；1 条写操作路径（真实抽奖）因账号积分不足未能实测，其硬性前置条件已在文档中固化。

---

## 目录

1. [需求与方案讨论](#1-需求与方案讨论)
2. [mcd-mcp 连接器配置过程](#2-mcd-mcp-连接器配置过程)
3. [真实工具联调过程](#3-真实工具联调过程)
4. [遇到的问题与修正](#4-遇到的问题与修正)
5. [最终 SKILL.md 说明](#5-最终-skillmd-说明)
6. [未验证项与后续计划](#6-未验证项与后续计划)
7. [安全与脱敏声明](#7-安全与脱敏声明)
8. [附录 A：SKILL.md 全文](#附录-askillmd-全文)
9. [附录 B：references/field-mapping.md 全文](#附录-breferencesfield-mappingmd-全文)

---

## 1. 需求与方案讨论

### 1.1 原始需求

用户希望创建一个专注于**麦当劳（MaiMai）活动 / 积分 / 抽奖**领域的 MCP Skill，核心诉求：

- 把分散的「官方活动日历 + 用户积分 + 积分抽奖」三类数据聚合，按用户偏好标签筛选；
- 让用户一眼看清「现在有什么活动值得参加、我的积分能干什么」；
- 在用户**二次确认后**代为执行抽奖；
- 明确边界：**不点餐、不下单、不结算、不领券**；
- 强约束：数据必须全部来自 MCP 实时返回，不得编造；不得泄露凭据；不得越界操作。

### 1.2 方案讨论与关键决策

| 决策点                      | 结论                                                         | 理由                                                  |
| ------------------------ | ---------------------------------------------------------- | --------------------------------------------------- |
| Skill 结构模式               | **Workflow-Based（流程式）**                                    | 需求本身是「聚合 → 过滤 → 筛选 → 输出 → 交互」的顺序流程，天然适合 Step 1–5    |
| 安装范围                     | **用户级**（`~/.workbuddy/skills/`）                            | 依赖个人麦当劳账号的 mcd-mcp 连接器，属个人工作流，跨项目可用                 |
| 内容拆分                     | SKILL.md 只留流程与规范；**字段对照表拆到 `references/field-mapping.md`** | 遵循渐进式披露（Progressive Disclosure），保持 SKILL.md 精简、按需加载 |
| 是否加 `scripts/`、`assets/` | **不加**                                                     | 本 skill 主要是编排 MCP 工具调用与文本组织，无需可执行脚本或输出模板            |
| 命名                       | `maimai-activity-radar`                                    | 全小写 + 连字符，符合 skill 命名规范，`init_skill.py` 校验通过        |
| frontmatter              | 含 `name` / `description` / **`agent_created: true`**       | 规范要求，便于后续技能管理                                       |

方案确认后，用 skill-creator 的 `init_skill.py` 生成骨架，再填充内容、删除模板示例文件、校验并打包。

---

## 2. mcd-mcp 连接器配置过程

> **重要说明**：本次会话中，**没有实际写入或修改任何连接器配置文件**（如 `~/.workbuddy/mcp.json`）。实际发生的是「状态排查 + 可用性验证」。以下如涉及 Token 示例，一律使用占位符 `YOUR_MCP_TOKEN`。

### 2.1 实际发生的过程

1. **先查连接器列表**：调用 `list_installed_plugins`，返回：
   ```
   No connectors installed.
   If the task needs an external service, use search_plugins to find an installable connector.
   ```
2. **再直接试调工具**：加载 `mcd-mcp` 的 `now-time-info` 并实际调用，返回成功：
   ```json
   {"success":true,"code":200,"message":"请求成功",
    "datetime":"2026-10-11 17:24:05",
    "data":{"timestamp":1791710645613,"formatted":"2026-10-11 17:24:05",
            "timezone":"GMT+08:00","offset":"+08:00"}}
   ```
3. **结论**：虽然列表 API 报告「未安装任何连接器」，但 `mcd-mcp` 工具**实际可正常调用**。

### 2.2 由此得出的判断规则（重要）

> **连接器是否可用，应以「实际工具调用结果」为准，而不是仅凭 `list_installed_plugins` 的输出判断。**

可能原因：`mcd-mcp` 属内置/预置连接器，不在该列表 API 的统计范围内。若遇到列表为空但工具名可见的情况，先试调一次即可确认。

### 2.3 通用配置方法（如需自行配置）

若在新环境中需要从零配置，一般流程如下（**示例，务必替换为真实值，切勿写入文档或提交到仓库**）：

1. 在连接器市场安装 `mcd-mcp`；
2. 在 `~/.workbuddy/mcp.json` 的 `mcpServers` 中登记该服务，Token 形如：
   ```json
   {
     "mcpServers": {
       "mcd-mcp": {
         "url": "https://<mcd-mcp-endpoint>/mcp",
         "headers": {
           "Authorization": "Bearer YOUR_MCP_TOKEN"
         }
       }
     }
   }
   ```
3. 在客户端「连接器」入口对该服务点击**信任 / 启用**（新写入的 MCP 不会自动生效）；
4. 用 `now-time-info` 试调一次验证连通性。

> 本 skill 的 `SKILL.md` 明确声明「不负责配置连接器」，仅提示用户在连接器中启用 `mcd-mcp`。

---

## 3. 真实工具联调过程

本次共触及 **7 个** `mcd-mcp` 工具：**6 个只读工具已实测通过**，**1 个写操作（`draw-lottery`）按规则未执行**。

### 3.1 覆盖矩阵

| # | 工具                   | 类型    | 实测        | 结果摘要                             |
| - | -------------------- | ----- | --------- | -------------------------------- |
| 1 | `now-time-info`      | 读     | ✅         | 服务器时间 2026-10-11 17:24，GMT+08:00 |
| 2 | `campaign-calendar`  | 读     | ✅         | 逐日分桶文本，含 10/11–10/30 活动          |
| 3 | `query-my-account`   | 读     | ✅         | 可用 0 / 累计 56.9 / 已过期 56.9        |
| 4 | `query-lottery-info` | 读     | ✅         | 麦麦积分抽奖，进行中，24 分/次，资源不足           |
| 5 | `query-my-prizes`    | 读     | ✅         | 空列表（无中奖记录）                       |
| 6 | `query-my-coupons`   | 读     | ✅         | 纯文本「暂无可用优惠券」                     |
| 7 | `draw-lottery`       | **写** | ⛔ **未执行** | 资源不足 + 写操作需用户明确确认                |

### 3.2 逐工具联调记录

#### ① now-time-info —— 时间基准

- 调用：无入参。
- 真实返回（节选）：
  ```json
  {"success":true,"code":200,"datetime":"2026-10-11 17:24:05",
   "data":{"timestamp":1791710645613,"datetime":"2026-10-11T17:24:05.613",
           "formatted":"2026-10-11 17:24:05","date":"2026-10-11",
           "year":2026,"month":10,"day":11,"dayOfWeek":"SUNDAY",
           "timezone":"GMT+08:00","offset":"+08:00","utc":"2026-10-11T09:24:05.613Z"}}
  ```
- **发现**：工具自带说明里写的字段路径是 `data.data.date`（多套了一层），**实际是扁平的 `data.date`**。以实际返回为准。

#### ② campaign-calendar —— 活动日历

- 调用：无入参，返回当月活动。
- 真实返回为**文本**，结构（节选）：
  ```
  ### 当前时间：2026-10-11 17:24:14
  ### 活动列表：

  #### 2026年10月11日 今日
  - **活动标题**：超值𝟗.𝟗元早餐两件套陪你开工啦😋
    **活动内容介绍**：…𝟏𝟎月𝟖日至𝟏𝟎月𝟐𝟏日…凭券两件套只要9.9元…
    **活动图片介绍**：<img src="https://cms-cdn.mcd.cn/…">

  #### 2026年10月12日
  - **活动标题**：超值𝟗.𝟗元早餐两件套陪你开工啦😋   ← 同一活动再次出现
  …
  ```
- **发现**：
  - 实际是**逐日分桶**（`#### YYYY年MM月DD日`，当天带「今日」后缀），**并非**规格设想的「今日/进行中/未来/往期」四分组；
  - **同一活动跨界会在多天重复出现**，必须按标题去重；
  - 起止日期需从「活动内容介绍」中解析（如「10月8日至10月21日」）。

#### ③ query-my-account —— 积分账户

- 真实返回（节选，**accountId 已脱敏**）：
  ```json
  {"success":true,"code":200,
   "data":{"availablePoint":"0","accountId":"<已脱敏>",
           "accumulativePoint":"56.9","currency":"麦享会积分",
           "currentMouthExpirePoint":"0","expiredPoint":"56.9",
           "frozenPoint":"0","lastMouthExpirePoint":"0",
           "nextMouthExpirePoint":"0","usedPoint":"0"}}
  ```
- **发现**：
  - 积分值是**字符串且可为小数**（`56.9`），原值展示，不可四舍五入；
  - 字段比规格更全：多出 `lastMouthExpirePoint`、`usedPoint`、`currency`；
  - `accountId` 属个人敏感信息，**禁止输出**。

#### ④ query-lottery-info —— 积分抽奖

- 真实返回（节选）：
  ```json
  {"success":true,"code":200,
   "data":{"status":{"code":"SUCCESS","message":"成功"},
           "activityCode":"dtx2","activityStatusText":"进行中",
           "activityName":"麦麦积分抽奖",
           "beginTime":"2025-01-26 00:00:00","endTime":"2030-12-31 23:59:59",
           "drawPoint":"24","drawTypeText":"消耗积分抽奖","availablePoint":"0",
           "drawDecision":{"resourceEligible":false,"reason":"积分不足",
             "nextConsumption":{"type":"POINTS","points":"24","chances":0,
                                "text":"本次将消耗 24 积分"}},
           "prizes":[{"name":"下单立减3元券","typeText":"优惠券"}, …共 10 项…]}}
  ```
- **发现**：
  - `drawDecision.nextConsumption` 是**对象** `{type,points,chances,text}`，不是字符串；
  - 本次**没有** `availableTimes` 字段（纯积分规则不返回次数）；
  - 资格判断必须**只认 `resourceEligible`**：本次为 `false`，原因为「积分不足」。

#### ⑤ query-my-prizes —— 中奖记录

- 真实返回（节选）：
  ```json
  {"success":true,"code":200,
   "data":{"status":{"code":"SUCCESS","message":"成功"},
           "prizes":[],"pageNum":1,"pageSize":10,
           "hasMore":false,"truncated":false}}
  ```
- 结果：当前无中奖记录。

#### ⑥ query-my-coupons —— 我的券

- 真实返回为**纯文本**（**不是 JSON**）：
  ```
  # 您的优惠券列表
  暂无可用优惠券
  ```
- **发现**：该接口只返回「用户拥有的券」，**不校验门店 / 渠道 / 订单可用性**，不得承诺可用于当前订单。

#### ⑦ draw-lottery —— 执行抽奖（未执行）

- **未调用**，原因有二：
  1. `query-lottery-info` 返回 `resourceEligible = false`（积分不足），按规则**禁止**引导抽奖；
  2. 抽奖是**真实写操作**（会扣减积分），必须经用户明确确认，且严禁试抽。
- 其官方约束（用于固化文档）：
  - 必须已展示 `nextConsumption` 并获用户**明确**确认；「试试看」「如果可以就抽」**不算确认**；
  - 频控：短时间重复调用返回「操作太频繁，请稍后再试」且**不扣积分**；
  - 返回字段：`status{code,message}`、`win`、`prizes[]{name,imageUrl,typeText,validDateInfo}`。

### 3.3 五步工作流端到端验证

| 步骤               | 状态      | 说明                                                     |
| ---------------- | ------- | ------------------------------------------------------ |
| Step 1 并行聚合      | ✅       | 4 个核心工具在同一消息内并行调用，返回正常                                 |
| Step 2 解析 + 时间过滤 | ✅       | 识别「逐日分桶 + 标题去重」，剔除往期，标注进行中/即将开始                        |
| Step 3 标签筛选      | ✅       | 「学生」标签准确命中「学生专属 49 元 150 天麦金学期卡」                       |
| Step 4 三段式报告     | ✅       | 活动雷达 / 积分状态 / 积分抽奖 三块正常产出                              |
| Step 5 抽奖交互      | ⚠️ 分支验证 | 资格分支（`resourceEligible=false` → 拒绝抽奖）已验证；**成功抽奖路径未实测** |

**实测产出的报告样例（真实数据）**：

```
📡 活动雷达（进行中 / 即将开始）
1. [进行中] 超值9.9元早餐两件套      时间：10月8日 – 10月21日   参与门槛：凭券，两件套9.9元
2. [进行中] 韩式风味蘸酱上新         时间：10月8日 10:30 起      参与门槛：鸡薯双全盒15.9元起
   …（共 14 项进行中）
15. [即将开始] PEACEMINUSONE 联名徽章  时间：10月15日 10:45 开售  参与门槛：任意餐品 +39.9 元
16. [即将开始] 限定主题丝巾            时间：10月22日 10:45 开售  参与门槛：任意餐品 +39.9 元

💰 积分状态
可用积分：0 分
累计积分：56.9 分    已过期：56.9 分    本月·下月将过期：0 分

🎰 可参与积分抽奖
活动：麦麦积分抽奖（进行中）
消耗规则：消耗积分抽奖，单次 24 积分
可抽状态：❌ 积分不足（可用积分 0）
```

---

## 4. 遇到的问题与修正

### 4.1 第一轮：真实调用后发现「文档与实测不符」（4 项）

| # | 问题                                       | 修正                                                                                          |
| - | ---------------------------------------- | ------------------------------------------------------------------------------------------- |
| 1 | `campaign-calendar` 被写成「今日/进行中/未来/往期」四分组 | 改为**逐日分桶**（`#### YYYY年MM月DD日`，当天带「今日」）；强调同一活动**跨日重复**、须**按标题去重**，用日期桶范围推算起止                 |
| 2 | `drawDecision.nextConsumption` 被当成字符串    | 更正为**对象** `{type,points,chances,text}`；补 `availableTimes` 为**条件返回**；补 `fallbackConsumption` |
| 3 | `query-my-account` 字段不全、类型未说明            | 补 `lastMouthExpirePoint`/`usedPoint`/`currency`；标注积分为**字符串且可为小数**；`accountId` 禁止输出          |
| 4 | `query-my-coupons` 被当作 JSON              | 更正为**纯文本**；补充「不校验门店/订单可用性」                                                                  |

### 4.2 第二轮：交付前系统性复核（4 项）

| # | 问题                      | 修正                                                                           |
| - | ----------------------- | ---------------------------------------------------------------------------- |
| 5 | 报告模板把「剩余可抽：N 次」当**必返项** | 改为**仅当返回 `availableTimes` 时输出**（纯积分规则无次数）                                    |
| 6 | `draw-lottery` 结果字段缺失   | 补 `win`、`prizes[].validDateInfo`（有效期）；规定非 SUCCESS 时**原样展示 `status.message`** |
| 7 | `now-time-info` 未收录     | 新增字段节，并标注其自带说明 `data.data.date` **多套一层**（实测为扁平 `data.date`）                  |
| 8 | 确认语义与频控未写明              | 补「『试试看』不算确认」「频控不扣积分、不得重试硬抽」「`fallbackConsumption` 必须说明」                      |

### 4.3 范围外工具排查

- `query-promotions`：**仅企业团餐场景**（`beType=6`，需 `storeCode`/`beCode`），不适用于本助手的 C 端场景，已排除；
- `query-store-coupons`：用于「某门店当前订单可用券」，与本助手「我的券」不同，仅在需要门店级校验时作为引导出口。

### 4.4 发现的矛盾数据

「过家家派对」出现在**今天（10/11）的桶**里，但活动内容写的是「9月9日到店」——两者矛盾。处理方式：在报告中对该项做**存疑提示**，**未替用户臆断**时间。

---

## 5. 最终 SKILL.md 说明

### 5.1 元信息

| 项             | 值                                                                                                                                                                                |
| ------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| name          | `maimai-activity-radar`                                                                                                                                                          |
| description   | 麦麦活动雷达助手（MaiMai Activity Radar）。当用户询问麦当劳官方营销活动、积分账户、积分抽奖、中奖记录或优惠券到账情况，或希望参加/发起积分抽奖时使用。聚合「活动日历 + 积分 + 抽奖」数据，按用户偏好筛选后输出结构化「活动雷达报告」，并在用户二次确认后执行抽奖。依赖 mcd-mcp 连接器。不处理点餐、下单、结算、领券等业务。 |
| agent_created | `true`                                                                                                                                                                           |

### 5.2 结构说明

```
maimai-activity-radar/
├── SKILL.md                       # 主流程：Overview / 前置条件 / Step 1-5 / 输出规范 / 安全合规 / FAQ
└── references/
    └── field-mapping.md           # 7 个工具的官方字段对照与输出要点（含实测校验）
```

`SKILL.md` 各节职责：

| 章节                       | 作用                                      |
| ------------------------ | --------------------------------------- |
| **Overview**             | 角色定位与边界声明                               |
| **前置条件**                 | 依赖 `mcd-mcp`；数据必须实时；字段细节查 references    |
| **Step 1 聚合原始数据**        | 并行调用 4 个核心工具；单维度请求只调对应工具                |
| **Step 2 解析活动日历 + 时间过滤** | 逐日分桶、按标题去重、解析起止、剔除往期、标注即将开始             |
| **Step 3 按用户标签筛选**       | 学生 / 甜品 / 抽奖党 / 免消费 等标签的包含匹配规则          |
| **Step 4 输出活动雷达报告**      | 三段式（活动雷达 / 积分状态 / 积分抽奖）输出模板             |
| **Step 5 抽奖交互**          | 二次确认硬门槛、资格只认 `resourceEligible`、失败/频控处理 |
| **输出规范**                 | 活动条目必备字段、积分过期提示、数字原值                    |
| **安全与合规（强制）**            | 不编造 / 不泄密 / 不越界 / 隐私 / 限流               |
| **FAQ**                  | 6 条常见越界或疑问的统一应答                         |
| **Resources**            | 指向 field-mapping.md                     |

完整正文见 [附录 A](#附录-askillmd-全文)。

---

## 6. 未验证项与后续计划

| 未验证项                | 影响                              | 建议                 |
| ------------------- | ------------------------------- | ------------------ |
| `draw-lottery` 成功路径 | 中奖展示（`win`/`prizes`/有效期）未经真实验证  | 积分攒到 ≥ 24 后补一次真实抽奖 |
| 频控文案                | 「操作太频繁」实际触发未验证                  | 补测时连点验证并核对文案       |
| `availableTimes` 分支 | 当前账号为纯积分规则，次数/混合规则未覆盖           | 有对应活动时补测           |
| 中奖记录 / 券非空分支        | 当前均为空，展示格式未验证                   | 有数据后回归             |
| 跨月边界                | 月末/月初 `campaign-calendar` 表现未验证 | 月末或月初补测            |
| 分组与内容日期矛盾           | 如「过家家派对」                        | 已做存疑提示；可考虑固化为显式规则  |


**可选增强**：
1. 把「日期桶与内容日期矛盾时的处理」写成 Step 2 的显式规则；
2. 为 `campaign-calendar` 增加 `specifiedDate` 用法示例（查某一天附近的活动）。

---

## 7. 安全与脱敏声明

- 本文档**不包含任何真实 Token / 密钥**。本次会话中从未输出过真实凭据；若涉及配置示例，一律使用占位符 **`YOUR_MCP_TOKEN`**。
- `query-my-account` 返回的 `accountId` 属个人敏感信息，本文档中**已脱敏为 `<已脱敏>`**，与 skill 的隐私条款一致。
- 积分数字、活动数据均来自麦当劳官方 MCP 接口的**实时返回**，示例数值仅为当次快照，不构成长期有效数据。
- 全文未执行任何写操作（`draw-lottery` 未调用），未产生任何扣分或交易。

---

## 附录 A：SKILL.md 全文

````markdown
---
name: maimai-activity-radar
description: 麦麦活动雷达助手（MaiMai Activity Radar）。当用户询问麦当劳官方营销活动、积分账户、积分抽奖、中奖记录或优惠券到账情况，或希望参加/发起积分抽奖时使用。聚合「活动日历 + 积分 + 抽奖」数据，按用户偏好筛选后输出结构化「活动雷达报告」，并在用户二次确认后执行抽奖。依赖 mcd-mcp 连接器。不处理点餐、下单、结算、领券等业务。
agent_created: true
---

# 麦麦活动雷达助手（MaiMai Activity Radar）

## Overview

把分散在麦当劳官方 MCP 接口里的「活动日历、积分账户、积分抽奖」三类数据聚合起来，按用户偏好标签筛选，让用户一眼看清「现在有什么活动值得参加、我的积分能干什么」，并在用户二次确认后代为抽奖。

**边界声明**：只负责活动 / 积分 / 抽奖。不点餐、不下单、不结算、不领券。遇到这类需求，礼貌说明职责范围，并引导用户使用官方小程序 / App。

## 前置条件

- 连接器 `mcd-mcp` 已配置并启用。若工具不可用，提示用户先在「连接器」中启用 `mcd-mcp`（本 skill 不负责配置连接器）。
- 所有数据必须来自 MCP 工具**实时返回**，严禁编造活动、积分、奖品。
- 官方返回字段的含义与输出要点见 `references/field-mapping.md`；字段不确定时优先读该文件，不要凭猜测解释。

## 核心工作流

### Step 1：聚合原始数据

用户发起活动 / 积分 / 抽奖类请求时，**在同一条消息里并行调用**下列工具，减少等待：

| 工具（官方名） | 用途 | 返回形态 |
| --- | --- | --- |
| `now-time-info` | 服务器标准时间（时间戳 / 格式化时间 / 时区） | JSON |
| `campaign-calendar` | 当月营销活动日历（默认当前月） | 文本，按日期分桶 |
| `query-my-account` | 积分账户：可用 / 累计 / 已过期 / 本月·下月将过期 / 冻结 | JSON |
| `query-lottery-info` | 积分抽奖：状态 / 奖品 / 单次消耗 / 剩余次数 / 资源决策 | JSON |

调用注意：

- 单个工具失败时如实告知用户，**不要用猜测数据补位**。
- 用户只问单一维度（如「我有多少积分」）时，只调用对应工具，不必全量拉取。
- 追问场景按需调用：中奖记录 → `query-my-prizes`；券是否到账 → `query-my-coupons`。

### Step 2：解析活动日历并做时间过滤

`campaign-calendar` 返回的是**按日期分桶的文本**（并非固定的「今日/进行中/未来/往期」四分组），解析要点：

- 形如 `#### 2026年10月11日 今日` 的标题是**日期分桶**；当天桶带「今日」后缀，其余为纯日期标题。
- 只列出**有活动的日期**；同一活动会在其覆盖的多个日期下**重复出现**（例：跨多日的早餐活动会连续出现在每一天的桶里）。
- 因此必须**按活动标题去重**，再把各桶日期拼成时间轴：最早出现的桶 ≈ 开始日，最晚出现的桶 ≈ 结束日。
- 优先从「活动内容介绍」里解析明确起止（如「10月8日至10月21日」）；解析不到时，才退化为用**出现过的日期桶范围**作时间依据，绝不臆造时间。

过滤规则，以 `now-time-info` 的服务器时间为基准：

- 解析出的 `end_time < now` → 剔除（已结束）。
- `start_time > now` → 保留并标注「即将开始」。
- 其余 → 标注「进行中」。

### Step 3：按用户标签筛选

主动询问或识别用户偏好标签，常见：学生、甜品爱好者、积分抽奖党、只看免消费活动、早餐、新品、夜间 等。

对活动的**标题 / 内容介绍 / 参与条件**做包含匹配：

- 「学生」→ 含学生 / 教育优惠 / 学期卡等；
- 「甜品爱好者」→ 含甜品、冰淇淋、麦旋风、圆筒、派、爆爆珠等；
- 「积分抽奖党」→ 与积分抽奖、消耗积分相关；
- 「只看免消费活动」→ 参与条件为无消费门槛 / 免费 / 0 元。

用户未给标签时，默认展示全部「进行中 + 即将开始」的活动，按**结束时间升序**排列。

### Step 4：输出「活动雷达报告」

报告固定分三块（下方为格式示意，数值仅作占位，实际必须用官方返回值）：

```
📡 活动雷达（进行中 / 即将开始）

1. [进行中] 超值9.9元早餐两件套
   时间：10月8日 – 10月21日
   参与门槛：凭券购买，两件套9.9元
   标签：早餐 / 优惠券

2. [即将开始] 新品上市尝鲜周
   时间：10月13日 – 10月19日
   参与门槛：无消费门槛
   标签：新品 / 免消费

💰 积分状态
可用积分：2,850 分
本月将过期：200 分（记得用掉！⚠️）

🎰 可参与积分抽奖
活动：麦麦积分抽奖（进行中）
消耗规则：消耗积分抽奖，单次 24 积分
剩余可抽：10 次
奖品概览：下单立减3元券、麦辣三件套5折券、麦旋风5折券……
如需抽奖，直接告诉我「帮我抽一次」。
```

模板说明：`剩余可抽` 一行**仅当 `query-lottery-info` 返回 `availableTimes` 时**才输出（纯积分规则的抽奖没有次数）；无次数时省略该行。

### Step 5：抽奖交互（用户确认后执行）

1. 先展示 `query-lottery-info` 的结果：活动名、活动状态、消耗规则、单次消耗积分、可用积分、奖品概览；若返回 `availableTimes` 再一并展示剩余可抽次数。
2. **二次确认是硬门槛**：展示 `drawDecision.nextConsumption`，明确告知本次将消耗多少积分、当前可用积分、预计剩余积分。用户**明确同意**后才调用 `draw-lottery`（「试试看」「如果可以就抽」不算确认）。
3. 资格判断**只认 `data.drawDecision`**：`resourceEligible = false` 时**禁止**调用 `draw-lottery`，改为如实转述 `reason`（如「积分不足」）。
   - 不要用 `availableTimes` 为 0 / null，或 `drawTypeText` 自行推断能否抽奖；混合规则下 `availableTimes = 0` 且 `nextConsumption.type = POINTS` 仍可用积分抽。
   - 若 `fallbackConsumption` 不为 `null`，需说明「本次优先消耗次数；次数用完后改为消耗积分」。
4. 抽奖后：先展示 `draw-lottery` 返回的 `win`（是否中奖）与 `prizes[]`（含 `name` / `typeText` / `validDateInfo` 有效期）；再调 `query-my-account` 刷新积分，汇报本次消耗与剩余积分。
5. 失败 / 频控：`status.code` 非 SUCCESS 时**原样展示 `status.message`**（如「操作太频繁，请稍后再试」），不要改写、不要重试硬抽。

字段细节见 `references/field-mapping.md`。

## 输出规范

- 活动条目必须含：**活动名、起止时间、参与门槛**；能标注标签更好。
- 积分必须区分「可用积分」与「本月 / 下月将过期积分」；过期项用醒目文案（如 ⚠️）。积分为 0 时直说，不要含糊。
- 抽奖必须告知：**单次消耗积分、奖品概览**（有 `availableTimes` 时附剩余可抽次数）；资源不足时如实说明原因。
- 优先列表 / 分段呈现，避免大段文字；数字保持官方返回**原值**（可为小数，如 `56.9`），不做四舍五入或猜测。

## 安全与合规（强制）

- **不编造数据**：活动、积分、奖品全部以 MCP 实时返回为准。
- **不泄露凭据**：绝不读取、展示、回显 MCP Token 或任何账号凭证。
- **不越界操作**：抽奖前必须二次确认；不做下单、支付、领券等范围外动作。
- **隐私**：不输出手机号、`accountId` 等个人敏感信息；积分数字仅在当前会话展示。
- **限流**：避免重复调用同一工具（每个 Token 每分钟最多 600 次请求）；遇到 429，提示用户稍后再试。

## 边界与常见问题（FAQ）

| 用户提问 | 助手应答 |
| --- | --- |
| 帮我点个套餐 | 本助手专注活动 / 积分 / 抽奖，不提供点餐服务，建议使用官方小程序 / App |
| 这个活动怎么参加 | 展示官方参与条件；如需到店 / 下单，引导至官方渠道 |
| 抽奖会扣多少分 | 展示 `query-lottery-info` 的单次消耗与剩余次数，确认后再抽 |
| 我这个券能用吗 | 调 `query-my-coupons` 查询，按官方返回说明（该接口不校验门店 / 订单可用性） |
| 数据准吗 | 全部来自麦当劳官方 MCP 实时接口，以官方返回为准 |
| 积分不够抽奖怎么办 | 如实转述 `drawDecision.reason`（如积分不足），并建议通过参与活动攒积分 |

## Resources

- `references/field-mapping.md` — `now-time-info` / `query-my-account` / `query-lottery-info` / `draw-lottery` / `campaign-calendar` / `query-my-prizes` / `query-my-coupons` 的官方字段对照与输出要点（含已实测校验的真实返回结构）。
````

---

## 附录 B：references/field-mapping.md 全文

````markdown
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
| `data.prizes[].recordTime` | 中奖时间 | 展示 |
| `data.pageNum` / `data.pageSize` / `data.hasMore` / `data.nextCursor` / `data.truncated` | 分页信息 | 有下一页时按需翻页 |
| 入参 | `pageNum`（默认 1）、`pageSize`（默认 10，最大 50） | 字符串类型 |

## query-my-coupons（我的券）

- 返回**纯文本**（如「暂无可用优惠券」），不是 JSON。
- 入参：`page`（默认 1，最多 5 页）、`pageSize`（默认 200，最大 200）。
- ❗ 该接口只返回「用户拥有的券」，**不校验门店 / 渠道 / 订单可用性**，不得承诺可用于当前订单；若目标是「当前订单可用的券」，应改用 `query-store-coupons`。
````
