import threading


from typing import List, Dict, Optional, Union
import pandas as pd

from config import (
    AMAZINGDATA_USERNAME,
    AMAZINGDATA_PASSWORD,
    AMAZINGDATA_HOST,
    AMAZINGDATA_PORT,
    CACHE_TTL_SECONDS,
    CALENDAR_CACHE_TTL,
)
from utils import cache, cached, df_to_records, dict_df_to_records


class AmazingDataClient:

    def __init__(self):
        self._logged_in = False
        self._login_attempted = False
        self._login_event = threading.Event()
        self._calendar = None
        self._ad = None

    # ==================== 延迟加载 SDK ====================

    def _get_ad(self):
        if self._ad is None:
            import AmazingData as ad
            self._ad = ad
        self.ensure_login()
        return self._ad

    # ==================== 登录（首次 SDK 调用时阻塞等待）====================

    def ensure_login(self):
        if self._login_event.is_set():
            return
        if self._login_attempted:
            self._login_event.wait(timeout=15)
            return
        self._login_attempted = True
        t = threading.Thread(target=self._do_login, daemon=True)
        t.start()
        self._login_event.wait(timeout=15)

    def _do_login(self):
        try:
            print(f"[login] 登录 host={AMAZINGDATA_HOST}:{AMAZINGDATA_PORT}", flush=True)
            import socket
            socket.setdefaulttimeout(5)
            self._ad.login(
                username=AMAZINGDATA_USERNAME,
                password=AMAZINGDATA_PASSWORD,
                host=AMAZINGDATA_HOST,
                port=AMAZINGDATA_PORT,
            )
            self._logged_in = True
            print(f"[login] 成功", flush=True)
        except Exception as e:
            self._logged_in = False
            print(f"[login] 失败: {e}", flush=True)
        finally:
            self._login_event.set()

    # ==================== 基础数据 ====================

    def get_calendar(self) -> List[int]:
        if self._calendar is not None:
            return self._calendar
        ad = self._get_ad()
        import time
        for attempt in range(3):
            result = ad.BaseData().get_calendar()
            if result is not None:
                self._calendar = result
                return self._calendar
            time.sleep(1)
        raise RuntimeError("SDK get_calendar() 返回 None，请稍后重试")

    def get_code_list(self, security_type: str = "EXTRA_STOCK_A") -> List[str]:
        cache_key = f"code_list:{security_type}"
        cached_val = cache.get(cache_key)
        if cached_val is not None:
            return cached_val
        result = self._get_ad().BaseData().get_code_list(security_type=security_type)
        cache.set(cache_key, result, ttl=CACHE_TTL_SECONDS)
        return result

    def get_code_info(self, security_type: str = "EXTRA_STOCK_A") -> list:
        cache_key = f"code_info:{security_type}"
        cached_val = cache.get(cache_key)
        if cached_val is not None:
            return cached_val
        df = self._get_ad().BaseData().get_code_info(security_type=security_type)
        result = df_to_records(df)
        del df
        cache.set(cache_key, result, ttl=CACHE_TTL_SECONDS)
        return result

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
        return self._get_ad().BaseData().get_hist_code_list(
            security_type=security_type, start_date=start_date, end_date=end_date, **kwargs
        )

    def get_future_code_list(self, security_type: str = "ZJ_FUTURE") -> List[str]:
        return self._get_ad().BaseData().get_future_code_list(security_type=security_type)

    def get_option_code_list(self, security_type: str = "EXTRA_ETF_OP") -> List[str]:
        return self._get_ad().BaseData().get_option_code_list(security_type=security_type)

    def get_backward_factor(
        self,
        code_list: List[str],
        local_path: Optional[str] = None,
        is_local: bool = False,
    ) -> list:
        return df_to_records(self._get_ad().BaseData().get_backward_factor(
            code_list, local_path=local_path, is_local=is_local
        ))

    def get_adj_factor(
        self,
        code_list: List[str],
        local_path: Optional[str] = None,
        is_local: bool = False,
    ) -> list:
        return df_to_records(self._get_ad().BaseData().get_adj_factor(
            code_list, local_path=local_path, is_local=is_local
        ))

    def get_bj_code_mapping(
        self,
        local_path: Optional[str] = None,
        is_local: bool = False,
    ) -> list:
        return df_to_records(self._get_ad().InfoData().get_bj_code_mapping(
            local_path=local_path, is_local=is_local
        ))

    # ==================== 行情数据 ====================

    def _get_period_value(self, period_key: str, default: str = "day"):
        P = self._get_ad().utils.constant.Period
        m = {
            "1min": P.min1.value, "3min": P.min3.value, "5min": P.min5.value,
            "10min": P.min10.value, "15min": P.min15.value, "30min": P.min30.value,
            "60min": P.min60.value, "120min": P.min120.value,
            "day": P.day.value, "week": P.week.value,
            "month": P.month.value, "season": P.season.value, "year": P.year.value,
        }
        return m.get(period_key, m[default])

    def query_kline(
        self, code_list: List[str], begin_date: int, end_date: int,
        period: str = "day", begin_time: Optional[int] = None, end_time: Optional[int] = None,
    ) -> Dict[str, list]:
        p = self._get_period_value(period)
        calendar = self.get_calendar()
        market_data = self._get_ad().MarketData(calendar)
        kwargs = {}
        if begin_time is not None:
            kwargs["begin_time"] = begin_time
        if end_time is not None:
            kwargs["end_time"] = end_time
        result = market_data.query_kline(code_list, begin_date=begin_date, end_date=end_date, period=p, **kwargs)
        records = {}
        for code, df in result.items():
            records[code] = df_to_records(df)
            del df
        del result
        return records

    def query_snapshot(
        self, code_list: List[str], begin_date: int, end_date: int,
        begin_time: Optional[int] = None, end_time: Optional[int] = None,
    ) -> Dict[str, list]:
        calendar = self.get_calendar()
        market_data = self._get_ad().MarketData(calendar)
        kwargs = {}
        if begin_time is not None:
            kwargs["begin_time"] = begin_time
        if end_time is not None:
            kwargs["end_time"] = end_time
        result = market_data.query_snapshot(code_list, begin_date=begin_date, end_date=end_date, **kwargs)
        records = {}
        for code, df in result.items():
            records[code] = df_to_records(df)
            del df
        del result
        return records

    # ==================== 证券基本信息 ====================

    def get_stock_basic(self, code_list: List[str]) -> list:
        return df_to_records(self._get_ad().InfoData().get_stock_basic(code_list))

    def get_history_stock_status(
        self, code_list: List[str],
        local_path: Optional[str] = None, is_local: bool = False,
        begin_date: Optional[int] = None, end_date: Optional[int] = None,
    ) -> list:
        kwargs = {}
        if local_path:
            kwargs["local_path"] = local_path
        if is_local:
            kwargs["is_local"] = is_local
        if begin_date:
            kwargs["begin_date"] = begin_date
        if end_date:
            kwargs["end_date"] = end_date
        return df_to_records(self._get_ad().InfoData().get_history_stock_status(code_list, **kwargs))

    # ==================== 财务报表 ====================

    def get_balance_sheet(
        self, code_list: List[str],
        local_path: Optional[str] = None, is_local: bool = False,
        begin_date: Optional[int] = None, end_date: Optional[int] = None,
    ) -> Dict[str, list]:
        kwargs = {}
        if local_path:
            kwargs["local_path"] = local_path
        if is_local:
            kwargs["is_local"] = is_local
        if begin_date:
            kwargs["begin_date"] = begin_date
        if end_date:
            kwargs["end_date"] = end_date
        result = self._get_ad().InfoData().get_balance_sheet(code_list, **kwargs)
        return dict_df_to_records(result)

    def get_cash_flow(
        self, code_list: List[str],
        local_path: Optional[str] = None, is_local: bool = False,
        begin_date: Optional[int] = None, end_date: Optional[int] = None,
    ) -> Dict[str, list]:
        kwargs = {}
        if local_path:
            kwargs["local_path"] = local_path
        if is_local:
            kwargs["is_local"] = is_local
        if begin_date:
            kwargs["begin_date"] = begin_date
        if end_date:
            kwargs["end_date"] = end_date
        result = self._get_ad().InfoData().get_cash_flow(code_list, **kwargs)
        return dict_df_to_records(result)

    def get_income(
        self, code_list: List[str],
        local_path: Optional[str] = None, is_local: bool = False,
        begin_date: Optional[int] = None, end_date: Optional[int] = None,
    ) -> Dict[str, list]:
        kwargs = {}
        if local_path:
            kwargs["local_path"] = local_path
        if is_local:
            kwargs["is_local"] = is_local
        if begin_date:
            kwargs["begin_date"] = begin_date
        if end_date:
            kwargs["end_date"] = end_date
        result = self._get_ad().InfoData().get_income(code_list, **kwargs)
        return dict_df_to_records(result)

    def get_profit_express(
        self, code_list: List[str],
        local_path: Optional[str] = None, is_local: bool = False,
        begin_date: Optional[int] = None, end_date: Optional[int] = None,
    ) -> list:
        kwargs = {}
        if local_path:
            kwargs["local_path"] = local_path
        if is_local:
            kwargs["is_local"] = is_local
        if begin_date:
            kwargs["begin_date"] = begin_date
        if end_date:
            kwargs["end_date"] = end_date
        return df_to_records(self._get_ad().InfoData().get_profit_express(code_list, **kwargs))

    def get_forecast(
        self, code_list: List[str],
        local_path: Optional[str] = None, is_local: bool = False,
        begin_date: Optional[int] = None, end_date: Optional[int] = None,
    ) -> list:
        kwargs = {}
        if local_path:
            kwargs["local_path"] = local_path
        if is_local:
            kwargs["is_local"] = is_local
        if begin_date:
            kwargs["begin_date"] = begin_date
        if end_date:
            kwargs["end_date"] = end_date
        return df_to_records(self._get_ad().InfoData().get_profit_notice(code_list, **kwargs))

    # ==================== 股东股本数据 ====================

    def get_top10_holder(
        self, code_list: List[str],
        local_path: Optional[str] = None, is_local: bool = False,
        begin_date: Optional[int] = None, end_date: Optional[int] = None,
    ) -> list:
        kwargs = {}
        if local_path:
            kwargs["local_path"] = local_path
        if is_local:
            kwargs["is_local"] = is_local
        if begin_date:
            kwargs["begin_date"] = begin_date
        if end_date:
            kwargs["end_date"] = end_date
        return df_to_records(self._get_ad().InfoData().get_share_holder(code_list, **kwargs))

    def get_shareholder_num(
        self, code_list: List[str],
        local_path: Optional[str] = None, is_local: bool = False,
        begin_date: Optional[int] = None, end_date: Optional[int] = None,
    ) -> list:
        kwargs = {}
        if local_path:
            kwargs["local_path"] = local_path
        if is_local:
            kwargs["is_local"] = is_local
        if begin_date:
            kwargs["begin_date"] = begin_date
        if end_date:
            kwargs["end_date"] = end_date
        return df_to_records(self._get_ad().InfoData().get_holder_num(code_list, **kwargs))

    def get_share_structure(
        self, code_list: List[str],
        local_path: Optional[str] = None, is_local: bool = False,
        begin_date: Optional[int] = None, end_date: Optional[int] = None,
    ) -> list:
        kwargs = {}
        if local_path:
            kwargs["local_path"] = local_path
        if is_local:
            kwargs["is_local"] = is_local
        if begin_date:
            kwargs["begin_date"] = begin_date
        if end_date:
            kwargs["end_date"] = end_date
        return df_to_records(self._get_ad().InfoData().get_equity_structure(code_list, **kwargs))

    def get_pledge_info(
        self, code_list: List[str],
        local_path: Optional[str] = None, is_local: bool = False,
        begin_date: Optional[int] = None, end_date: Optional[int] = None,
    ) -> list:
        kwargs = {}
        if local_path:
            kwargs["local_path"] = local_path
        if is_local:
            kwargs["is_local"] = is_local
        if begin_date:
            kwargs["begin_date"] = begin_date
        if end_date:
            kwargs["end_date"] = end_date
        return df_to_records(self._get_ad().InfoData().get_equity_pledge_freeze(code_list, **kwargs))

    def get_restricted_share(
        self, code_list: List[str],
        local_path: Optional[str] = None, is_local: bool = False,
        begin_date: Optional[int] = None, end_date: Optional[int] = None,
    ) -> list:
        kwargs = {}
        if local_path:
            kwargs["local_path"] = local_path
        if is_local:
            kwargs["is_local"] = is_local
        if begin_date:
            kwargs["begin_date"] = begin_date
        if end_date:
            kwargs["end_date"] = end_date
        return df_to_records(self._get_ad().InfoData().get_equity_restricted(code_list, **kwargs))

    # ==================== 股东权益 ====================

    def get_dividend(
        self, code_list: List[str],
        local_path: Optional[str] = None, is_local: bool = False,
        begin_date: Optional[int] = None, end_date: Optional[int] = None,
    ) -> list:
        kwargs = {}
        if local_path:
            kwargs["local_path"] = local_path
        if is_local:
            kwargs["is_local"] = is_local
        if begin_date:
            kwargs["begin_date"] = begin_date
        if end_date:
            kwargs["end_date"] = end_date
        return df_to_records(self._get_ad().InfoData().get_dividend(code_list, **kwargs))

    def get_allotment(
        self, code_list: List[str],
        local_path: Optional[str] = None, is_local: bool = False,
        begin_date: Optional[int] = None, end_date: Optional[int] = None,
    ) -> list:
        kwargs = {}
        if local_path:
            kwargs["local_path"] = local_path
        if is_local:
            kwargs["is_local"] = is_local
        if begin_date:
            kwargs["begin_date"] = begin_date
        if end_date:
            kwargs["end_date"] = end_date
        return df_to_records(self._get_ad().InfoData().get_right_issue(code_list, **kwargs))

    # ==================== 融资融券 ====================

    def get_margin_trade(
        self, code_list: List[str],
        local_path: Optional[str] = None, is_local: bool = False,
        begin_date: Optional[int] = None, end_date: Optional[int] = None,
    ) -> list:
        kwargs = {}
        if local_path:
            kwargs["local_path"] = local_path
        if is_local:
            kwargs["is_local"] = is_local
        if begin_date:
            kwargs["begin_date"] = begin_date
        if end_date:
            kwargs["end_date"] = end_date
        return df_to_records(self._get_ad().InfoData().get_margin_summary(code_list, **kwargs))

    def get_margin_detail(
        self, code_list: List[str],
        local_path: Optional[str] = None, is_local: bool = False,
        begin_date: Optional[int] = None, end_date: Optional[int] = None,
    ) -> list:
        kwargs = {}
        if local_path:
            kwargs["local_path"] = local_path
        if is_local:
            kwargs["is_local"] = is_local
        if begin_date:
            kwargs["begin_date"] = begin_date
        if end_date:
            kwargs["end_date"] = end_date
        return df_to_records(self._get_ad().InfoData().get_margin_detail(code_list, **kwargs))

    # ==================== 市场异动 ====================

    def get_block_trade(
        self, code_list: List[str],
        local_path: Optional[str] = None, is_local: bool = False,
        begin_date: Optional[int] = None, end_date: Optional[int] = None,
    ) -> list:
        kwargs = {}
        if local_path:
            kwargs["local_path"] = local_path
        if is_local:
            kwargs["is_local"] = is_local
        if begin_date:
            kwargs["begin_date"] = begin_date
        if end_date:
            kwargs["end_date"] = end_date
        return df_to_records(self._get_ad().InfoData().get_block_trading(code_list, **kwargs))

    def get_abnormal_trade(
        self, code_list: List[str],
        local_path: Optional[str] = None, is_local: bool = False,
        begin_date: Optional[int] = None, end_date: Optional[int] = None,
    ) -> list:
        kwargs = {}
        if local_path:
            kwargs["local_path"] = local_path
        if is_local:
            kwargs["is_local"] = is_local
        if begin_date:
            kwargs["begin_date"] = begin_date
        if end_date:
            kwargs["end_date"] = end_date
        return df_to_records(self._get_ad().InfoData().get_abnormal_trade(code_list, **kwargs))

    def get_long_hu_bang(
        self, code_list: List[str],
        local_path: Optional[str] = None, is_local: bool = False,
        begin_date: Optional[int] = None, end_date: Optional[int] = None,
    ) -> list:
        kwargs = {}
        if local_path:
            kwargs["local_path"] = local_path
        if is_local:
            kwargs["is_local"] = is_local
        if begin_date:
            kwargs["begin_date"] = begin_date
        if end_date:
            kwargs["end_date"] = end_date
        return df_to_records(self._get_ad().InfoData().get_long_hu_bang(code_list, **kwargs))

    # ==================== ETF 数据 ====================

    def get_etf_daily_subscription(
        self, code_list: List[str],
        local_path: Optional[str] = None, is_local: bool = False,
        begin_date: Optional[int] = None, end_date: Optional[int] = None,
    ) -> list:
        kwargs = {}
        if local_path:
            kwargs["local_path"] = local_path
        if is_local:
            kwargs["is_local"] = is_local
        if begin_date:
            kwargs["begin_date"] = begin_date
        if end_date:
            kwargs["end_date"] = end_date
        return df_to_records(self._get_ad().InfoData().get_etf_daily_subscription(code_list, **kwargs))

    def get_etf_share(
        self, code_list: List[str],
        local_path: Optional[str] = None, is_local: bool = False,
        begin_date: Optional[int] = None, end_date: Optional[int] = None,
    ) -> list:
        kwargs = {}
        if local_path:
            kwargs["local_path"] = local_path
        if is_local:
            kwargs["is_local"] = is_local
        if begin_date:
            kwargs["begin_date"] = begin_date
        if end_date:
            kwargs["end_date"] = end_date
        return df_to_records(self._get_ad().InfoData().get_etf_share(code_list, **kwargs))

    def get_etf_iopv(
        self, code_list: List[str],
        local_path: Optional[str] = None, is_local: bool = False,
        begin_date: Optional[int] = None, end_date: Optional[int] = None,
    ) -> list:
        kwargs = {}
        if local_path:
            kwargs["local_path"] = local_path
        if is_local:
            kwargs["is_local"] = is_local
        if begin_date:
            kwargs["begin_date"] = begin_date
        if end_date:
            kwargs["end_date"] = end_date
        return df_to_records(self._get_ad().InfoData().get_etf_iopv(code_list, **kwargs))

    def get_fund_nav(
        self, code_list: List[str],
        local_path: Optional[str] = None, is_local: bool = False,
        begin_date: Optional[int] = None, end_date: Optional[int] = None,
    ) -> list:
        kwargs = {}
        if local_path:
            kwargs["local_path"] = local_path
        if is_local:
            kwargs["is_local"] = is_local
        if begin_date:
            kwargs["begin_date"] = begin_date
        if end_date:
            kwargs["end_date"] = end_date
        return df_to_records(self._get_ad().InfoData().get_fund_nav(code_list, **kwargs))

    # ==================== 申万指数 ====================

    def get_shenwan_index_info(self) -> list:
        return df_to_records(self._get_ad().InfoData().get_index_constituent([], is_local=False))

    def get_shenwan_index_component(self, code_list: List[str]) -> list:
        return df_to_records(self._get_ad().InfoData().get_index_constituent(code_list, is_local=False))

    def get_shenwan_index_component_weight(self, code_list: List[str]) -> list:
        return df_to_records(self._get_ad().InfoData().get_index_weight(code_list, is_local=False))

    def get_shenwan_index_data(
        self, code_list: List[str],
        begin_date: Optional[int] = None, end_date: Optional[int] = None,
    ) -> list:
        kwargs = {}
        if begin_date:
            kwargs["begin_date"] = begin_date
        if end_date:
            kwargs["end_date"] = end_date
        return df_to_records(self._get_ad().InfoData().get_shenwan_index_data(code_list, **kwargs))

    # ==================== 行业指数 ====================

    def get_industry_index_info(
        self, local_path: Optional[str] = None, is_local: bool = False,
    ) -> list:
        return df_to_records(self._get_ad().InfoData().get_industry_base_info(
            local_path=local_path, is_local=is_local
        ))

    def get_industry_index_component(
        self, code_list: List[str],
        local_path: Optional[str] = None, is_local: bool = False,
    ) -> list:
        return df_to_records(self._get_ad().InfoData().get_industry_constituent(
            code_list, local_path=local_path, is_local=is_local
        ))

    def get_industry_index_component_weight(
        self, code_list: List[str],
        local_path: Optional[str] = None, is_local: bool = False,
    ) -> list:
        return df_to_records(self._get_ad().InfoData().get_industry_weight(
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
        return df_to_records(self._get_ad().InfoData().get_industry_daily(code_list, **kwargs))

    # ==================== 可转债 ====================

    def get_cb_info(
        self, code_list: List[str],
        local_path: Optional[str] = None, is_local: bool = False,
        begin_date: Optional[int] = None, end_date: Optional[int] = None,
    ) -> list:
        kwargs = {}
        if local_path:
            kwargs["local_path"] = local_path
        if is_local:
            kwargs["is_local"] = is_local
        if begin_date:
            kwargs["begin_date"] = begin_date
        if end_date:
            kwargs["end_date"] = end_date
        return df_to_records(self._get_ad().InfoData().get_kzz_issuance(code_list, **kwargs))

    def get_cb_share(
        self, code_list: List[str],
        local_path: Optional[str] = None, is_local: bool = False,
        begin_date: Optional[int] = None, end_date: Optional[int] = None,
    ) -> list:
        kwargs = {}
        if local_path:
            kwargs["local_path"] = local_path
        if is_local:
            kwargs["is_local"] = is_local
        if begin_date:
            kwargs["begin_date"] = begin_date
        if end_date:
            kwargs["end_date"] = end_date
        return df_to_records(self._get_ad().InfoData().get_kzz_share(code_list, **kwargs))

    def get_cb_conversion(
        self, code_list: List[str],
        local_path: Optional[str] = None, is_local: bool = False,
        begin_date: Optional[int] = None, end_date: Optional[int] = None,
    ) -> list:
        kwargs = {}
        if local_path:
            kwargs["local_path"] = local_path
        if is_local:
            kwargs["is_local"] = is_local
        if begin_date:
            kwargs["begin_date"] = begin_date
        if end_date:
            kwargs["end_date"] = end_date
        return df_to_records(self._get_ad().InfoData().get_kzz_conv(code_list, **kwargs))

    def get_cb_conversion_change(
        self, code_list: List[str],
        local_path: Optional[str] = None, is_local: bool = False,
        begin_date: Optional[int] = None, end_date: Optional[int] = None,
    ) -> list:
        kwargs = {}
        if local_path:
            kwargs["local_path"] = local_path
        if is_local:
            kwargs["is_local"] = is_local
        if begin_date:
            kwargs["begin_date"] = begin_date
        if end_date:
            kwargs["end_date"] = end_date
        return df_to_records(self._get_ad().InfoData().get_kzz_conv_change(code_list, **kwargs))

    def get_cb_correction(
        self, code_list: List[str],
        local_path: Optional[str] = None, is_local: bool = False,
        begin_date: Optional[int] = None, end_date: Optional[int] = None,
    ) -> list:
        kwargs = {}
        if local_path:
            kwargs["local_path"] = local_path
        if is_local:
            kwargs["is_local"] = is_local
        if begin_date:
            kwargs["begin_date"] = begin_date
        if end_date:
            kwargs["end_date"] = end_date
        return df_to_records(self._get_ad().InfoData().get_kzz_corr(code_list, **kwargs))

    def get_cb_redemption(
        self, code_list: List[str],
        local_path: Optional[str] = None, is_local: bool = False,
        begin_date: Optional[int] = None, end_date: Optional[int] = None,
    ) -> list:
        kwargs = {}
        if local_path:
            kwargs["local_path"] = local_path
        if is_local:
            kwargs["is_local"] = is_local
        if begin_date:
            kwargs["begin_date"] = begin_date
        if end_date:
            kwargs["end_date"] = end_date
        return df_to_records(self._get_ad().InfoData().get_kzz_call(code_list, **kwargs))

    def get_cb_putback(
        self, code_list: List[str],
        local_path: Optional[str] = None, is_local: bool = False,
        begin_date: Optional[int] = None, end_date: Optional[int] = None,
    ) -> list:
        kwargs = {}
        if local_path:
            kwargs["local_path"] = local_path
        if is_local:
            kwargs["is_local"] = is_local
        if begin_date:
            kwargs["begin_date"] = begin_date
        if end_date:
            kwargs["end_date"] = end_date
        return df_to_records(self._get_ad().InfoData().get_kzz_put(code_list, **kwargs))

    def get_cb_put_call_item(
        self, code_list: List[str],
        local_path: Optional[str] = None, is_local: bool = False,
        begin_date: Optional[int] = None, end_date: Optional[int] = None,
    ) -> list:
        kwargs = {}
        if local_path:
            kwargs["local_path"] = local_path
        if is_local:
            kwargs["is_local"] = is_local
        if begin_date:
            kwargs["begin_date"] = begin_date
        if end_date:
            kwargs["end_date"] = end_date
        return df_to_records(self._get_ad().InfoData().get_kzz_put_call_item(code_list, **kwargs))

    def get_cb_put_explanation(
        self, code_list: List[str],
        local_path: Optional[str] = None, is_local: bool = False,
        begin_date: Optional[int] = None, end_date: Optional[int] = None,
    ) -> list:
        kwargs = {}
        if local_path:
            kwargs["local_path"] = local_path
        if is_local:
            kwargs["is_local"] = is_local
        if begin_date:
            kwargs["begin_date"] = begin_date
        if end_date:
            kwargs["end_date"] = end_date
        return df_to_records(self._get_ad().InfoData().get_kzz_put_explanation(code_list, **kwargs))

    def get_cb_call_explanation(
        self, code_list: List[str],
        local_path: Optional[str] = None, is_local: bool = False,
        begin_date: Optional[int] = None, end_date: Optional[int] = None,
    ) -> list:
        kwargs = {}
        if local_path:
            kwargs["local_path"] = local_path
        if is_local:
            kwargs["is_local"] = is_local
        if begin_date:
            kwargs["begin_date"] = begin_date
        if end_date:
            kwargs["end_date"] = end_date
        return df_to_records(self._get_ad().InfoData().get_kzz_call_explanation(code_list, **kwargs))

    def get_cb_call(
        self, code_list: List[str],
        local_path: Optional[str] = None, is_local: bool = False,
        begin_date: Optional[int] = None, end_date: Optional[int] = None,
    ) -> list:
        kwargs = {}
        if local_path:
            kwargs["local_path"] = local_path
        if is_local:
            kwargs["is_local"] = is_local
        if begin_date:
            kwargs["begin_date"] = begin_date
        if end_date:
            kwargs["end_date"] = end_date
        return df_to_records(self._get_ad().InfoData().get_kzz_call(code_list, **kwargs))

    def get_cb_suspend(
        self, code_list: List[str],
        local_path: Optional[str] = None, is_local: bool = False,
        begin_date: Optional[int] = None, end_date: Optional[int] = None,
    ) -> list:
        kwargs = {}
        if local_path:
            kwargs["local_path"] = local_path
        if is_local:
            kwargs["is_local"] = is_local
        if begin_date:
            kwargs["begin_date"] = begin_date
        if end_date:
            kwargs["end_date"] = end_date
        return df_to_records(self._get_ad().InfoData().get_kzz_suspend(code_list, **kwargs))

    # ==================== 期权 ====================

    def get_option_info(
        self, code_list: List[str],
        local_path: Optional[str] = None, is_local: bool = False,
        begin_date: Optional[int] = None, end_date: Optional[int] = None,
    ) -> list:
        kwargs = {}
        if local_path:
            kwargs["local_path"] = local_path
        if is_local:
            kwargs["is_local"] = is_local
        if begin_date:
            kwargs["begin_date"] = begin_date
        if end_date:
            kwargs["end_date"] = end_date
        return df_to_records(self._get_ad().InfoData().get_option_info(code_list, **kwargs))

    def get_option_contract(
        self, code_list: List[str],
        local_path: Optional[str] = None, is_local: bool = False,
        begin_date: Optional[int] = None, end_date: Optional[int] = None,
    ) -> list:
        kwargs = {}
        if local_path:
            kwargs["local_path"] = local_path
        if is_local:
            kwargs["is_local"] = is_local
        if begin_date:
            kwargs["begin_date"] = begin_date
        if end_date:
            kwargs["end_date"] = end_date
        return df_to_records(self._get_ad().InfoData().get_option_contract(code_list, **kwargs))

    def get_option_contract_change(
        self, code_list: List[str],
        local_path: Optional[str] = None, is_local: bool = False,
        begin_date: Optional[int] = None, end_date: Optional[int] = None,
    ) -> list:
        kwargs = {}
        if local_path:
            kwargs["local_path"] = local_path
        if is_local:
            kwargs["is_local"] = is_local
        if begin_date:
            kwargs["begin_date"] = begin_date
        if end_date:
            kwargs["end_date"] = end_date
        return df_to_records(self._get_ad().InfoData().get_option_contract_change(code_list, **kwargs))

    def get_option_std_ctr_specs(
        self, code_list: List[str],
        local_path: Optional[str] = None, is_local: bool = False,
        begin_date: Optional[int] = None, end_date: Optional[int] = None,
    ) -> list:
        kwargs = {}
        if local_path:
            kwargs["local_path"] = local_path
        if is_local:
            kwargs["is_local"] = is_local
        if begin_date:
            kwargs["begin_date"] = begin_date
        if end_date:
            kwargs["end_date"] = end_date
        return df_to_records(self._get_ad().InfoData().get_option_std_ctr_specs(code_list, **kwargs))

    def get_option_mon_ctr_specs(
        self, code_list: List[str],
        local_path: Optional[str] = None, is_local: bool = False,
        begin_date: Optional[int] = None, end_date: Optional[int] = None,
    ) -> list:
        kwargs = {}
        if local_path:
            kwargs["local_path"] = local_path
        if is_local:
            kwargs["is_local"] = is_local
        if begin_date:
            kwargs["begin_date"] = begin_date
        if end_date:
            kwargs["end_date"] = end_date
        return df_to_records(self._get_ad().InfoData().get_option_mon_ctr_specs(code_list, **kwargs))

    # ==================== 国债 ====================

    def get_treasury(
        self, term_list: List[str],
        local_path: Optional[str] = None, is_local: bool = False,
        begin_date: Optional[int] = None, end_date: Optional[int] = None,
    ) -> list:
        kwargs = {}
        if local_path:
            kwargs["local_path"] = local_path
        if is_local:
            kwargs["is_local"] = is_local
        if begin_date:
            kwargs["begin_date"] = begin_date
        if end_date:
            kwargs["end_date"] = end_date
        return df_to_records(self._get_ad().InfoData().get_treasury_yield(term_list, **kwargs))


client = AmazingDataClient()
