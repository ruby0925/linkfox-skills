# Sponsored Brands V4 API

V4 是默认版本，支持 Legacy 与 Multi-Ad-Group Campaign。共存规则见 [sb-coexistence.md](./sb-coexistence.md)。

## 脚本

| 资源 | 脚本 | Amazon 路径 |
|---|---|---|
| Campaign | `list/create/update_campaigns.py` | `sb/v4/campaigns[/list]` |
| Ad Group | `list/create/update_ad_groups.py` | `sb/v4/adGroups[/list]` |
| Ad | `list/create/update_ads.py` | `sb/v4/ads[/list]`、`sb/v4/ads/{adType}` |
| Keyword | `list/create/update_keywords.py` | `sb/keywords`（共享 targeting 路径；GET 使用 SB keyword V3 media type；create/update 请求体使用 `application/json`） |
| Target | `list/create/update_targets.py` | `sb/targets[/list]`（共享 targeting 路径；使用 `application/json`） |
| Creative Version | `list_creatives.py`、`create_creatives.py` | `sb/ads/creatives/list` 按 `adId` 查询；`sb/ads/creatives/{creativeType}` 创建新版本 |
| Budget Rule | `list/create/update_budget_rules.py` | `sb/budgetRules` |

所有路径都位于 `scripts/sb/v4/`。旧的 `scripts/sb/*.py` 保留为 V4 兼容入口，新调用不要继续依赖旧路径。

## Campaign / Ad Group / Ad list

使用 V4 Object/Text filter：

```json
{
  "profileId": 1234567890,
  "region": "NA",
  "campaignIdFilter": {"include": ["1122334455"]},
  "stateFilter": {"include": ["ENABLED", "PAUSED"]},
  "maxResults": 100
}
```

响应包含 `nextToken`，Campaign/Ad Group/Ad 原始响应还可能包含 `totalCount`；skill 自动聚合为 `total`。

## Keyword / Target

Amazon 没有 `/sb/v4/keywords` 或 `/sb/v4/targets` 路径。V4 脚本通过 `campaignId + adGroupId` 调用共享 targeting 资源：

```bash
python scripts/sb/v4/list_keywords.py '{"profileId":1234567890,"region":"NA","campaignIdFilter":["1122334455"],"adGroupIdFilter":["5566778899"]}'

python scripts/sb/v4/list_targets.py '{"profileId":1234567890,"region":"NA","campaignIdFilter":{"include":["1122334455"]},"stateFilter":["enabled"]}'

python scripts/sb/v4/create_targets.py '{"profileId":1234567890,"region":"NA","payload":{"targets":[{"campaignId":1122334455,"adGroupId":5566778899,"expressions":[{"type":"asinSameAs","value":"B0EXAMPLE"}],"bid":1.25}]}}'
```

`list_targets.py` 会把顶层 `campaignIdFilter` / `adGroupIdFilter` / `stateFilter` 等映射为 Amazon `filters[]`，避免按 keywords 习惯传参时静默全量拉取。这属于 Amazon 官方共享资源，并非 V4 失败后回退到 V3。

分页差异：

- `list_keywords.py` 是 `GET sb/keywords`，使用 `startIndex + count`。
- `list_targets.py` 是 `POST sb/targets/list`，使用 `nextToken`。
- `list_budget_rules.py` 是 `GET sb/budgetRules`，使用 `pageSize + nextToken`，响应列表字段兼容 `budgetRulesForAdvertiserResponse`。

Media type 差异：

- `create_keywords.py` / `update_keywords.py`：`Content-Type: application/json`，`Accept: application/vnd.sbkeywordresponse.v3+json`。
- `list_keywords.py`：`Accept: application/vnd.sbkeyword.v3+json`。

## Ad 与 Creative

创建 Ad 时必须传 `adType`：

```text
autoCollection
manualCollection
brandVideo
video
productCollection
productCollectionExtended
storeSpotlight
```

创建新的 Creative Version 时，使用 `create_creatives.py`，传：

```text
productCollection
productCollectionExtended
storeSpotlight
video
brandVideo
```

示例：

```bash
python scripts/sb/v4/create_creatives.py '{"profileId":1234567890,"region":"NA","creativeType":"productCollection","payload":{"adId":"998877","creative":{"asins":["B0EXAMPLE"],"headline":"Example"}}}'
```

查询 Creative Version 时使用 `list_creatives.py`，必须传 `adId`；该接口不是全账号 Creative 全量列表：

```bash
python scripts/sb/v4/list_creatives.py '{"profileId":1234567890,"region":"NA","adId":"998877","maxResults":100}'
```

当前 SB V4 Creative 支持“按 Ad 查询 Creative Version”和“创建新 Creative Version”，没有 `update_creatives.py`。

## 选择规则

- 新建活动、多 Ad Group、Ad、独立 Creative：V4。
- 未说明版本的关键词/定向管理：默认 V4 入口。
- 只有确认是 Legacy 或用户明确要求 V3 时，改用 `scripts/sb/v3/`。
- 调用失败时不自动转 V3。
