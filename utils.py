import time
from functools import wraps
from typing import Dict, Any, Optional
import pandas as pd


class SimpleCache:
    """简单的内存缓存"""

    def __init__(self):
        self._cache: Dict[str, tuple[float, Any]] = {}

    def get(self, key: str) -> Optional[Any]:
        if key in self._cache:
            expire_at, value = self._cache[key]
            if time.time() < expire_at:
                return value
            del self._cache[key]
        return None

    def set(self, key: str, value: Any, ttl: int):
        self._cache[key] = (time.time() + ttl, value)

    def clear(self):
        self._cache.clear()


cache = SimpleCache()


def cached(ttl: int):
    """缓存装饰器"""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            key_parts = [func.__name__] + [str(a) for a in args] + [f"{k}={v}" for k, v in sorted(kwargs.items())]
            key = ":".join(key_parts)
            result = cache.get(key)
            if result is not None:
                return result
            result = func(*args, **kwargs)
            cache.set(key, result, ttl)
            return result

        return wrapper

    return decorator


def df_to_records(df: pd.DataFrame) -> list:
    """DataFrame 转字典列表"""
    if df is None or df.empty:
        return []
    df_copy = df.copy()
    for col in df_copy.select_dtypes(include=["datetime64"]).columns:
        df_copy[col] = df_copy[col].astype(str)
    if df_copy.index.name is not None or not isinstance(df_copy.index, pd.RangeIndex):
        df_copy = df_copy.reset_index()
        for col in df_copy.select_dtypes(include=["datetime64"]).columns:
            df_copy[col] = df_copy[col].astype(str)
    return df_copy.to_dict(orient="records")
