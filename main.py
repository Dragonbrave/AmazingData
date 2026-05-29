import os
import sys
import traceback
from contextlib import asynccontextmanager
from typing import List, Optional
from datetime import datetime
import uvicorn
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config import SERVICE_HOST, SERVICE_PORT
from sdk_client import client


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        client.login()
        print("AmazingData SDK 登录成功", file=sys.stderr)
    except Exception as e:
        print(f"AmazingData SDK 登录失败: {e}", file=sys.stderr)
        traceback.print_exc()
        print("服务将以降级模式运行（部分接口可能不可用）", file=sys.stderr)
    yield


app = FastAPI(title="AmazingData API Service", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== 工具函数 ====================

def _parse_code_list(code_list: str) -> List[str]:
    codes = [c.strip() for c in code_list.split(",") if c.strip()]
    if not codes:
        raise HTTPException(status_code=400, detail="code_list 不能为空")
    return codes


class KlineRequest(BaseModel):
    code_list: List[str]
    begin_date: int
    end_date: int
    period: str = "day"

class SnapshotRequest(BaseModel):
    code_list: List[str]
    begin_date: int
    end_date: int

class DividendRequest(BaseModel):
    code_list: List[str]
    begin_date: Optional[int] = None
    end_date: Optional[int] = None


# ==================== 健康检查 ====================

@app.get("/api/health")
def health():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


# ==================== 交易日历 ====================

@app.get("/api/calendar")
def get_calendar():
    calendar = client.get_calendar()
    return {"count": len(calendar), "calendar": calendar}


# ==================== 基础数据 ====================

@app.get("/api/security/list")
def get_security_list(
    security_type: str = Query(default="EXTRA_STOCK_A"),
):
    try:
        code_list = client.get_code_list(security_type=security_type)
        return {"count": len(code_list), "security_type": security_type, "code_list": code_list}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/security/info")
def get_security_info(
    security_type: str = Query(default="EXTRA_STOCK_A"),
):
    try:
        data = client.get_code_info(security_type=security_type)
        return {"count": len(data), "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/security/hist_list")
def get_hist_code_list(
    security_type: str = Query(default="EXTRA_STOCK_A_SH_SZ"),
    start_date: int = Query(default=20130101),
    end_date: Optional[int] = Query(default=None),
):
    try:
        code_list = client.get_hist_code_list(security_type=security_type, start_date=start_date, end_date=end_date)
        return {"count": len(code_list), "code_list": code_list}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/security/future_list")
def get_future_list(security_type: str = Query(default="ZJ_FUTURE")):
    try:
        code_list = client.get_future_code_list(security_type=security_type)
        return {"count": len(code_list), "code_list": code_list}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/security/option_list")
def get_option_list(security_type: str = Query(default="EXTRA_ETF_OP")):
    try:
        code_list = client.get_option_code_list(security_type=security_type)
        return {"count": len(code_list), "code_list": code_list}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/security/basic")
def get_stock_basic(code_list: str = Query(description="逗号分隔代码列表")):
    try:
        data = client.get_stock_basic(_parse_code_list(code_list))
        return {"count": len(data), "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/security/hist_status")
def get_history_stock_status(
    code_list: str = Query(),
    begin_date: Optional[int] = Query(default=None),
    end_date: Optional[int] = Query(default=None),
):
    try:
        data = client.get_history_stock_status(_parse_code_list(code_list), begin_date=begin_date, end_date=end_date)
        return {"count": len(data), "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/security/bj_code_mapping")
def get_bj_code_mapping():
    try:
        data = client.get_bj_code_mapping()
        return {"count": len(data), "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 复权因子 ====================

@app.get("/api/factor/backward")
def get_backward_factor(
    code_list: str = Query(),
    local_path: Optional[str] = Query(default=None),
    is_local: bool = Query(default=False),
):
    try:
        data = client.get_backward_factor(_parse_code_list(code_list), local_path=local_path, is_local=is_local)
        return {"count": len(data), "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/factor/adj")
def get_adj_factor(
    code_list: str = Query(),
    local_path: Optional[str] = Query(default=None),
    is_local: bool = Query(default=False),
):
    try:
        data = client.get_adj_factor(_parse_code_list(code_list), local_path=local_path, is_local=is_local)
        return {"count": len(data), "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 行情数据 ====================

@app.get("/api/kline")
def get_kline(
    code_list: str = Query(),
    begin_date: int = Query(),
    end_date: int = Query(),
    period: str = Query(default="day"),
    begin_time: Optional[int] = Query(default=None),
    end_time: Optional[int] = Query(default=None),
):
    try:
        data = client.query_kline(
            _parse_code_list(code_list),
            begin_date=begin_date, end_date=end_date, period=period,
            begin_time=begin_time, end_time=end_time,
        )
        return {"data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/snapshot")
def get_snapshot(
    code_list: str = Query(),
    begin_date: int = Query(),
    end_date: int = Query(),
    begin_time: Optional[int] = Query(default=None),
    end_time: Optional[int] = Query(default=None),
):
    try:
        data = client.query_snapshot(
            _parse_code_list(code_list),
            begin_date=begin_date, end_date=end_date,
            begin_time=begin_time, end_time=end_time,
        )
        return {"data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 财务报表 ====================

@app.get("/api/finance/balance_sheet")
def get_balance_sheet(
    code_list: str = Query(),
    begin_date: Optional[int] = Query(default=None),
    end_date: Optional[int] = Query(default=None),
):
    try:
        data = client.get_balance_sheet(_parse_code_list(code_list), begin_date=begin_date, end_date=end_date)
        return {"data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/finance/cash_flow")
def get_cash_flow(
    code_list: str = Query(),
    begin_date: Optional[int] = Query(default=None),
    end_date: Optional[int] = Query(default=None),
):
    try:
        data = client.get_cash_flow(_parse_code_list(code_list), begin_date=begin_date, end_date=end_date)
        return {"data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/finance/income")
def get_income(
    code_list: str = Query(),
    begin_date: Optional[int] = Query(default=None),
    end_date: Optional[int] = Query(default=None),
):
    try:
        data = client.get_income(_parse_code_list(code_list), begin_date=begin_date, end_date=end_date)
        return {"data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/finance/profit_express")
def get_profit_express(
    code_list: str = Query(),
    begin_date: Optional[int] = Query(default=None),
    end_date: Optional[int] = Query(default=None),
):
    try:
        data = client.get_profit_express(_parse_code_list(code_list), begin_date=begin_date, end_date=end_date)
        return {"count": len(data), "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/finance/forecast")
def get_forecast(
    code_list: str = Query(),
    begin_date: Optional[int] = Query(default=None),
    end_date: Optional[int] = Query(default=None),
):
    try:
        data = client.get_forecast(_parse_code_list(code_list), begin_date=begin_date, end_date=end_date)
        return {"count": len(data), "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 股东股本 ====================

@app.get("/api/shareholder/top10")
def get_top10_holder(
    code_list: str = Query(),
    begin_date: Optional[int] = Query(default=None),
    end_date: Optional[int] = Query(default=None),
):
    try:
        data = client.get_top10_holder(_parse_code_list(code_list), begin_date=begin_date, end_date=end_date)
        return {"count": len(data), "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/shareholder/count")
def get_shareholder_num(
    code_list: str = Query(),
    begin_date: Optional[int] = Query(default=None),
    end_date: Optional[int] = Query(default=None),
):
    try:
        data = client.get_shareholder_num(_parse_code_list(code_list), begin_date=begin_date, end_date=end_date)
        return {"count": len(data), "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/shareholder/structure")
def get_share_structure(
    code_list: str = Query(),
    begin_date: Optional[int] = Query(default=None),
    end_date: Optional[int] = Query(default=None),
):
    try:
        data = client.get_share_structure(_parse_code_list(code_list), begin_date=begin_date, end_date=end_date)
        return {"count": len(data), "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/shareholder/pledge")
def get_pledge_info(
    code_list: str = Query(),
    begin_date: Optional[int] = Query(default=None),
    end_date: Optional[int] = Query(default=None),
):
    try:
        data = client.get_pledge_info(_parse_code_list(code_list), begin_date=begin_date, end_date=end_date)
        return {"count": len(data), "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/shareholder/restricted")
def get_restricted_share(
    code_list: str = Query(),
    begin_date: Optional[int] = Query(default=None),
    end_date: Optional[int] = Query(default=None),
):
    try:
        data = client.get_restricted_share(_parse_code_list(code_list), begin_date=begin_date, end_date=end_date)
        return {"count": len(data), "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 股东权益 ====================

@app.get("/api/corporate/dividend")
def get_dividend(
    code_list: str = Query(),
    begin_date: Optional[int] = Query(default=None),
    end_date: Optional[int] = Query(default=None),
):
    try:
        data = client.get_dividend(_parse_code_list(code_list), begin_date=begin_date, end_date=end_date)
        return {"count": len(data), "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/corporate/allotment")
def get_allotment(
    code_list: str = Query(),
    begin_date: Optional[int] = Query(default=None),
    end_date: Optional[int] = Query(default=None),
):
    try:
        data = client.get_allotment(_parse_code_list(code_list), begin_date=begin_date, end_date=end_date)
        return {"count": len(data), "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 融资融券 ====================

@app.get("/api/margin/trade")
def get_margin_trade(
    code_list: str = Query(),
    begin_date: Optional[int] = Query(default=None),
    end_date: Optional[int] = Query(default=None),
):
    try:
        data = client.get_margin_trade(_parse_code_list(code_list), begin_date=begin_date, end_date=end_date)
        return {"count": len(data), "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/margin/detail")
def get_margin_detail(
    code_list: str = Query(),
    begin_date: Optional[int] = Query(default=None),
    end_date: Optional[int] = Query(default=None),
):
    try:
        data = client.get_margin_detail(_parse_code_list(code_list), begin_date=begin_date, end_date=end_date)
        return {"count": len(data), "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 市场异动 ====================

@app.get("/api/market/block_trade")
def get_block_trade(
    code_list: str = Query(),
    begin_date: Optional[int] = Query(default=None),
    end_date: Optional[int] = Query(default=None),
):
    try:
        data = client.get_block_trade(_parse_code_list(code_list), begin_date=begin_date, end_date=end_date)
        return {"count": len(data), "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/market/abnormal_trade")
def get_abnormal_trade(
    code_list: str = Query(),
    begin_date: Optional[int] = Query(default=None),
    end_date: Optional[int] = Query(default=None),
):
    try:
        data = client.get_abnormal_trade(_parse_code_list(code_list), begin_date=begin_date, end_date=end_date)
        return {"count": len(data), "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== ETF ====================

@app.get("/api/etf/list")
def get_etf_list():
    try:
        code_list = client.get_code_list(security_type="EXTRA_ETF")
        return {"count": len(code_list), "code_list": code_list}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/etf/kline")
def get_etf_kline(
    code_list: str = Query(),
    begin_date: int = Query(),
    end_date: int = Query(),
    period: str = Query(default="day"),
):
    return get_kline(code_list=code_list, begin_date=begin_date, end_date=end_date, period=period)


@app.get("/api/etf/snapshot")
def get_etf_snapshot(
    code_list: str = Query(),
    begin_date: int = Query(),
    end_date: int = Query(),
):
    return get_snapshot(code_list=code_list, begin_date=begin_date, end_date=end_date)


@app.get("/api/etf/daily_subscription")
def get_etf_daily_subscription(
    code_list: str = Query(),
    begin_date: Optional[int] = Query(default=None),
    end_date: Optional[int] = Query(default=None),
):
    try:
        data = client.get_etf_daily_subscription(_parse_code_list(code_list), begin_date=begin_date, end_date=end_date)
        return {"count": len(data), "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/etf/share")
def get_etf_share(
    code_list: str = Query(),
    begin_date: Optional[int] = Query(default=None),
    end_date: Optional[int] = Query(default=None),
):
    try:
        data = client.get_etf_share(_parse_code_list(code_list), begin_date=begin_date, end_date=end_date)
        return {"count": len(data), "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/etf/iopv")
def get_etf_iopv(
    code_list: str = Query(),
    begin_date: Optional[int] = Query(default=None),
    end_date: Optional[int] = Query(default=None),
):
    try:
        data = client.get_etf_iopv(_parse_code_list(code_list), begin_date=begin_date, end_date=end_date)
        return {"count": len(data), "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 申万指数 ====================

@app.get("/api/index/shenwan/info")
def get_shenwan_index_info():
    try:
        data = client.get_shenwan_index_info()
        return {"count": len(data), "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/index/shenwan/component")
def get_shenwan_index_component(code_list: str = Query()):
    try:
        data = client.get_shenwan_index_component(_parse_code_list(code_list))
        return {"count": len(data), "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/index/shenwan/weight")
def get_shenwan_index_component_weight(code_list: str = Query()):
    try:
        data = client.get_shenwan_index_component_weight(_parse_code_list(code_list))
        return {"count": len(data), "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/index/shenwan/data")
def get_shenwan_index_data(
    code_list: str = Query(),
    begin_date: Optional[int] = Query(default=None),
    end_date: Optional[int] = Query(default=None),
):
    try:
        data = client.get_shenwan_index_data(_parse_code_list(code_list), begin_date=begin_date, end_date=end_date)
        return {"count": len(data), "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 行业指数 ====================

@app.get("/api/index/industry/info")
def get_industry_index_info():
    try:
        data = client.get_industry_index_info()
        return {"count": len(data), "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/index/industry/component")
def get_industry_index_component(code_list: str = Query()):
    try:
        data = client.get_industry_index_component(_parse_code_list(code_list))
        return {"count": len(data), "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/index/industry/weight")
def get_industry_index_component_weight(code_list: str = Query()):
    try:
        data = client.get_industry_index_component_weight(_parse_code_list(code_list))
        return {"count": len(data), "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/index/industry/data")
def get_industry_index_data(
    code_list: str = Query(),
    begin_date: Optional[int] = Query(default=None),
    end_date: Optional[int] = Query(default=None),
):
    try:
        data = client.get_industry_index_data(_parse_code_list(code_list), begin_date=begin_date, end_date=end_date)
        return {"count": len(data), "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 可转债 ====================

@app.get("/api/cb/info")
def get_cb_info(
    code_list: str = Query(),
    begin_date: Optional[int] = Query(default=None),
    end_date: Optional[int] = Query(default=None),
):
    try:
        data = client.get_cb_info(_parse_code_list(code_list), begin_date=begin_date, end_date=end_date)
        return {"count": len(data), "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/cb/share")
def get_cb_share(
    code_list: str = Query(),
    begin_date: Optional[int] = Query(default=None),
    end_date: Optional[int] = Query(default=None),
):
    try:
        data = client.get_cb_share(_parse_code_list(code_list), begin_date=begin_date, end_date=end_date)
        return {"count": len(data), "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/cb/conversion")
def get_cb_conversion(
    code_list: str = Query(),
    begin_date: Optional[int] = Query(default=None),
    end_date: Optional[int] = Query(default=None),
):
    try:
        data = client.get_cb_conversion(_parse_code_list(code_list), begin_date=begin_date, end_date=end_date)
        return {"count": len(data), "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/cb/conversion_change")
def get_cb_conversion_change(
    code_list: str = Query(),
    begin_date: Optional[int] = Query(default=None),
    end_date: Optional[int] = Query(default=None),
):
    try:
        data = client.get_cb_conversion_change(_parse_code_list(code_list), begin_date=begin_date, end_date=end_date)
        return {"count": len(data), "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/cb/redemption")
def get_cb_redemption(
    code_list: str = Query(),
    begin_date: Optional[int] = Query(default=None),
    end_date: Optional[int] = Query(default=None),
):
    try:
        data = client.get_cb_redemption(_parse_code_list(code_list), begin_date=begin_date, end_date=end_date)
        return {"count": len(data), "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/cb/putback")
def get_cb_putback(
    code_list: str = Query(),
    begin_date: Optional[int] = Query(default=None),
    end_date: Optional[int] = Query(default=None),
):
    try:
        data = client.get_cb_putback(_parse_code_list(code_list), begin_date=begin_date, end_date=end_date)
        return {"count": len(data), "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/cb/call")
def get_cb_call(
    code_list: str = Query(),
    begin_date: Optional[int] = Query(default=None),
    end_date: Optional[int] = Query(default=None),
):
    try:
        data = client.get_cb_call(_parse_code_list(code_list), begin_date=begin_date, end_date=end_date)
        return {"count": len(data), "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/cb/suspend")
def get_cb_suspend(
    code_list: str = Query(),
    begin_date: Optional[int] = Query(default=None),
    end_date: Optional[int] = Query(default=None),
):
    try:
        data = client.get_cb_suspend(_parse_code_list(code_list), begin_date=begin_date, end_date=end_date)
        return {"count": len(data), "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 期权 ====================

@app.get("/api/option/info")
def get_option_info(
    code_list: str = Query(),
    begin_date: Optional[int] = Query(default=None),
    end_date: Optional[int] = Query(default=None),
):
    try:
        data = client.get_option_info(_parse_code_list(code_list), begin_date=begin_date, end_date=end_date)
        return {"count": len(data), "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/option/contract")
def get_option_contract(
    code_list: str = Query(),
    begin_date: Optional[int] = Query(default=None),
    end_date: Optional[int] = Query(default=None),
):
    try:
        data = client.get_option_contract(_parse_code_list(code_list), begin_date=begin_date, end_date=end_date)
        return {"count": len(data), "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/option/contract_change")
def get_option_contract_change(
    code_list: str = Query(),
    begin_date: Optional[int] = Query(default=None),
    end_date: Optional[int] = Query(default=None),
):
    try:
        data = client.get_option_contract_change(_parse_code_list(code_list), begin_date=begin_date, end_date=end_date)
        return {"count": len(data), "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 国债 ====================

@app.get("/api/treasury")
def get_treasury(
    code_list: str = Query(),
    begin_date: Optional[int] = Query(default=None),
    end_date: Optional[int] = Query(default=None),
):
    try:
        data = client.get_treasury(_parse_code_list(code_list), begin_date=begin_date, end_date=end_date)
        return {"count": len(data), "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", SERVICE_PORT))
    uvicorn.run(app, host=SERVICE_HOST, port=port, log_level="info")
