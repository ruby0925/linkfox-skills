---
name: linkfox-amazon-ads-sp-insights-report
description: 亚马逊广告 Sponsored Products（SP）洞察报告技能，统一获取 Audience 受众细分表现和 Search Term Impression Share/Rank 搜索词展示份额/排名两类 Amazon Ads Reporting API v1 beta 报告。自动完成 profile 到 advertiser account 映射、报告创建、状态轮询、多分片 CSV 下载和落盘。只有用户明确要求 SP 受众报告、SP 搜索词展示份额或展示份额排名时触发；普通 SP 搜索词表现报告、SB/SD/DSP 报告不得触发。本技能依赖 linkfox-amazon-ads-auth。
---

# Amazon Ads SP 洞察报告

统一获取两类 Sponsored Products 专项洞察报告：Audience 和 Search Term Impression Share/Rank。脚本经 `/amazonAds/developerProxy` 使用后台 Token，自动完成 advertiser account 映射、创建、轮询和 CSV 分片下载。Amazon 异步生成通常需要约 2–10 分钟，偶尔可能更久；等待不代表调用卡死或报告失败。

**依赖 `linkfox-amazon-ads-auth`**。入口启动时自动检查；缺失时以 exit 42 和 `DEPENDENCY_MISSING` 结束。

## 多账号处理

调用前先用 `linkfox-amazon-ads-auth/scripts/authorized_stores.py` 按站点解析 `profileId`：

1. 一个候选：静默使用。
2. 多个候选：按 `accountName` 向用户确认，禁止默认取第一个。
3. 无候选：引导用户完成 Amazon Ads 授权。
4. 不要求用户直接提供 `profileId` 数字。

## 报告路由

| 用户意图 | 入口脚本 | 详细规范 |
|---|---|---|
| SP 受众、Audience、受众细分表现 | `get_sp_audience_report.py` | `references/sp-audience-reporting-v1.md` |
| SP 搜索词展示份额、impression share、份额排名 | `get_sp_search_impression_share.py` | `references/sp-search-impression-share-v1.md` |

普通搜索词表现（曝光、点击、花费、转化）应使用 `linkfox-amazon-ads-report` 的 v3 `spSearchTerm`，不得使用本 Skill。SB、SD、DSP 或泛化市场份额请求也不得触发。

## 调用方式

- **API 端点**：`POST /amazonAds/developerProxy`（脚本内部按顺序调用三个 Ads v1 路径；完整参数、响应和错误码见 `references/api.md`）
- **Audience**：`python scripts/get_sp_audience_report.py '<JSON 参数>' [--inline] [--no-cache]`
- **Search Impression Share**：`python scripts/get_sp_search_impression_share.py '<JSON 参数>' [--inline] [--no-cache]`
- **成本约束**：本工具不消耗积分；成功结果按会话和参数缓存 24 小时。失败或空报告不得自动扩大日期、切换账号或连续试探。

**输出策略**：

- 完整响应始终写入 `<cwd>/linkfox/<YYYY-MM-DD>/<session>/data/linkfox-amazon-ads-sp-insights-report-<timestamp>.json`。
- 报告 CSV 分片写入同一会话的 `data/`；最终响应不暴露 Amazon 预签名 URL。
- 响应不超过 8 KB 时打印完整 JSON；更大时打印摘要；`--inline` 强制完整打印。
- `--no-cache` 强制重新获取；同一会话、同一报告类型和同一参数的成功结果默认命中 24 小时缓存。

## 参数指南

两个入口共同接受：

| 参数 | 必填 | 说明 |
|---|---:|---|
| `profileId` | 是 | 正整数；由 Ads Auth Skill 解析 |
| `region` | 是 | `NA` / `EU` / `FE` |
| `startDate` / `endDate` | 创建时是 | `YYYY-MM-DD`，不得晚于今天 |
| `timeUnit` | 否 | `DAILY`（默认）或 `SUMMARY` |
| `advertiserAccountId` | 否 | 自动映射失败时使用的 Ads v1 account ID |
| `pollInterval` | 否 | 5–300 秒，默认 60；官方建议每分钟轮询 |
| `maxAttempts` | 否 | 1–120，默认 10；配合默认 60 秒间隔形成约 10 分钟客户端等待窗口 |
| `reportId` | 否 | 传入后跳过账户映射和创建，仅轮询已有报告 |

Audience 额外支持 `detailLevel`：`ACCOUNT`（默认）、`CAMPAIGN`、`AD_GROUP`。Search Impression Share 不接受 campaign、adGroup、target、keyword、groupBy 或自定义 fields；这些维度与官方份额字段组合不兼容。

参数中禁止出现 access token、refresh token、LWA 密钥或自定义 Amazon 请求头；脚本会在联网前递归拒绝。

## Agent 执行流程

1. 根据用户表述选择且只选择一个入口；不要把普通 `spSearchTerm` 路由到份额报告。
2. 按站点解析唯一 `profileId` 与区域。
3. 确认日期和粒度；用户未指定时用 `DAILY`，Audience 用 `ACCOUNT`。
4. 调用前告知用户报告通常需要约 2–10 分钟，然后运行入口。脚本自动查询 advertiser account、创建报告、轮询并下载全部 CSV/gzip 分片；约 5 分钟仍未完成时会输出一次耐心提示。
5. `success=true` 时展示日期、报告类型、总行数、文件路径和预览；`totalRows=0` 是合法空报告。
6. `status=STILL_PROCESSING` 表示客户端等待窗口结束但 Amazon 仍在生成，并非失败。向用户确认是否继续，再用 `resumeHint.params` 和 `--no-cache` 续跑同一 `reportId`；不要创建第二份报告。

## 示例

### SP Audience

```bash
python scripts/get_sp_audience_report.py '{
  "profileId": 1234567890, "region": "NA",
  "startDate": "2026-08-01", "endDate": "2026-08-07",
  "timeUnit": "DAILY", "detailLevel": "ACCOUNT"
}'
```

### SP Search Term Impression Share/Rank

```bash
python scripts/get_sp_search_impression_share.py '{
  "profileId": 1234567890, "region": "NA",
  "startDate": "2026-08-01", "endDate": "2026-08-07",
  "timeUnit": "DAILY"
}'
```

## 结果与展示

成功结果包含 `reportKind`、`reportId`、`status`、`profileId`、`advertiserAccountId`、`fields`、`totalRows`、`dataFiles`、`preview`、轮询次数和耗时。

- Audience 重点展示 audience segment、曝光、点击、花费、购买、销售额和 ROAS；标注币种字段。
- Search Impression Share 重点展示 `searchTerm.value`、`metric.impressionShare` 和 `metric.impressionShareRank`。
- 客观呈现数据；除非用户要求，不主动给出商业决策建议。
- 不展示完整 Token、内部授权记录或预签名下载 URL。

## 限制与错误

- Amazon 官方当前将 Reporting API v1 标为 open beta；账号可能尚未开放，字段和限流可能变化，不按 GA 稳定性承诺。
- 报告为异步生成，通常约 2–10 分钟，Search Impression Share 偶尔可能更久；约 5 分钟会提示仍在上游生成。
- `HTTP 403`：检查 Ads API 应用及授权账号是否开放 v1；不得用 v3 数据伪造份额。
- `HTTP 429`：降低轮询频率，禁止密集重试。
- `FAILED`：透传 Amazon 失败详情，不自动换参数重建。
- `totalRows=0`：合法空结果，不自动扩大日期。
- 授权、普通 v3 报告和广告实体写操作分别交给 Ads Auth、Ads Report 和 Ads Manager Skill。

## Feedback

当功能与文档不一致、结果偏离用户意图、用户明确评价或发现可改进项时，按 `references/api.md` 调用 Feedback API；不要打断当前任务。

---
*For more high-quality, professional cross-border e-commerce skills, visit [LinkFox Skills](https://skill.linkfox.com/).*
