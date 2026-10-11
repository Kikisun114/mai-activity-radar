# WorkBuddy 开发与对话导出指南（拿 3,000 积分专项奖用）

> 目标：在 WorkBuddy 中**真实开发并调试**「麦麦活动雷达助手」Skill，
> 然后把这段开发对话导出为 `workbuddy.md`，替换仓库根目录的模板文件。
> 排行榜前 100 名作品提交 `workbuddy.md` 可获得 **3,000 WorkBuddy AI 积分**。
>
> 参考官方文档：<https://www.workbuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/Connector>

---

## 第 1 步：准备

- [ ] 已申请麦当劳 MCP Token（[open.mcd.cn/mcp](https://open.mcd.cn/mcp) 控制台激活）；
- [ ] 已安装并登录 WorkBuddy；
- [ ] 本仓库的 `mcp-config.example.json` 已就绪（脱敏版，仅占位符）。

## 第 2 步：在 WorkBuddy 配置 MCP 连接器

1. 打开 WorkBuddy，左侧边栏找到【**专家·技能·连接器**】，选中【**连接器**】页签；
2. 点击右上角【**自定义连接器**】→【**配置MCP**】；
3. 把下面 JSON 粘贴进去，**把 `YOUR_MCP_TOKEN` 替换为你的真实 Token**，点击【保存】：

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

4. 回到【自定义连接器】列表，将 `mcd-mcp` 的开关**启用**；
5. 确认连接器显示「已连接」（可用对话框问一句"现在几点"，能调用成功即连通）。

## 第 3 步：加载 Skill

1. 在【专家·技能·连接器】的【**技能**】页签中新建/导入一个技能；
2. 把本仓库 [`skill/SKILL.md`](./skill/SKILL.md) 的完整内容粘贴进去（名称：麦麦活动雷达助手）；
3. 保存并启用该技能。

## 第 4 步：开发调试对话（这段对话就是要导出的内容）

在 WorkBuddy 对话框中**按顺序**进行以下操作，让 AI 实际调用 MCP 工具。每步都保留对话，这就是开发过程记录：

| 顺序 | 你输入 | 验证点（对话里应体现） |
| --- | --- | --- |
| 1 | 我要开发一个「麦麦活动雷达助手」，聚合麦当劳活动、积分、抽奖……帮我设计流程 | 需求构思与方案讨论 |
| 2 | 现在几点？ | 调用 `now-time-info`，确认时间 |
| 3 | 最近麦当劳有什么活动？ | 调用 `campaign-calendar`，拿到活动列表 |
| 4 | 查一下我的积分 | 调用 `query-my-account`，展示可用/将过期积分 |
| 5 | 有什么积分抽奖可以参加？ | 调用 `query-lottery-info`，展示单次消耗、剩余次数、奖品 |
| 6 | 我是甜品爱好者，早上常吃早餐，帮我筛一下适合我的活动 | 完整流程：时间过滤 + 标签筛选 + 输出报告 |
| 7 | 帮我抽一次奖 | 应触发二次确认；若积分不足，应如实提示「积分不足」**且不调用** `draw-lottery` |
| 8 | 帮我点一个巨无霸套餐 | 应礼貌拒绝并说明边界（不做点餐） |

**调试记录建议**：如果某次调用报错（如 401/429/字段解析问题），在对话里追问 AI 排查、修正后重试——「遇到问题→解决」的过程正是 WorkBuddy 核验时最看重的内容。

## 第 5 步：导出并替换 workbuddy.md

1. 开发完成后，在 WorkBuddy 中找到该会话的导出功能，导出为 **Markdown（MD）格式**；
2. ⚠️ **Token 脱敏检查（必做）**：导出后用编辑器搜索你的真实 Token 字符串，
   如果对话里出现过配置 JSON（含真实 Token），**全部替换为 `YOUR_MCP_TOKEN`**；
3. 用导出文件**整体替换**仓库根目录的 `workbuddy.md`（文件名不可改动）；
4. 本地自检：文件中应包含连接器配置、MCP 工具真实调用、流程验证、调试过程。

## 第 6 步：提交前自检清单

- [ ] `workbuddy.md` 已替换为 WorkBuddy 实际导出的完整开发对话（MD 格式）；
- [ ] 对话中包含 `mcd-mcp` 连接器配置与启用过程；
- [ ] 对话中包含至少 `now-time-info`、`campaign-calendar`、`query-my-account`、`query-lottery-info` 的真实调用与结果讨论；
- [ ] 对话中**不含真实 MCP Token / 密钥 / 个人敏感信息**（已搜索替换）；
- [ ] 其余强制文件齐全：`README.md`、`CONTEST_DECLARATION.md`、`MCP_INTEGRATION.md`、源代码。
