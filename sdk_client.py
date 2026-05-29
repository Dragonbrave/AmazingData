from typing import List, Dict, Optional, Union
import pandas as pd
import AmazingData as ad
from AmazingData.utils.constant import Period

from config import (
    AMAZINGDATA_USERNAME,
    AMAZINGDATA_PASSWORD,
    AMAZINGDATA_HOST,
    AMAZINGDATA_PORT,
    CACHE_TTL_SECONDS,
    CALENDAR_CACHE_TTL,
)
from utils import cache, cached, df_to_records


class AmazingDataClient:

    def __init__(self):
        self._logged_in = False
        self._calendar = None

    # ==================== 登录 ====================

    def login(self):
        if self._logged_in:
            return
        print(f"正在连接 AmazingData SDK (host={AMAZINGDATA_HOST}:{AMAZINGDATA_PORT}) ...")
        ad.login(
            username=AMAZINGDATA_USERNAME,
            password=AMAZINGDATA_PASSWORD,
            host=AMAZINGDATA_HOST,
            port=AMAZINGDATA_PORT,
        )
        self._logged_in = True
        print(f"AmazingData SDK 登录成功 (host={AMAZINGDATA_HOST}:{AMAZINGDATA_PORT})")

    # ==================== 基础数据 ====================

    def get_calendar(self) -> List[int]:
        if self._calendar is not None:
            return self._calendar
        self._calendar = ad.BaseData().get_calendar()
        return self._calendar

    def get_code_list(self, security_type: str = "EXTRA_STOCK_A") -> List[str]:
        return ad.BaseData().get_code_list(security_type=security_type)

    def get_code_info(self, security_type: str = "EXTRA_STOCK_A") -> list:
        df = ad.BaseData().get_code_info(security_type=security_type)
        return df_to_records(df)

    def get_hist_code_list(
        self,
        security_type: str = "EXTRA_STOCK_A_SH_SZ",
        start_date: int = 20130101,
        end_date: Optional[int] = None,
        local_path: Optional[str] = None,
    ) -> List[str]:
        if end_date is None:
            end_date = self.get_calendar()[-1]
        kwargs = {}
        if local_path:
            kwargs["local_path"] = local_path
        return ad.BaseData().get_hist_code_list(
            security_type=security_type, start_date=start_date, end_date=end_date, **kwargs
        )

    def get_future_code_list(self, security_type: str = "ZJ_FUTURE") -> List[str]:
        return ad.BaseData().get_future_code_list(security_type=security_type)

    def get_option_code_list(self, security_type: str = "EXTRA_ETF_OP") -> List[str]:
        return ad.BaseData().get_option_code_list(security_type=security_type)

    def get_backward_factor(
        self,
        code_list: List[str],
        local_path: Optional[str] = None,
        is_local: bool = False,
    ) -> list:
        return df_to_records(ad.BaseData().get_backward_factor(
            code_list, local_path=local_path, is_local=is_local
        ))

    def get_adj_factor(
        self,
        code_list: List[str],
        local_path: Optional[str] = None,
        is_local: bool = False,
    ) -> list:
        return df_to_records(ad.BaseData().get_adj_factor(
            code_list, local_path=local_path, is_local=is_local
        ))

    def get_bj_code_mapping(
        self,
        local_path: Optional[str] = None,
        is_local: bool = False,
    ) -> list:
        return df_to_records(ad.InfoData().get_bj_code_mapping(
            local_path=local_path, is_local=is_local
        ))

    # ==================== 行情数据 ====================

    PERIOD_MAP = {
        "1min": Period.min1.value, "3min": Period.min3.value, "5min": Period.min5.value,
        "10min": Period.min10.value, "15min": Period.min15.value, "30min": Period.min30.value,
        "60min": Period.min60.value, "120min": Period.min120.value,
        "day": Period.day.value, "week": Period.week.value,
        "month": Period.month.value, "season": Period.season.value, "year": Period.year.value,
    }

    def query_kline(
        self, code_list: List[str], begin_date: int, end_date: int,
        period: str = "day", begin_time: Optional[int] = None, end_time: Optional[int] = None,
    ) -> Dict[str, list]:
        p = self.PERIOD_MAP.get(period, Period.day.value)
        calendar = self.get_calendar()
        market_data = ad.MarketData(calendar)
        kwargs = {}
        if begin_time is not None:
            kwargs["begin_time"] = begin_time
        if end_time is not None:
            kwargs["end_time"] = end_time
        result = market_data.query_kline(code_list, begin_date=begin_date, end_date=end_date, period=p, **kwargs)
        return {code: df_to_records(df) for code, df in result.items()}

    def query_snapshot(
        self, code_list: List[str], begin_date: int, end_date: int,
        begin_time: Optional[int] = None, end_time: Optional[int] = None,
    ) -> Dict[str, list]:
        calendar = self.get_calendar()
        market_data = ad.MarketData(calendar)
        kwargs = {}
        if begin_time is not None:
            kwargs["begin_time"] = begin_time
        if end_time is not None:
            kwargs["end_time"] = end_time
        result = market_data.query_snapshot(code_list, begin_date=begin_date, end_date=end_date, **kwargs)
        return {code: df_to_records(df) for code, df in result.items()}

    # ==================== 证券基本信息 ====================

    def get_stock_basic(self, code_list: List[str]) -> list:
        return df_to_records(ad.InfoData().get_stock_basic(code_list))

    def get_history_stock_status(
        self, code_list: List[str],
        local_path: Optional[str] = None, is_local: bool = False,
        begin_date: Optional[int] = None, end_date: Optional[int] = None,
    ) -> list:
        kwargs = {}
        if local_path:
            kwargs["local_path"] = local_path
        if not is_local:
            kwargs["is_local"] = is_local
        if begin_date:
            kwargs["begin_date"] = begin_date
        if end_date:
            kwargs["end_date"] = end_date
        return df_to_records(ad.InfoData().get_history_stock_status(code_list, **kwargs))

    # ==================== 财务报表 ====================

    def get_balance_sheet(
        self, code_list: List[str],
        local_path: Optional[str] = None, is_local: bool = False,
        begin_date: Optional[int] = None, end_date: Optional[int] = None,
    ) -> Dict[str, list]:
        kwargs = {}
        if local_path:
            kwargs["local_path"] = local_path
        if not is_local:
            kwargs["is_local"] = is_local
        if begin_date:
            kwargs["begin_date"] = begin_date
        if end_date:
            kwargs["end_date"] = end_date
        result = ad.InfoData().get_balance_sheet(code_list, **kwargs)
        return {code: df_to_records(df) for code, df in result.items()}

    def get_cash_flow(
        self, code_list: List[str],
        local_path: Optional[str] = None, is_local: bool = False,
        begin_date: Optional[int] = None, end_date: Optional[int] = None,
    ) -> Dict[str, list]:
        kwargs = {}
        if local_path:
            kwargs["local_path"] = local_path
        if not is_local:
            kwargs["is_local"] = is_local
        if begin_date:
            kwargs["begin_date"] = begin_date
        if end_date:
            kwargs["end_date"] = end_date
        result = ad.InfoData().get_cash_flow(code_list, **kwargs)
        return {code: df_to_records(df) for code, df in result.items()}

    def get_income(
        self, code_list: List[str],
        local_path: Optional[str] = None, is_local: bool = False,
        begin_date: Optional[int] = None, end_date: Optional[int] = None,
    ) -> Dict[str, list]:
        kwargs = {}
        if local_path:
            kwargs["local_path"] = local_path
        if not is_local:
            kwargs["is_local"] = is_local
        if begin_date:
            kwargs["begin_date"] = begin_date
        if end_date:
            kwargs["end_date"] = end_date
        result = ad.InfoData().get_income(code_list, **kwargs)
        return {code: df_to_records(df) for code, df in result.items()}

    def get_profit_express(
        self, code_list: List[str],
        local_path: Optional[str] = None, is_local: bool = False,
        begin_date: Optional[int] = None, end_date: Optional[int] = None,
    ) -> list:
        kwargs = {}
        if local_path:
            kwargs["local_path"] = local_path
        if not is_local:
            kwargs["is_local"] = is_local
        if begin_date:
            kwargs["begin_date"] = begin_date
        if end_date:
            kwargs["end_date"] = end_date
        return df_to_records(ad.InfoData().get_profit_express(code_list, **kwargs))

    def get_forecast(
        self, code_list: List[str],
        local_path: Optional[str] = None, is_local: bool = False,
        begin_date: Optional[int] = None, end_date: Optional[int] = None,
    ) -> list:
        kwargs = {}
        if local_path:
            kwargs["local_path"] = local_path
        if not is_local:
            kwargs["is_local"] = is_local
        if begin_date:
            kwargs["begin_date"] = begin_date
        if end_date:
            kwargs["end_date"] = end_date
        return df_to_records(ad.InfoData().get_forecast(code_list, **kwargs))

    # ==================== 股东股本数据 ====================

    def get_top10_holder(
        self, code_list: List[str],
        local_path: Optional[str] = None, is_local: bool = False,
        begin_date: Optional[int] = None, end_date: Optional[int] = None,
    ) -> list:
        kwargs = {}
        if local_path:
            kwargs["local_path"] = local_path
        if not is_local:
            kwargs["is_local"] = is_local
        if begin_date:
            kwargs["begin_date"] = begin_date
        if end_date:
            kwargs["end_date"] = end_date
        return df_to_records(ad.InfoData().get_top10_holder(code_list, **kwargs))

    def get_shareholder_num(
        self, code_list: List[str],
        local_path: Optional[str] = None, is_local: bool = False,
        begin_date: Optional[int] = None, end_date: Optional[int] = None,
    ) -> list:
        kwargs = {}
        if local_path:
            kwargs["local_path"] = local_path
        if not is_local:
            kwargs["is_local"] = is_local
        if begin_date:
            kwargs["begin_date"] = begin_date
        if end_date:
            kwargs["end_date"] = end_date
        return df_to_records(ad.InfoData().get_shareholder_num(code_list, **kwargs))

    def get_share_structure(
        self, code_list: List[str],
        local_path: Optional[str] = None, is_local: bool = False,
        begin_date: Optional[int] = None, end_date: Optional[int] = None,
    ) -> list:
        kwargs = {}
        if local_path:
            kwargs["local_path"] = local_path
        if not is_local:
            kwargs["is_local"] = is_local
        if begin_date:
            kwargs["begin_date"] = begin_date
        if end_date:
            kwargs["end_date"] = end_date
        return df_to_records(ad.InfoData().get_share_structure(code_list, **kwargs))

    def get_pledge_info(
        self, code_list: List[str],
        local_path: Optional[str] = None, is_local: bool = False,
        begin_date: Optional[int] = None, end_date: Optional[int] = None,
    ) -> list:
        kwargs = {}
        if local_path:
            kwargs["local_path"] = local_path
        if not is_local:
            kwargs["is_local"] = is_local
        if begin_date:
            kwargs["begin_date"] = begin_date
        if end_date:
            kwargs["end_date"] = end_date
        return df_to_records(ad.InfoData().get_pledge_info(code_list, **kwargs))

    def get_restricted_share(
        self, code_list: List[str],
        local_path: Optional[str] = None, is_local: bool = False,
        begin_date: Optional[int] = None, end_date: Optional[int] = None,
    ) -> list:
        kwargs = {}
        if local_path:
            kwargs["local_path"] = local_path
        if not is_local:
            kwargs["is_local"] = is_local
        if begin_date:
            kwargs["begin_date"] = begin_date
        if end_date:
            kwargs["end_date"] = end_date
        return df_to_records(ad.InfoData().get_restricted_share(code_list, **kwargs))

    # ==================== 股东权益 ====================

    def get_dividend(
        self, code_list: List[str],
        local_path: Optional[str] = None, is_local: bool = False,
        begin_date: Optional[int] = None, end_date: Optional[int] = None,
    ) -> list:
        kwargs = {}
        if local_path:
            kwargs["local_path"] = local_path
        if not is_local:
            kwargs["is_local"] = is_local
        if begin_date:
            kwargs["begin_date"] = begin_date
        if end_date:
            kwargs["end_date"] = end_date
        return df_to_records(ad.InfoData().get_dividend(code_list, **kwargs))

    def get_allotment(
        self, code_list: List[str],
        local_path: Optional[str] = None, is_local: bool = False,
        begin_date: Optional[int] = None, end_date: Optional[int] = None,
    ) -> list:
        kwargs = {}
        if local_path:
            kwargs["local_path"] = local_path
        if not is_local:
            kwargs["is_local"] = is_local
        if begin_date:
            kwargs["begin_date"] = begin_date
        if end_date:
            kwargs["end_date"] = end_date
        return df_to_records(ad.InfoData().get_allotment(code_list, **kwargs))

    # ==================== 融资融券 ====================

    def get_margin_trade(
        self, code_list: List[str],
        local_path: Optional[str] = None, is_local: bool = False,
        begin_date: Optional[int] = None, end_date: Optional[int] = None,
    ) -> list:
        kwargs = {}
        if local_path:
            kwargs["local_path"] = local_path
        if not is_local:
            kwargs["is_local"] = is_local
        if begin_date:
            kwargs["begin_date"] = begin_date
        if end_date:
            kwargs["end_date"] = end_date
        return df_to_records(ad.InfoData().get_margin_trade(code_list, **kwargs))

    def get_margin_detail(
        self, code_list: List[str],
        local_path: Optional[str] = None, is_local: bool = False,
        begin_date: Optional[int] = None, end_date: Optional[int] = None,
    ) -> list:
        kwargs = {}
        if local_path:
            kwargs["local_path"] = local_path
        if not is_local:
            kwargs["is_local"] = is_local
        if begin_date:
            kwargs["begin_date"] = begin_date
        if end_date:
            kwargs["end_date"] = end_date
        return df_to_records(ad.InfoData().get_margin_detail(code_list, **kwargs))

    # ==================== 市场异动 ====================

    def get_block_trade(
        self, code_list: List[str],
        local_path: Optional[str] = None, is_local: bool = False,
        begin_date: Optional[int] = None, end_date: Optional[int] = None,
    ) -> list:
        kwargs = {}
        if local_path:
            kwargs["local_path"] = local_path
        if not is_local:
            kwargs["is_local"] = is_local
        if begin_date:
            kwargs["begin_date"] = begin_date
        if end_date:
            kwargs["end_date"] = end_date
        return df_to_records(ad.InfoData().get_block_trade(code_list, **kwargs))

    def get_abnormal_trade(
        self, code_list: List[str],
        local_path: Optional[str] = None, is_local: bool = False,
        begin_date: Optional[int] = None, end_date: Optional[int] = None,
    ) -> list:
        kwargs = {}
        if local_path:
            kwargs["local_path"] = local_path
        if not is_local:
            kwargs["is_local"] = is_local
        if begin_date:
            kwargs["begin_date"] = begin_date
        if end_date:
            kwargs["end_date"] = end_date
        return df_to_records(ad.InfoData().get_abnormal_trade(code_list, **kwargs))

    # ==================== ETF 数据 ====================

    def get_etf_daily_subscription(
        self, code_list: List[str],
        local_path: Optional[str] = None, is_local: bool = False,
        begin_date: Optional[int] = None, end_date: Optional[int] = None,
    ) -> list:
        kwargs = {}
        if local_path:
            kwargs["local_path"] = local_path
        if not is_local:
            kwargs["is_local"] = is_local
        if begin_date:
            kwargs["begin_date"] = begin_date
        if end_date:
            kwargs["end_date"] = end_date
        return df_to_records(ad.InfoData().get_etf_daily_subscription(code_list, **kwargs))

    def get_etf_share(
        self, code_list: List[str],
        local_path: Optional[str] = None, is_local: bool = False,
        begin_date: Optional[int] = None, end_date: Optional[int] = None,
    ) -> list:
        kwargs = {}
        if local_path:
            kwargs["local_path"] = local_path
        if not is_local:
            kwargs["is_local"] = is_local
        if begin_date:
            kwargs["begin_date"] = begin_date
        if end_date:
            kwargs["end_date"] = end_date
        return df_to_records(ad.InfoData().get_etf_share(code_list, **kwargs))

    def get_etf_iopv(
        self, code_list: List[str],
        local_path: Optional[str] = None, is_local: bool = False,
        begin_date: Optional[int] = None, end_date: Optional[int] = None,
    ) -> list:
        kwargs = {}
        if local_path:
            kwargs["local_path"] = local_path
        if not is_local:
            kwargs["is_local"] = is_local
        if begin_date:
            kwargs["begin_date"] = begin_date
        if end_date:
            kwargs["end_date"] = end_date
        return df_to_records(ad.InfoData().get_etf_iopv(code_list, **kwargs))

    # ==================== 申万指数 ====================

    def get_shenwan_index_info(self) -> list:
        return df_to_records(ad.InfoData().get_shenwan_index_info())

    def get_shenwan_index_component(self, code_list: List[str]) -> list:
        return df_to_records(ad.InfoData().get_shenwan_index_component(code_list))

    def get_shenwan_index_component_weight(self, code_list: List[str]) -> list:
        return df_to_records(ad.InfoData().get_shenwan_index_component_weight(code_list))

    def get_shenwan_index_data(
        self, code_list: List[str],
        begin_date: Optional[int] = None, end_date: Optional[int] = None,
    ) -> list:
        kwargs = {}
        if begin_date:
            kwargs["begin_date"] = begin_date
        if end_date:
            kwargs["end_date"] = end_date
        return df_to_records(ad.InfoData().get_shenwan_index_data(code_list, **kwargs))

    # ==================== 行业指数 ====================

    def get_industry_index_info(
        self, local_path: Optional[str] = None, is_local: bool = False,
    ) -> list:
        return df_to_records(ad.InfoData().get_industry_index_info(
            local_path=local_path, is_local=is_local
        ))

    def get_industry_index_component(
        self, code_list: List[str],
        local_path: Optional[str] = None, is_local: bool = False,
    ) -> list:
        return df_to_records(ad.InfoData().get_industry_index_component(
            code_list, local_path=local_path, is_local=is_local
        ))

    def get_industry_index_component_weight(
        self, code_list: List[str],
        local_path: Optional[str] = None, is_local: bool = False,
    ) -> list:
        return df_to_records(ad.InfoData().get_industry_index_component_weight(
            code_list, local_path=local_path, is_local=is_local
        ))

    def get_industry_index_data(
        self, code_list: List[str],
        begin_date: Optional[int] = None, end_date: Optional[int] = None,
    ) -> list:
        kwargs = {}
        if begin_date:
            kwargs["begin_date"] = begin_date
        if end_date:
            kwargs["end_date"] = end_date
        return df_to_records(ad.InfoData().get_industry_index_data(code_list, **kwargs))

    # ==================== 可转债 ====================

    def get_cb_info(
        self, code_list: List[str],
        local_path: Optional[str] = None, is_local: bool = False,
        begin_date: Optional[int] = None, end_date: Optional[int] = None,
    ) -> list:
        kwargs = {}
        if local_path:
            kwargs["local_path"] = local_path
        if not is_local:
            kwargs["is_local"] = is_local
        if begin_date:
            kwargs["begin_date"] = begin_date
        if end_date:
            kwargs["end_date"] = end_date
        return df_to_records(ad.InfoData().get_cb_info(code_list, **kwargs))

    def get_cb_share(
        self, code_list: List[str],
        local_path: Optional[str] = None, is_local: bool = False,
        begin_date: Optional[int] = None, end_date: Optional[int] = None,
    ) -> list:
        kwargs = {}
        if local_path:
            kwargs["local_path"] = local_path
        if not is_local:
            kwargs["is_local"] = is_local
        if begin_date:
            kwargs["begin_date"] = begin_date
        if end_date:
            kwargs["end_date"] = end_date
        return df_to_records(ad.InfoData().get_cb_share(code_list, **kwargs))

    def get_cb_conversion(
        self, code_list: List[str],
        local_path: Optional[str] = None, is_local: bool = False,
        begin_date: Optional[int] = None, end_date: Optional[int] = None,
    ) -> list:
        kwargs = {}
        if local_path:
            kwargs["local_path"] = local_path
        if not is_local:
            kwargs["is_local"] = is_local
        if begin_date:
            kwargs["begin_date"] = begin_date
        if end_date:
            kwargs["end_date"] = end_date
        return df_to_records(ad.InfoData().get_cb_conversion(code_list, **kwargs))

    def get_cb_conversion_change(
        self, code_list: List[str],
        local_path: Optional[str] = None, is_local: bool = False,
        begin_date: Optional[int] = None, end_date: Optional[int] = None,
    ) -> list:
        kwargs = {}
        if local_path:
            kwargs["local_path"] = local_path
        if not is_local:
            kwargs["is_local"] = is_local
        if begin_date:
            kwargs["begin_date"] = begin_date
        if end_date:
            kwargs["end_date"] = end_date
        return df_to_records(ad.InfoData().get_cb_conversion_change(code_list, **kwargs))

    def get_cb_redemption(
        self, code_list: List[str],
        local_path: Optional[str] = None, is_local: bool = False,
        begin_date: Optional[int] = None, end_date: Optional[int] = None,
    ) -> list:
        kwargs = {}
        if local_path:
            kwargs["local_path"] = local_path
        if not is_local:
            kwargs["is_local"] = is_local
        if begin_date:
            kwargs["begin_date"] = begin_date
        if end_date:
            kwargs["end_date"] = end_date
        return df_to_records(ad.InfoData().get_cb_redemption(code_list, **kwargs))

    def get_cb_putback(
        self, code_list: List[str],
        local_path: Optional[str] = None, is_local: bool = False,
        begin_date: Optional[int] = None, end_date: Optional[int] = None,
    ) -> list:
        kwargs = {}
        if local_path:
            kwargs["local_path"] = local_path
        if not is_local:
            kwargs["is_local"] = is_local
        if begin_date:
            kwargs["begin_date"] = begin_date
        if end_date:
            kwargs["end_date"] = end_date
        return df_to_records(ad.InfoData().get_cb_putback(code_list, **kwargs))

    def get_cb_call(
        self, code_list: List[str],
        local_path: Optional[str] = None, is_local: bool = False,
        begin_date: Optional[int] = None, end_date: Optional[int] = None,
    ) -> list:
        kwargs = {}
        if local_path:
            kwargs["local_path"] = local_path
        if not is_local:
            kwargs["is_local"] = is_local
        if begin_date:
            kwargs["begin_date"] = begin_date
        if end_date:
            kwargs["end_date"] = end_date
        return df_to_records(ad.InfoData().get_cb_call(code_list, **kwargs))

    def get_cb_suspend(
        self, code_list: List[str],
        local_path: Optional[str] = None, is_local: bool = False,
        begin_date: Optional[int] = None, end_date: Optional[int] = None,
    ) -> list:
        kwargs = {}
        if local_path:
            kwargs["local_path"] = local_path
        if not is_local:
            kwargs["is_local"] = is_local
        if begin_date:
            kwargs["begin_date"] = begin_date
        if end_date:
            kwargs["end_date"] = end_date
        return df_to_records(ad.InfoData().get_cb_suspend(code_list, **kwargs))

    # ==================== 期权 ====================

    def get_option_info(
        self, code_list: List[str],
        local_path: Optional[str] = None, is_local: bool = False,
        begin_date: Optional[int] = None, end_date: Optional[int] = None,
    ) -> list:
        kwargs = {}
        if local_path:
            kwargs["local_path"] = local_path
        if not is_local:
            kwargs["is_local"] = is_local
        if begin_date:
            kwargs["begin_date"] = begin_date
        if end_date:
            kwargs["end_date"] = end_date
        return df_to_records(ad.InfoData().get_option_info(code_list, **kwargs))

    def get_option_contract(
        self, code_list: List[str],
        local_path: Optional[str] = None, is_local: bool = False,
        begin_date: Optional[int] = None, end_date: Optional[int] = None,
    ) -> list:
        kwargs = {}
        if local_path:
            kwargs["local_path"] = local_path
        if not is_local:
            kwargs["is_local"] = is_local
        if begin_date:
            kwargs["begin_date"] = begin_date
        if end_date:
            kwargs["end_date"] = end_date
        return df_to_records(ad.InfoData().get_option_contract(code_list, **kwargs))

    def get_option_contract_change(
        self, code_list: List[str],
        local_path: Optional[str] = None, is_local: bool = False,
        begin_date: Optional[int] = None, end_date: Optional[int] = None,
    ) -> list:
        kwargs = {}
        if local_path:
            kwargs["local_path"] = local_path
        if not is_local:
            kwargs["is_local"] = is_local
        if begin_date:
            kwargs["begin_date"] = begin_date
        if end_date:
            kwargs["end_date"] = end_date
        return df_to_records(ad.InfoData().get_option_contract_change(code_list, **kwargs))

    # ==================== 国债 ====================

    def get_treasury(
        self, code_list: List[str],
        local_path: Optional[str] = None, is_local: bool = False,
        begin_date: Optional[int] = None, end_date: Optional[int] = None,
    ) -> list:
        kwargs = {}
        if local_path:
            kwargs["local_path"] = local_path
        if not is_local:
            kwargs["is_local"] = is_local
        if begin_date:
            kwargs["begin_date"] = begin_date
        if end_date:
            kwargs["end_date"] = end_date
        return df_to_records(ad.InfoData().get_treasury(code_list, **kwargs))


client = AmazingDataClient()
