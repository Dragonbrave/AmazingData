# AmazingData API Service

基于中国银河证券「星耀数智」AmazingData SDK 封装的 REST API 数据服务，为 Node.js 或其他语言开发的 App 提供 A 股、ETF、可转债、期权、指数等金融市场数据。

---

## 部署

### 在 Zeabur 上部署（推荐）

1. 将 `data-service/` 整个目录上传到 Zeabur 作为一个新服务
2. 确保 `zbpack.json` 存在且内容为 `{ "serverless": false }`（容器化模式）
3. Zeabur 会自动使用 `Dockerfile` 构建（推荐）或根据 `zeabur.json` 运行

### Docker 部署

```bash
cd data-service
docker build -t amazingdata-api .
docker run -d -p 8000:8000 amazingdata-api
```

### 本地调试

```bash
cd data-service

# 1. 安装 whl 包
pip install lib/tgw-1.0.8.7-py3-none-any.whl
pip install lib/AmazingData-1.1.7-cp310-none-any.whl

# 2. 安装依赖
pip install -r requirements.txt

# 3. 启动
python main.py
# 服务运行在 http://0.0.0.0:8000
```

---

## 通用说明

### 请求方式

所有接口均为 `GET` 请求，参数通过 URL Query String 传递。

### 代码格式 (code_list)

多只证券代码用**英文逗号**分隔，格式为 `代码.市场后缀`：

| 市场 | 后缀 | 示例 |
|------|------|------|
| 上交所 | `.SH` | `600000.SH`，`510050.SH` |
| 深交所 | `.SZ` | `000001.SZ`，`159915.SZ` |
| 北交所 | `.BJ` | `838402.BJ` |
| 中金所(期货) | `.CFE` | `IF2401.CFE` |

### 日期格式 (begin_date / end_date)

`int` 类型，格式 `YYYYMMDD`，例如 `20240601` 表示 2024年6月1日。

### 时间格式 (begin_time / end_time)

K线和快照接口可选参数，`int` 类型。不同接口数值不同：

- **快照接口**：`90000000`（9:00），`172500000`（17:25）
- **K线接口**：`900`（9:00），`1725`（17:25）

### 响应格式

所有接口返回 JSON，统一结构：

```json
{
  "data": { ... },
  "count": 123
}
```

---

## API 接口

### 1. 健康检查

```
GET /api/health
```

**响应示例**：
```json
{
  "status": "ok",
  "timestamp": "2024-06-01T09:30:00"
}
```

---

### 2. 交易日历

```
GET /api/calendar
```

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| 无 | | | | |

**响应示例**：
```json
{
  "count": 365,
  "calendar": [20230103, 20230104, 20230105, ...]
}
```

---

### 3. 基础数据

#### 3.1 获取证券代码列表

```
GET /api/security/list
```

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| security_type | str | 否 | EXTRA_STOCK_A | 证券类型（见下方枚举） |

**security_type 取值**：

| 值 | 说明 |
|----|------|
| `EXTRA_STOCK_A` | 沪深北 A 股 |
| `EXTRA_STOCK_A_SH_SZ` | 仅沪深 A 股 |
| `SH_A` | 上交所 A 股 |
| `SZ_A` | 深交所 A 股 |
| `BJ_A` | 北交所 A 股 |
| `EXTRA_ETF` | 沪深 ETF |
| `SH_ETF` | 上交所 ETF |
| `SZ_ETF` | 深交所 ETF |
| `EXTRA_INDEX_A` | 沪深北指数 |
| `SH_INDEX` | 上交所指数 |
| `SZ_INDEX` | 深交所指数 |
| `BJ_INDEX` | 北交所指数 |
| `EXTRA_KZZ` | 沪深可转债 |
| `SH_KZZ` | 上交所可转债 |
| `SZ_KZZ` | 深交所可转债 |
| `EXTRA_HKT` | 沪深港股通 |
| `EXTRA_GLRA` | 沪深质押式回购 |

**调用示例**：
```
GET /api/security/list?security_type=EXTRA_ETF
```

**响应示例**：
```json
{
  "count": 952,
  "security_type": "EXTRA_ETF",
  "code_list": ["510050.SH", "510300.SH", "159915.SZ", ...]
}
```

---

#### 3.2 获取每日证券信息

```
GET /api/security/info
```

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| security_type | str | 否 | EXTRA_STOCK_A | 同 security/list |

**响应示例**：
```json
{
  "count": 5000,
  "data": [
    {
      "symbol": "000001.SZ",
      "security_status": 1,
      "pre_close": 12.50,
      "high_limited": 13.75,
      "low_limited": 11.25,
      "price_tick": 0.01
    }
  ]
}
```

---

#### 3.3 获取历史代码列表

```
GET /api/security/hist_list
```

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| security_type | str | 否 | EXTRA_STOCK_A_SH_SZ | 证券类型 |
| start_date | int | 否 | 20130101 | 起始日期 |
| end_date | int | 否 | 最新交易日 | 截止日期 |

**调用示例**：
```
GET /api/security/hist_list?start_date=20240101&end_date=20240601
```

---

#### 3.4 获取期货代码列表

```
GET /api/security/future_list?security_type=ZJ_FUTURE
```

---

#### 3.5 获取期权代码列表

```
GET /api/security/option_list?security_type=EXTRA_ETF_OP
```

---

#### 3.6 获取证券基本信息

```
GET /api/security/basic?code_list=000001.SZ,600000.SH
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| code_list | str | 是 | 逗号分隔代码列表 |

**响应示例**：
```json
{
  "count": 2,
  "data": [
    {
      "MARKET_CODE": "000001.SZ",
      "SECURITY_NAME": "平安银行",
      "COMP_NAME": "平安银行股份有限公司",
      "PINYIN": "PING AN YIN HANG",
      "COMP_NAME_ENG": "Ping An Bank Co.,Ltd.",
      "LISTDATE": 19910403,
      "DELISTDATE": null,
      "LISTPLATE_NAME": "主板",
      "COMP_SNAME_ENG": "PAB",
      "IS_LISTED": 1
    }
  ]
}
```

---

#### 3.7 获取历史证券状态

```
GET /api/security/hist_status?code_list=000001.SZ&begin_date=20240101&end_date=20240601
```

返回每日是否 ST、停牌、除权除息、涨跌停价等信息。

---

#### 3.8 北交所代码映射

```
GET /api/security/bj_code_mapping
```

返回北交所新旧代码对照表。

---

### 4. 复权因子

#### 4.1 后复权因子

```
GET /api/factor/backward?code_list=000001.SZ,600000.SH
```

#### 4.2 前复权因子

```
GET /api/factor/adj?code_list=000001.SZ,600000.SH
```

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| code_list | str | 是 | | 逗号分隔代码 |
| local_path | str | 否 | | 本地缓存路径 |
| is_local | bool | 否 | false | 是否仅读本地缓存 |

**响应示例**（前复权因子）：
```json
{
  "count": 120,
  "data": [
    { "date": "20240102", "000001.SZ": 1.0, "600000.SH": 1.0 },
    { "date": "20240103", "000001.SZ": 1.0, "600000.SH": 1.0 }
  ]
}
```

---

### 5. 行情数据

#### 5.1 K 线数据

```
GET /api/kline
```

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| code_list | str | 是 | | 逗号分隔代码 |
| begin_date | int | 是 | | 开始日期 YYYYMMDD |
| end_date | int | 是 | | 结束日期 YYYYMMDD |
| period | str | 否 | day | K 线周期 |
| begin_time | int | 否 | | 开始时间（日内筛选） |
| end_time | int | 否 | | 结束时间（日内筛选） |

**period 取值**：
`1min` / `3min` / `5min` / `10min` / `15min` / `30min` / `60min` / `120min` / `day` / `week` / `month` / `season` / `year`

**调用示例**：
```
GET /api/kline?code_list=000001.SZ,600000.SH&begin_date=20240601&end_date=20240630&period=day
GET /api/kline?code_list=510050.SH&begin_date=20240601&end_date=20240607&period=5min
```

**响应示例**：
```json
{
  "data": {
    "000001.SZ": [
      {
        "code": "000001.SZ",
        "kline_time": "2024-06-03T00:00:00",
        "open": 12.50,
        "high": 12.80,
        "low": 12.45,
        "close": 12.72,
        "volume": 120000000,
        "amount": 1526000000.0
      }
    ],
    "600000.SH": [
      { "code": "600000.SH", "kline_time": "2024-06-03T00:00:00", "open": 8.30, ... }
    ]
  }
}
```

---

#### 5.2 历史行情快照

```
GET /api/snapshot
```

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| code_list | str | 是 | | 逗号分隔代码 |
| begin_date | int | 是 | | 开始日期 YYYYMMDD |
| end_date | int | 是 | | 结束日期 YYYYMMDD |
| begin_time | int | 否 | | 开始时间 |
| end_time | int | 否 | | 结束时间 |

**调用示例**：
```
GET /api/snapshot?code_list=000001.SZ&begin_date=20240601&end_date=20240601
```

**响应示例**（股票快照）：
```json
{
  "data": {
    "000001.SZ": [
      {
        "code": "000001.SZ",
        "trade_time": "2024-06-01T09:30:03",
        "pre_close": 12.50,
        "last": 12.60,
        "open": 12.55,
        "high": 12.80,
        "low": 12.45,
        "close": 12.72,
        "volume": 50000.0,
        "amount": 630000.0,
        "num_trades": 120,
        "high_limited": 13.75,
        "low_limited": 11.25,
        "ask_price1": 12.73,
        "ask_volume1": 1000,
        "bid_price1": 12.72,
        "bid_volume1": 2000,
        "trading_phase_code": "T010..."
      }
    ]
  }
}
```

---

### 6. 财务报表

所有财务接口支持 `code_list`（必填）、`begin_date`（可选）、`end_date`（可选）。

#### 6.1 资产负债表

```
GET /api/finance/balance_sheet?code_list=000001.SZ&begin_date=20230101&end_date=20250601
```

#### 6.2 现金流量表

```
GET /api/finance/cash_flow?code_list=000001.SZ
```

#### 6.3 利润表

```
GET /api/finance/income?code_list=000001.SZ,600000.SH
```

#### 6.4 业绩快报

```
GET /api/finance/profit_express?code_list=000001.SZ
```

#### 6.5 业绩预告

```
GET /api/finance/forecast?code_list=000001.SZ
```

**响应示例**（资产负债表）：
```json
{
  "data": {
    "000001.SZ": [
      {
        "MARKET_CODE": "000001.SZ",
        "SECURITY_NAME": "平安银行",
        "STATEMENT_TYPE": 1,
        "REPORT_TYPE": 4,
        "REPORTING_PERIOD": "20231231",
        "ANN_DATE": "20240315",
        "TOTAL_ASSETS": 5580000000000.0,
        "TOTAL_LIAB": 5180000000000.0,
        "TOT_SHARE_EQUITY_INCL_MIN_INT": 400000000000.0
      }
    ]
  }
}
```

---

### 7. 股东股本

所有接口支持 `code_list`（必填）、`begin_date`（可选）、`end_date`（可选）。

| 接口 | 说明 |
|------|------|
| `/api/shareholder/top10` | 十大股东 |
| `/api/shareholder/count` | 股东人数 |
| `/api/shareholder/structure` | 股本结构 |
| `/api/shareholder/pledge` | 股权质押/冻结 |
| `/api/shareholder/restricted` | 限售股解禁 |

**调用示例**：
```
GET /api/shareholder/top10?code_list=000001.SZ&end_date=20240601
GET /api/shareholder/count?code_list=000001.SZ&begin_date=20200101
```

---

### 8. 股东权益

| 接口 | 说明 |
|------|------|
| `/api/corporate/dividend` | 分红送股记录 |
| `/api/corporate/allotment` | 配股记录 |

**调用示例**：
```
GET /api/corporate/dividend?code_list=000001.SZ&begin_date=20200101
```

---

### 9. 融资融券

| 接口 | 说明 |
|------|------|
| `/api/margin/trade` | 融资融券每日成交汇总 |
| `/api/margin/detail` | 融资融券每日交易明细 |

**调用示例**：
```
GET /api/margin/trade?code_list=000001.SZ&begin_date=20240601&end_date=20240630
```

---

### 10. 市场异动

| 接口 | 说明 |
|------|------|
| `/api/market/block_trade` | 大宗交易记录 |
| `/api/market/abnormal_trade` | 大额交易记录 |

**调用示例**：
```
GET /api/market/block_trade?code_list=000001.SZ&begin_date=20240101&end_date=20240601
```

---

### 11. ETF 数据

#### 11.1 ETF 列表

```
GET /api/etf/list
```

#### 11.2 ETF K 线

```
GET /api/etf/kline?code_list=510050.SH&begin_date=20240101&end_date=20240601&period=day
```
参数同 `/api/kline`。

#### 11.3 ETF 行情快照

```
GET /api/etf/snapshot?code_list=510050.SH&begin_date=20240601&end_date=20240601
```
参数同 `/api/snapshot`。

#### 11.4 ETF 每日申赎清单

```
GET /api/etf/daily_subscription?code_list=510050.SH&begin_date=20240601&end_date=20240630
```

#### 11.5 ETF 份额变动

```
GET /api/etf/share?code_list=510050.SH&begin_date=20240101&end_date=20240601
```

#### 11.6 ETF 每日 IOPV

```
GET /api/etf/iopv?code_list=510050.SH&begin_date=20240601&end_date=20240630
```

---

### 12. 申万指数

| 接口 | 说明 |
|------|------|
| `/api/index/shenwan/info` | 申万指数基本信息 |
| `/api/index/shenwan/component?code_list=801010.SH` | 申万指数成分股 |
| `/api/index/shenwan/weight?code_list=801010.SH` | 申万指数成分股权重 |
| `/api/index/shenwan/data?code_list=801010.SH&begin_date=20240101&end_date=20240601` | 申万指数行情 |

---

### 13. 行业指数

| 接口 | 说明 |
|------|------|
| `/api/index/industry/info` | 行业指数基本信息 |
| `/api/index/industry/component?code_list=801010.SH` | 行业指数成分股 |
| `/api/index/industry/weight?code_list=801010.SH` | 行业指数成分股权重 |
| `/api/index/industry/data?code_list=801010.SH&begin_date=20240101&end_date=20240601` | 行业指数行情 |

---

### 14. 可转债

所有接口支持 `code_list`（必填）、`begin_date`（可选）、`end_date`（可选）。

| 接口 | 说明 |
|------|------|
| `/api/cb/info` | 可转债基本信息 |
| `/api/cb/share` | 可转债份额变动 |
| `/api/cb/conversion` | 可转债转股数据 |
| `/api/cb/conversion_change` | 可转债转股变动 |
| `/api/cb/redemption` | 可转债赎回信息 |
| `/api/cb/putback` | 可转债回售信息 |
| `/api/cb/call` | 可转债回售价格 |
| `/api/cb/suspend` | 可转债停复牌信息 |

**调用示例**：
```
GET /api/cb/info?code_list=110043.SH
GET /api/cb/conversion?code_list=110043.SH&begin_date=20240101&end_date=20240601
```

---

### 15. 期权

所有接口支持 `code_list`（必填）、`begin_date`（可选）、`end_date`（可选）。

| 接口 | 说明 |
|------|------|
| `/api/option/info` | 期权基本信息 |
| `/api/option/contract` | 期权合约信息 |
| `/api/option/contract_change` | 期权合约变更 |

**调用示例**：
```
GET /api/option/info?code_list=510050C2406M02900.SH
```

---

### 16. 国债

```
GET /api/treasury?code_list=019666.SH&begin_date=20240101&end_date=20240601
```

---

## Node.js 调用示例

```javascript
const BASE_URL = "http://43.156.121.7:8000";  // 替换为实际地址

// 1. 获取 ETF 列表
const etfList = await fetch(`${BASE_URL}/api/etf/list`).then(r => r.json());
console.log(`共 ${etfList.count} 只 ETF`);

// 2. 获取平安银行日 K 线
const kline = await fetch(
  `${BASE_URL}/api/kline?code_list=000001.SZ&begin_date=20240601&end_date=20240630&period=day`
).then(r => r.json());
const records = kline.data["000001.SZ"];
records.forEach(bar => {
  console.log(`${bar.kline_time} O:${bar.open} H:${bar.high} L:${bar.low} C:${bar.close}`);
});

// 3. 获取资产负债表
const balance = await fetch(
  `${BASE_URL}/api/finance/balance_sheet?code_list=000001.SZ`
).then(r => r.json());

// 4. 获取 50ETF 日内5分钟 K 线
const etf5min = await fetch(
  `${BASE_URL}/api/etf/kline?code_list=510050.SH&begin_date=20240601&end_date=20240601&period=5min`
).then(r => r.json());

// 5. 获取若干股票的基本信息
const basicInfo = await fetch(
  `${BASE_URL}/api/security/basic?code_list=000001.SZ,600036.SH,601318.SH`
).then(r => r.json());

// 6. 获取 ETF IOPV
const iopv = await fetch(
  `${BASE_URL}/api/etf/iopv?code_list=510050.SH&begin_date=20240601&end_date=20240630`
).then(r => r.json());
```

---

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `PORT` | 服务端口 | `8000` |

可通过编辑 `config.py` 修改 SDK 连接参数（账号、IP、端口）。

---

## 项目结构

```
data-service/
├── main.py              # FastAPI 服务入口 + 所有 API 路由
├── sdk_client.py        # AmazingData SDK 封装层
├── config.py            # 配置（账号、IP、端口）
├── utils.py             # 缓存 + DataFrame 序列化工具
├── requirements.txt     # Python 依赖
├── Dockerfile           # Docker 构建文件
├── zeabur.json          # Zeabur 部署配置
├── zbpack.json          # Zeabur 容器化配置
├── .gitignore
└── lib/
    ├── tgw-1.0.8.7-py3-none-any.whl
    └── AmazingData-1.1.7-cp310-none-any.whl
```
