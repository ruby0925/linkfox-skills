# Walmart 产品分析 API 参考

## 调用规范

- **请求地址**：`${LINKFOX_TOOL_GATEWAY}/sorftime/walmart/productAnalysis`
- **请求方式**：POST，`Content-Type: application/json`
- **认证方式**：Header `Authorization: <api_key>`；api_key 优先从 `LINKFOX_AGENT_API_KEY` 读取，回退 `LINKFOXAGENT_API_KEY`
- **User-Agent**：`LinkFox-Skill/2.0`
- **超时**：150s
- **透传 Header**：`SESSION_ID`、`MODE_ID`、`APP_NAME`
- **市场**：Walmart 美国站；后端固定使用 Sorftime `domain=21`

请求体为扁平 JSON。一次只选择一个大小写严格匹配的 `operation`；不得批量或自动串行调用。上游普通 JSON 与 Base64/GZip 响应的识别、校验和解码均由服务端完成。

## 操作与请求参数

| operation | 用途 | 必填参数 | 可选参数 | 默认 | Sorftime Request |
|---|---|---|---|---|---:|
| `searchByName` | 按自然语言名称搜索相关商品 | `name` | `pageIndex` | 第 1 页 | 2 |
| `detail` | 商品详情 | `productId` | 无 | - | 1 |
| `trend` | 商品趋势 | `productId` | 无 | - | 2 |
| `salesVolume` | 按日/变体销量 | `productId` | `queryDate`, `queryEndDate`, `pageIndex` | 近 30 天；第 1 页 | 1 |

操作与对象字段：

| 参数 | 类型 | 规则 |
|---|---|---|
| `operation` | string | 必填；仅 `searchByName`、`detail`、`trend`、`salesVolume` |
| `name` | string | `searchByName` 必填；非空自然语言商品名称 |
| `productId` | string | `detail`、`trend`、`salesVolume` 必填；非空 Walmart ProductId |

分页与销量字段：

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `queryDate` | string | 否 | 开始日期，`yyyy-MM-dd` |
| `queryEndDate` | string | 否 | 截止日期，`yyyy-MM-dd`；仅给开始日期时默认当前日 |
| `pageIndex` | integer | 否 | `searchByName`、`salesVolume` 从 1 开始，默认 1；每页最多 100 条 |

`searchByName` 对应上游 `ProductSearchFromName`，使用自然语言名称返回相关商品。`salesVolume` 两日期均省略时默认最近 30 天。可查询的最早日期以 Sorftime 当前数据覆盖为准；开始日期不得晚于截止日期。

## 请求示例

```json
{"operation":"searchByName","name":"wireless earbuds","pageIndex":1}
```

```json
{"operation":"detail","productId":"5169493923"}
```

```json
{"operation":"trend","productId":"5169493923"}
```

```json
{"operation":"salesVolume","productId":"5169493923","queryDate":"2026-07-01","queryEndDate":"2026-07-31","pageIndex":1}
```

## 响应结构

网关使用两层状态：框架层为 `errcode` / `errmsg`，业务成功体内为 `code` / `msg`。成功时通常同时返回 `errcode=200`、`errmsg="ok"` 和 `code=200`、`msg="success"`；参数或服务异常时可能只返回 `errcode` / `errmsg`，应先判断框架层状态。

| 字段 | 类型 | 说明 |
|---|---|---|
| `errcode` | integer | 网关框架层状态码；`200` 表示请求成功进入业务响应 |
| `errmsg` | string | 网关框架层状态消息；成功时通常为 `ok` |
| `code` | integer | `200` 表示成功 |
| `msg` | string | 响应消息 |
| `data` | object | 固定响应容器；`data.value` 保留各 operation 的 Sorftime 原始对象、数组、标量或 `null` |
| `operation` | string | 本次实际执行的 `searchByName`、`detail`、`trend` 或 `salesVolume` |
| `requestConsumed` | integer | 本次上游消耗；上游缺失或返回 0 时按该 operation 的文档消耗补全；Sorftime 明确返回 `Code=11`（无数据）时保持 0 |
| `costTime` | integer | 耗时，毫秒 |
| `costToken` | integer / absent | 生产网关响应头 `X-Cost-Token`；入口脚本会复制到该字段。直接解析 JSON body 时该字段当前缺失 |
| `costCredit` | integer / absent | 生产网关响应头 `X-Cost-Credit`，即本次实际扣除算力；入口脚本会复制到该字段 |
| `sourceType` | string | `sorftime` |

Sorftime 明确返回 `Code=11`（无数据）时，网关保持 `requestConsumed=0`、`X-Cost-Token=0`，不按文档消耗补全；`X-Cost-Credit` 此时可能缺失。使用入口脚本时直接读取 `costToken` / `costCredit`；直接使用 curl 时从对应响应头读取。`data.value=null` 本身不等于 `Code=11`：生产实测某些 `Code=0` 空详情仍会正常消耗 Request，应结合 `msg` 与 `requestConsumed` 判断。

业务结果统一从 `data.value` 读取。网关不会改名、扁平化或补造其中的 Sorftime 字段，因此下表字段保持上游 PascalCase。无数据时 `data.value` 可能为 `null` 或空数组；有数据但某个指标暂缺时，对应字段可能为 `null` 或不出现。

### 各 operation 的 `data.value` 类型

| operation | 类型 | 元素类型 / 说明 |
|---|---|---|
| `searchByName` | array<object> | 相关商品摘要数组 |
| `detail` | object | 单个商品详情对象 |
| `trend` | object | 单个商品趋势对象 |
| `salesVolume` | array<array> | 销量记录行数组；每行为 `[date, sales, type]` |

### `searchByName` 与 `detail`：商品字段

`searchByName` 的数组元素与 `detail` 使用同一组商品基础字段；表中标记“详情扩展”的字段仅在 `detail` 响应中观察到。

| 字段 | 类型 | 说明 |
|---|---|---|
| `Title` | string | 商品标题 |
| `Photo` | array<string> | 商品图片 URL 数组 |
| `ListingSalesVolumeOfMonth` | integer | Listing 维度近 30 天预估销量，不区分变体 |
| `ListingSalesOfMonth` | integer | Listing 维度近 30 天预估销售额；美国站单位为美分 |
| `ProductId` | string | Walmart ProductId |
| `ParentProductId` | string | 父商品 ProductId |
| `Price` | integer | 售价；美国站单位为美分，如 `1999` 表示 `$19.99` |
| `Brand` | string | 品牌 |
| `Seller` | string | 采集时的卖家名称 |
| `Shipedby` | string | 采集时的配送方式；字段名是上游原始拼写 |
| `WFSFee` | integer | WFS 费用；美国站单位为美分 |
| `Attribute` | array<string> / null | 商品属性，按 `[属性名, 属性值, ...]` 交错编码 |
| `FirstReviewsDate` | string / null | 首条评论日期，`yyyy-MM-dd` |
| `ReviewsCount` | integer | 评论数 |
| `Ratings` | number | 评分，如 `4.8` |
| `NodePath` | array<string\|null> | 类目及排名记录，按 `[类目名, NodeId, 排名日期, 排名, ...]` 分组编码；某日排名缺失时对应位置为 `null` |
| `Label` | array<string> | 商品标签，如 `pickup`、`savewith`、`bestsell` |
| `PopularPick` | integer | Popular Pick 标记；`1` 表示存在 |
| `Clearance` | integer | Clearance 标记；`1` 表示存在 |
| `ReducedPrice` | integer | Reduced Price 标记；`1` 表示存在 |
| `Rollback` | integer | Rollback 标记；`1` 表示存在 |
| `FlashDeal` | integer | Flash Deal 标记；`1` 表示存在 |
| `Size` | array<string> / null | 外包装尺寸 `[最长边, 次长边, 最短边]`，单位 cm |
| `Weight` | number | 商品重量，单位 g |
| `Variants` | array / null | 变体数据；`searchByName` 与 `detail` 的编码不同，见下文 |
| `NumberOfStar` | array<number\|string> / null | 各星级评论数，按 `[星级, 评论数, ...]` 交错编码 |
| `Pickup` | integer | 详情扩展：Pickup 标签标记；`1` 表示存在 |
| `Savewith` | integer | 详情扩展：Save with 标签标记；`1` 表示存在 |
| `Bestseller` | integer | 详情扩展：Best Seller 标签标记；`1` 表示存在 |
| `UpdateDate` | string / null | 详情扩展：商品数据更新时间，通常为 `yyyy-MM-dd` |

`searchByName` 的 `Variants` 是对象数组，数组元素字段如下：

| 字段 | 类型 | 说明 |
|---|---|---|
| `VariantId` | string | 变体 ProductId |
| `Url` | string | 变体商品 URL |
| `Property` | array<string> | 变体属性，按 `[属性名, 属性值, ...]` 编码 |
| `PriceUpdate` | string / null | 价格更新时间，通常为 `yyyy-MM-dd` |
| `DetailUpdate` | string / null | 详情更新时间，通常为 `yyyy-MM-dd`；无有效日期时可能使用 `--` 等上游占位符 |

`detail` 的 `Variants` 在当前生产响应中是扁平数组，不是对象数组。每 3 项表示一个变体：

| 组内下标 | 类型 | 说明 |
|---:|---|---|
| `0` | string | 变体 ProductId |
| `1` | string | 变体商品 URL；上游值可能带前导空格，使用前宜 `trim` |
| `2` | array<string> | 变体属性，按 `[属性名, 属性值, ...]` 编码 |

例如两个变体的整体结构为 `[VariantId, Url, Property, VariantId, Url, Property]`。

### `trend`：商品趋势字段

趋势序列按 `[日期, 值, 日期, 值, ...]` 交错编码。真实响应中的日期和值当前均以字符串传输，调用方不要依赖 JSON 数字类型；需要计算时再显式转换。`RankTrend` 是二维数组，编码规则单独列出。

| 字段 | 类型 | 说明 |
|---|---|---|
| `ProductId` | string | Walmart ProductId |
| `ListingSalesVolumeOfMonth` | integer | 当前 Listing 维度近 30 天预估销量 |
| `ListingSalesOfMonth` | integer | 当前 Listing 维度近 30 天预估销售额；美国站单位为美分 |
| `ListingSalesVolumeOfMonthTrend` | array<string> | 月销量历史，按 `[yyyy-MM-dd, 销量, ...]` 编码 |
| `ListingSalesOfMonthTrend` | array<string> | 月销售额历史，按 `[yyyy-MM-dd, 销售额, ...]` 编码；金额单位为美分 |
| `PriceTrend` | array<string> | 价格历史，按 `[yyyy-MM-dd, 价格, ...]` 编码；金额单位为美分 |
| `ReviewsTrend` | array<string> | 评论数历史，按 `[yyyy-MM-dd, 评论数, ...]` 编码 |
| `StarTrend` | array<string> | 评分历史，按 `[yyyy-MM-dd, 评分, ...]` 编码；当前响应示例值为 `5.00` |
| `RankTrend` | array<array<string>> | 各类目排名历史；每行按 `[类目名, NodeId, 日期, 排名, 日期, 排名, ...]` 编码 |

### `salesVolume`：销量记录行

`data.value` 是二维数组。真实响应当前把三个值都序列化为字符串，例如 `["2026-08-31","10000","2"]`；下表说明其业务类型。

| 下标 | 业务类型 | 说明 |
|---:|---|---|
| `0` | date | 记录日期，`yyyy-MM-dd` |
| `1` | integer | 销量值 |
| `2` | integer | 记录类型；`2` 表示昨日单日销量 |

## 错误码

| errcode / HTTP | 含义 | 处理建议 |
|---:|---|---|
| 200 | 成功 | 按 operation 解析 `data.value` |
| 400 | 网关请求结构校验失败 | 检查全局必填 `operation`、operation 枚举、日期格式及 `pageIndex>=1` |
| 4000 | operation 的条件必填参数缺失 | 补充 `searchByName.name`，或 `detail`、`trend`、`salesVolume` 的 `productId` |
| 4001 | 后端语义校验失败 | 检查无关参数、真实日历日期及开始/结束日期顺序 |
| 401 | 认证失败 | 按 SKILL.md 的认证引导处理 |
| 402 | 算力不足 | 按 SKILL.md 的算力引导处理 |
| 5101–5103 | 上游 HTTP、响应或解析异常 | 不自动改变日期或操作重试 |
| 5104–5108 | 上游访问受限、参数、IP 或权限异常 | 核对参数；权限类问题交由服务维护方处理 |
| 5109–5111 | 上游额度或频率限制 | 稍后重试；不要连续请求 |
| 5112 | 其他上游业务异常 | 保留返回信息并反馈 |
| 5901 | 服务内部错误 | 稍后重试或反馈 |

网关参数校验错误可能使用 `application/xml` 返回 `ToolErrorResponse`，HTTP 状态可能为 200 或 400。入口脚本会把该 XML 统一转换成 JSON：`{"errcode":4001,"errmsg":"..."}`；直接使用 curl 时需同时兼容 JSON 与 XML。

## curl 示例

```bash
API_KEY="${LINKFOX_AGENT_API_KEY:-$LINKFOXAGENT_API_KEY}"
curl --max-time 150 -X POST "${LINKFOX_TOOL_GATEWAY}/sorftime/walmart/productAnalysis" \
  -H "Authorization: $API_KEY" -H "Content-Type: application/json" \
  -H "User-Agent: LinkFox-Skill/2.0" \
  -H "SESSION_ID: $SESSION_ID" -H "MODE_ID: $MODE_ID" -H "APP_NAME: $APP_NAME" \
  -d '{"operation":"detail","productId":"5169493923"}'
```

```bash
curl --max-time 150 -X POST "${LINKFOX_TOOL_GATEWAY}/sorftime/walmart/productAnalysis" \
  -H "Authorization: $API_KEY" -H "Content-Type: application/json" \
  -H "User-Agent: LinkFox-Skill/2.0" \
  -H "SESSION_ID: $SESSION_ID" -H "MODE_ID: $MODE_ID" -H "APP_NAME: $APP_NAME" \
  -d '{"operation":"searchByName","name":"wireless earbuds","pageIndex":1}'
```

```bash
curl --max-time 150 -X POST "${LINKFOX_TOOL_GATEWAY}/sorftime/walmart/productAnalysis" \
  -H "Authorization: $API_KEY" -H "Content-Type: application/json" \
  -H "User-Agent: LinkFox-Skill/2.0" \
  -H "SESSION_ID: $SESSION_ID" -H "MODE_ID: $MODE_ID" -H "APP_NAME: $APP_NAME" \
  -d '{"operation":"salesVolume","productId":"5169493923","pageIndex":1}'
```

## Feedback API

工具反馈使用独立端点 `POST https://skill-api.linkfox.com/api/v1/public/feedback`，`Content-Type: application/json`。

```json
{"skillName":"linkfox-sorftime-walmart-product-analysis","sentiment":"NEUTRAL","category":"SUGGESTION","content":"Describe intent, result, and feedback."}
```

`sentiment` 为 `POSITIVE`、`NEUTRAL`、`NEGATIVE` 之一；`category` 为 `BUG`、`COMPLAINT`、`SUGGESTION`、`OTHER` 之一。
