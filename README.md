# 📡 麦麦活动雷达助手（MaiMai Activity Radar）

> 麦当劳官方 MCP Skill 智能助手 —— 聚合活动、积分、抽奖，帮你不错过任何限时福利。

基于 **麦当劳中国官方 MCP 服务**（[M-China/mcd-mcp-server](https://github.com/M-China/mcd-mcp-server)）开发的活动雷达 Skill：
一次对话聚合 **官方活动日历 + 积分账户 + 积分抽奖** 三类数据，按你的偏好智能筛选，
并主动提醒即将过期的积分。让「麦门」爱好者不再错过上新、限时活动和积分玩法。

> 🏆 本项目为「麦当劳程序员创意开发大赛」参赛作品，参赛声明见 [CONTEST_DECLARATION.md](./CONTEST_DECLARATION.md)。

---

## ✨ 核心功能

| 功能 | 说明 |
| --- | --- |
| 📡 活动雷达 | 自动拉取当月全部官方营销活动（进行中 / 即将开始），按结束时间排序 |
| 🏷️ 智能筛选 | 支持用户偏好标签：学生、甜品爱好者、积分抽奖党、只看免消费活动…… |
| 💰 积分管家 | 展示可用积分，主动提醒**本月/下月即将过期积分**，不让积分沉睡 |
| 🎰 抽奖直达 | 展示可参与积分抽奖（单次消耗、剩余次数、奖品概览），确认后一键抽奖 |
| ⏱️ 时效保证 | 以服务器标准时间过滤已结束活动，只推荐现在能参加的 |

**边界**：不做点餐下单，聚焦「活动 · 积分 · 抽奖」，职责清晰。

---

## 🎯 为什么做这个？

- **活动分散**：麦当劳活动分布在 App、小程序、线下多个渠道，上新了限时活动用户很难及时知道；
- **积分浪费**：很多人不知道自己有多少积分、哪些快过期，更不知道积分能参加什么活动；
- **抽奖隐蔽**：积分抽奖的规则（单次消耗、剩余次数、奖品）不直观，缺一个统一入口。

「麦麦活动雷达助手」把这三件事聚合到一个 Skill 里，一句话搞定。

---

## 🚀 快速开始

### 1. 申请 MCP Token

1. 打开 [麦当劳 MCP 开放平台](https://open.mcd.cn/mcp)，手机号登录；
2. 点击右上角【控制台】→【激活】，申请并复制 MCP Token。

### 2. 配置 MCP 连接器

在 WorkBuddy（或 Cherry Studio / Cursor 等支持 Streamable HTTP 的 MCP 客户端）中配置：

```json
{
  "mcpServers": {
    "mcd-mcp": {
      "type": "streamablehttp",
      "url": "https://mcp.mcd.cn",
      "headers": {
        "Authorization": "Bearer YOUR_MCP_TOKEN"
      }
    }
  }
}
```

> ⚠️ 将 `YOUR_MCP_TOKEN` 替换为你的真实 Token 后保存并启用连接器。
> 仓库内 [mcp-config.example.json](./mcp-config.example.json) 仅含占位符，**严禁提交真实密钥**。

### 3. 加载 Skill

将 [`skill/SKILL.md`](./skill/SKILL.md) 导入你的 Agent/Skill 系统（WorkBuddy 中可直接把本文档作为技能说明加载），启用 `mcd-mcp` 连接器后即可对话。

### 4. 本地运行演示（可选）

无需 Token 也可体验完整流程（使用模拟数据）：

```bash
python src/mai_radar.py --tags 学生 甜品 积分抽奖
```

运行单元测试：

```bash
python -m unittest discover -s tests -v
```

---

## 💬 使用示例

**用户：** 最近麦当劳有什么新活动？我是甜品爱好者，早上也常吃早餐。

**助手：**

```
📡 活动雷达（进行中 / 即将开始）

1. [进行中] 超值9.9元早餐两件套
   时间：10月8日 – 10月21日（工作日早餐时段）
   参与门槛：凭券购买，两件套9.9元
   标签：早餐 / 优惠券

2. [进行中] 蓝莓爆爆珠麦旋风上新
   时间：10月8日 – 10月31日
   参与门槛：到店甜品站购买
   标签：甜品 / 新品

💰 积分状态
可用积分：2,850 分
本月将过期：200 分（记得用掉！⚠️）

🎰 可参与积分抽奖
活动：麦麦积分抽奖（进行中）
单次消耗：24 积分 ｜ 剩余可抽：10 次
奖品概览：下单立减3元券、麦辣三件套5折券、麦旋风5折券……
如需抽奖，直接告诉我「帮我抽一次」。
```

> 演示数据取自 2026 年 10 月官方活动日历实测（结构化整理），字段与官方返回一致。

更多场景（抽奖执行、积分不足、只看免消费、不做点餐）见 [examples/demo-conversation.md](./examples/demo-conversation.md)。

---

## 📂 项目结构

```
.
├── README.md                    # 项目介绍、使用示例、目标用户（本文件）
├── CONTEST_DECLARATION.md       # 参赛声明（官方原版，不可修改）
├── MCP_INTEGRATION.md           # MCP 集成说明：Server/Tool/调用流程/业务价值
├── mcp-config.example.json      # 脱敏 MCP 配置示例（仅占位符）
├── skill/
│   ├── SKILL.md                 # 核心 Skill 源代码（工作流 Step1-5、输出规范、安全合规）
│   └── references/
│       └── field-mapping.md      # 7 个工具的官方字段对照（含真实联调校验）
├── src/
│   └── mai_radar.py             # 本地计算模块：时间过滤、标签匹配、报告排版（纯标准库）
├── tests/
│   └── test_mai_radar.py        # 单元测试
└── examples/
    ├── demo-conversation.md     # 使用示例对话（5 个场景）
    └── mock-data/               # 模拟数据（字段与官方返回结构一致）
        ├── campaign-calendar.json
        ├── query-my-account.json
        ├── query-lottery-info.json
        └── draw-lottery.json
```

---

## 🧩 用到的 MCP 工具

| Tool | 用途 |
| --- | --- |
| `campaign-calendar` | 活动日历：当月全部营销活动（按日期分组） |
| `query-my-account` | 积分账户：可用/累计/本月将过期/下月将过期 |
| `query-lottery-info` | 积分抽奖：活动状态、消耗规则、剩余次数、资源决策 |
| `draw-lottery` | 执行积分抽奖（用户确认后调用） |
| `now-time-info` | 服务器标准时间，过滤已结束活动 |

> 增强能力（可选）：`query-my-prizes`（我的奖品）、`query-my-coupons`（我的券）。
> 详细调用流程与字段结构见 [MCP_INTEGRATION.md](./MCP_INTEGRATION.md)。

---

## 👤 目标用户

- 经常玩麦当劳积分、蹲守限时活动的「麦门」爱好者
- 学生群体（关注学生优惠、早餐特惠）
- 甜品/新品尝鲜人群
- 手里有积分但不知道如何使用的用户

---

## 🛡️ 安全与合规

- 仓库内**不含任何真实 Token/密钥**，配置仅用环境变量占位符（见 [CONTEST_DECLARATION.md](./CONTEST_DECLARATION.md)）；
- 所有数据来自麦当劳官方 MCP 实时接口，不缓存、不编造；
- 抽奖为真实积分消耗，Skill 强制二次确认后才执行；
- 本作品非麦当劳官方产品，输出仅供参考，以官方渠道实时结果为准。

---

## ⭐ 喜欢就点个 Star

如果这个 Skill 对你有用，欢迎 ⭐ Star 支持一下，也欢迎提 Issue 建议新功能～
