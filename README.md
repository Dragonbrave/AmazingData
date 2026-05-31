# AmazingData API Service

基于中国银河证券「星耀数智」AmazingData SDK 封装的 REST API 数据服务，为 Node.js 或其他语言开发的 App 提供 A 股、ETF、可转债、期权、指数等金融市场数据。

---

## 架构

```
Zeabur (ETF 应用) ──HTTP──► 腾讯云 VPS (AmazingData SDK + FastAPI)
```

ETF 应用部署在 Zeabur，通过 HTTP 调用 VPS 上的 SDK 数据服务。

---

## 部署

### 在腾讯云 VPS 上部署（推荐）

#### 前置条件

- 腾讯云轻量应用服务器（推荐 2核2G 以上）
- Ubuntu 22.04 + Docker 预装镜像
- 公网 IP + 防火墙放行 8080 端口（TCP）

#### 部署步骤

```bash
# 1. SSH 登录 VPS
ssh root@<公网IP>

# 2. 安装 swap（2G 内存必须）
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# 3. 下载代码
cd /home/ubuntu
wget -q https://ghfast.top/https://github.com/Dragonbrave/AmazingData/archive/refs/heads/main.zip -O AmazingData.zip
unzip AmazingData.zip
mv AmazingData-main AmazingData
rm AmazingData.zip

# 4. 构建并启动
cd AmazingData
sudo docker build --no-cache -t amazingdata-sdk .
sudo docker run -d \
  --name amazingdata \
  --restart unless-stopped \
  -p 8080:8000 \
  amazingdata-sdk

# 5. 验证
curl http://localhost:8080/health
curl "http://localhost:8080/api/calendar"
```

#### 防火墙配置

在腾讯云控制台 → 轻量应用服务器 → 防火墙，添加规则：

| 协议 | 端口 | 来源 | 策略 |
|------|------|------|------|
| TCP | 22 | 0.0.0.0/0 | 允许 |
| TCP | 8080 | 0.0.0.0/0 | 允许 |
| ICMP | ALL | 0.0.0.0/0 | 允许 |

**不要开放全部 TCP 端口！** 只开 22（SSH）和 8080（API）。

### Docker 部署（通用）

```bash
docker build -t amazingdata-sdk .
docker run -d \
  --name amazingdata \
  --restart unless-stopped \
  -p 8080:8000 \
  amazingdata-sdk
```

### 本地调试

```bash
# 1. 安装 whl 包
pip install lib/tgw-1.0.8.7-py3-none-any.whl
pip install lib/AmazingData-1.1.7-cp311-none-any.whl

# 2. 安装依赖
pip install -r requirements.txt

# 3. 启动
python main.py
# 服务运行在 http://0.0.0.0:8000
```

---

## API 调用

### 基础地址

```
http://<服务器IP>:8080
```

例如：`http://175.178.44.32:8080`

### 通用说明

所有接口均为 `GET` 请求，参数通过 URL Query String 传递。

#### 代码格式 (code_list)

多只证券代码用**英文逗号**分隔，格式为 `代码.市场后缀`：

| 市场 | 后缀 | 示例 |
|------|------|------|
| 上交所 | `.SH` | `600000.SH`，`510050.SH` |
| 深交所 | `.SZ` | `000001.SZ`，`159915.SZ` |
| 北交所 | `.BJ` | `838402.BJ` |
| 中金所(期货) | `.CFE` | `IF2401.CFE` |

#### 日期格式 (begin_date / end_date)

`int` 类型，格式 `YYYYMMDD`，例如 `20240601` 表示 2024年6月1日。

#### 时间格式 (begin_time / end_time)

K线和快照接口可选参数，`int` 类型。不同接口数值不同：

- **快照接口**：`90000000`（9:00），`172500000`（17:25）
- **K线接口**：`900`（9:00），`1725`（17:25）

### 快速测试

```bash
# 健康检查
curl http://<服务器IP>:8080/health

# 交易日历
curl "http://<服务器IP>:8080/api/calendar"

# A股列表
curl "http://<服务器IP>:8080/api/security/list?security_type=EXTRA_STOCK_A"

# K线数据（贵州茅台）
curl "http://<服务器IP>:8080/api/kline?code_list=600519.SH&begin_date=20260501&end_date=20260529"

# ETF列表
curl "http://<服务器IP>:8080/api/etf/list"

# 行情快照
curl "http://<服务器IP>:8080/api/snapshot?code_list=600519.SH&begin_date=20260528&end_date=20260529"
```

---

## API 接口

### 1. 健康检查

```
GET /health
GET /ready
GET /api/health
```

**响应示例**：
```json
{
  "status": "ok",
  "timestamp": "2026-05-30T15:44:08.209124"
}
```

---

### 2. 交易日历

```
GET /api/calendar
```

**响应示例**：
```json
{
  "count": 8650,
  "calendar": [19901219, 19901220, ..., 20260529]
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

---

#### 3.4 获取证券基本信息

```
GET /api/security/basic?code_list=000001.SZ,600000.SH
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| code_list | str | 是 | 逗号分隔代码列表 |

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

**period 取值**：`1min` / `3min` / `5min` / `10min` / `15min` / `30min` / `60min` / `120min` / `day` / `week` / `month` / `season` / `year`

**调用示例**：
```
GET /api/kline?code_list=000001.SZ,600000.SH&begin_date=20240601&end_date=20240630&period=day
GET /api/kline?code_list=510050.SH&begin_date=20240601&end_date=20240607&period=5min
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

---

### 6. 财务报表

所有财务接口支持 `code_list`（必填）、`begin_date`（可选）、`end_date`（可选）。

| 接口 | 说明 |
|------|------|
| `/api/finance/balance_sheet` | 资产负债表 |
| `/api/finance/cash_flow` | 现金流量表 |
| `/api/finance/income` | 利润表 |
| `/api/finance/profit_express` | 业绩快报 |
| `/api/finance/forecast` | 业绩预告 |

---

### 7. 股东股本

| 接口 | 说明 |
|------|------|
| `/api/shareholder/top10` | 十大股东 |
| `/api/shareholder/count` | 股东人数 |
| `/api/shareholder/structure` | 股本结构 |
| `/api/shareholder/pledge` | 股权质押/冻结 |
| `/api/shareholder/restricted` | 限售股解禁 |

---

### 8. 股东权益

| 接口 | 说明 |
|------|------|
| `/api/corporate/dividend` | 分红送股记录 |
| `/api/corporate/allotment` | 配股记录 |

---

### 9. 融资融券

| 接口 | 说明 |
|------|------|
| `/api/margin/trade` | 融资融券每日成交汇总 |
| `/api/margin/detail` | 融资融券每日交易明细 |

---

### 10. 市场异动

| 接口 | 说明 |
|------|------|
| `/api/market/block_trade` | 大宗交易记录 |
| `/api/market/abnormal_trade` | 大额交易记录 |
| `/api/market/long_hu_bang` | 龙虎榜 |

**调用示例**：
```
GET /api/market/block_trade?code_list=000001.SZ&begin_date=20240101&end_date=20240601
```

---

### 11. ETF 数据

| 接口 | 说明 |
|------|------|
| `/api/etf/list` | ETF 列表 |
| `/api/etf/kline` | ETF K 线（参数同 /api/kline） |
| `/api/etf/snapshot` | ETF 行情快照（参数同 /api/snapshot） |
| `/api/etf/daily_subscription` | ETF 每日申赎清单 |
| `/api/etf/share` | ETF 份额变动 |
| `/api/etf/nav` | ETF 基金净值 |
| `/api/etf/iopv` | ETF 每日 IOPV |

---

### 12. 申万指数

| 接口 | 说明 |
|------|------|
| `/api/index/shenwan/info` | 申万指数基本信息 |
| `/api/index/shenwan/component` | 申万指数成分股 |
| `/api/index/shenwan/weight` | 申万指数成分股权重 |
| `/api/index/shenwan/data` | 申万指数行情 |

---

### 13. 行业指数

| 接口 | 说明 |
|------|------|
| `/api/index/industry/info` | 行业指数基本信息 |
| `/api/index/industry/component` | 行业指数成分股 |
| `/api/index/industry/weight` | 行业指数成分股权重 |
| `/api/index/industry/data` | 行业指数行情 |

---

### 14. 可转债

| 接口 | 说明 |
|------|------|
| `/api/cb/info` | 可转债基本信息 |
| `/api/cb/share` | 可转债份额变动 |
| `/api/cb/conversion` | 可转债转股数据 |
| `/api/cb/conversion_change` | 可转债转股变动 |
| `/api/cb/correction` | 可转债修正数据 |
| `/api/cb/redemption` | 可转债赎回信息 |
| `/api/cb/putback` | 可转债回售信息 |
| `/api/cb/put_call_item` | 可转债回售赎回条款 |
| `/api/cb/put_explanation` | 可转债回售条款执行说明 |
| `/api/cb/call_explanation` | 可转债赎回条款执行说明 |
| `/api/cb/call` | 可转债回售价格 |
| `/api/cb/suspend` | 可转债停复牌信息 |

---

### 15. 期权

| 接口 | 说明 |
|------|------|
| `/api/option/info` | 期权基本信息 |
| `/api/option/contract` | 期权合约信息 |
| `/api/option/contract_change` | 期权合约变更 |
| `/api/option/std_ctr_specs` | 期权标准合约属性 |
| `/api/option/mon_ctr_specs` | 期权月合约属性变动 |

---

### 16. 国债

```
GET /api/treasury?code_list=019666.SH&begin_date=20240101&end_date=20240601
```

---

## Node.js 调用示例

```javascript
const BASE_URL = "http://175.178.44.32:8080";  // 替换为实际 VPS 地址

// 1. 健康检查
const health = await fetch(`${BASE_URL}/health`).then(r => r.json());
console.log(health.status);  // "ok"

// 2. 获取 ETF 列表
const etfList = await fetch(`${BASE_URL}/api/etf/list`).then(r => r.json());
console.log(`共 ${etfList.count} 只 ETF`);

// 3. 获取平安银行日 K 线
const kline = await fetch(
  `${BASE_URL}/api/kline?code_list=000001.SZ&begin_date=20240601&end_date=20240630&period=day`
).then(r => r.json());
const records = kline.data["000001.SZ"];
records.forEach(bar => {
  console.log(`${bar.kline_time} O:${bar.open} H:${bar.high} L:${bar.low} C:${bar.close}`);
});

// 4. 获取资产负债表
const balance = await fetch(
  `${BASE_URL}/api/finance/balance_sheet?code_list=000001.SZ`
).then(r => r.json());

// 5. 获取 50ETF 日内5分钟 K 线
const etf5min = await fetch(
  `${BASE_URL}/api/etf/kline?code_list=510050.SH&begin_date=20240601&end_date=20240601&period=5min`
).then(r => r.json());

// 6. 获取若干股票的基本信息
const basicInfo = await fetch(
  `${BASE_URL}/api/security/basic?code_list=000001.SZ,600036.SH,601318.SH`
).then(r => r.json());

// 7. 获取 ETF IOPV
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
AmazingData/
├── main.py              # FastAPI 服务入口 + 所有 API 路由
├── sdk_client.py        # AmazingData SDK 封装层
├── config.py            # 配置（账号、IP、端口）
├── utils.py             # 缓存 + DataFrame 序列化工具
├── requirements.txt     # Python 依赖
├── Dockerfile           # Docker 构建文件
├── zbpack.json          # Zeabur 容器化配置
├── .gitignore
└── lib/
    ├── tgw-1.0.8.7-py3-none-any.whl
    └── AmazingData-1.1.7-cp311-none-any.whl
```

---

## 服务器维护与迁移指南

### 当前部署信息

| 项目 | 值 |
|------|-----|
| 服务器 | 腾讯云轻量应用服务器 |
| 公网 IP | `175.178.44.32` |
| 端口 | `8080` |
| 镜像 | Ubuntu 22.04 + Docker 26 |
| 容器 | `amazingdata`（自动重启） |
| Swap | 2GB |

### 注意事项

#### 1. 服务器到期处理

腾讯云轻量应用服务器有使用期限（当前 1 个月）。到期前需要：

- **续费**：在腾讯云控制台续费，保留同一台服务器
- **或迁移**：购买新服务器，按下方步骤迁移

#### 2. 服务器迁移步骤

当需要迁移到新服务器时：

```bash
# === 在旧服务器上 ===
# 1. 导出 Docker 镜像
sudo docker save amazingdata-sdk -o /tmp/amazingdata-sdk.tar

# 2. 传输到新服务器
scp /tmp/amazingdata-sdk.tar root@<新服务器IP>:/tmp/

# === 在新服务器上 ===
# 3. 安装 Docker（如果没有预装）
curl -fsSL https://get.docker.com | sh

# 4. 添加 swap
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# 5. 导入镜像并启动
sudo docker load -i /tmp/amazingdata-sdk.tar
sudo docker run -d \
  --name amazingdata \
  --restart unless-stopped \
  -p 8080:8000 \
  amazingdata-sdk

# 6. 验证
curl http://localhost:8080/health
```

#### 3. 更新 ETF 应用的 API 地址

迁移后需要更新 ETF 应用中的 API 地址：

```
旧地址：http://175.178.44.32:8080
新地址：http://<新服务器IP>:8080
```

#### 4. 防火墙规则

新服务器需要重新配置防火墙：

| 协议 | 端口 | 来源 | 策略 |
|------|------|------|------|
| TCP | 22 | 0.0.0.0/0 | 允许 |
| TCP | 8080 | 0.0.0.0/0 | 允许 |
| ICMP | ALL | 0.0.0.0/0 | 允许 |

#### 5. 数据持久化

- 本服务**无状态**，不保存本地数据
- 所有数据通过 SDK 实时从 AmazingData 服务器获取
- 迁移时只需迁移 Docker 镜像，无需迁移数据

#### 6. 代码更新

如果本地代码有更新：

```bash
# 在 VPS 上
cd /home/ubuntu/AmazingData
# 重新下载最新代码
rm -rf AmazingData
wget -q https://ghfast.top/https://github.com/Dragonbrave/AmazingData/archive/refs/heads/main.zip -O AmazingData.zip
unzip AmazingData.zip && mv AmazingData-main AmazingData && rm AmazingData.zip
cd AmazingData

# 重建并重启
sudo docker stop amazingdata && sudo docker rm amazingdata
sudo docker build --no-cache -t amazingdata-sdk .
sudo docker run -d \
  --name amazingdata \
  --restart unless-stopped \
  -p 8080:8000 \
  amazingdata-sdk
```

#### 7. 监控

定期检查服务状态：

```bash
# 查看容器状态
sudo docker ps

# 查看日志
sudo docker logs amazingdata --tail 50

# 查看内存使用
free -h

# 测试接口
curl http://localhost:8080/health
```

#### 8. 故障排查

| 问题 | 解决方案 |
|------|----------|
| 容器退出 | `sudo docker restart amazingdata` |
| 接口 500 错误 | `sudo docker logs amazingdata --tail 50` 查看日志 |
| 内存不足 | 检查 swap 是否启用，或升级配置 |
| 连接超时 | 检查防火墙是否放行 8080 端口 |
| SDK 登录失败 | 检查 config.py 中的账号密码和服务器地址 |

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
| `/api/market/long_hu_bang` | 龙虎榜 |

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

#### 11.7 ETF 基金净值

```
GET /api/etf/nav?code_list=510050.SH&begin_date=20240601&end_date=20240630
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
| `/api/cb/correction` | 可转债修正数据 |
| `/api/cb/redemption` | 可转债赎回信息 |
| `/api/cb/putback` | 可转债回售信息 |
| `/api/cb/put_call_item` | 可转债回售赎回条款 |
| `/api/cb/put_explanation` | 可转债回售条款执行说明 |
| `/api/cb/call_explanation` | 可转债赎回条款执行说明 |
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
| `/api/option/std_ctr_specs` | 期权标准合约属性 |
| `/api/option/mon_ctr_specs` | 期权月合约属性变动 |

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
