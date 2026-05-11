"""
全局配置
"""
import os
from datetime import date

# ── 时间范围 ────────────────────────────────────────────────
START_DATE = "20200101"
END_DATE   = date.today().strftime("%Y%m%d")

# ── 输出根目录 ───────────────────────────────────────────────
BASE_DIR = os.path.join(os.path.dirname(__file__), "data")

DIRS = {
    "stock_daily"    : os.path.join(BASE_DIR, "stock", "daily"),
    "stock_minute"   : os.path.join(BASE_DIR, "stock", "minute_5m"),
    "stock_info"     : os.path.join(BASE_DIR, "stock"),
    "fundamentals"   : os.path.join(BASE_DIR, "stock", "fundamentals"),
    "capital_flow"   : os.path.join(BASE_DIR, "stock", "capital_flow"),
    "futures_daily"  : os.path.join(BASE_DIR, "futures", "daily"),
    "futures_info"   : os.path.join(BASE_DIR, "futures"),
    "hk_daily"       : os.path.join(BASE_DIR, "hk_stock", "daily"),
    "hk_info"        : os.path.join(BASE_DIR, "hk_stock"),
    "macro"          : os.path.join(BASE_DIR, "macro"),
    "news"           : os.path.join(BASE_DIR, "news"),
    "announcement"   : os.path.join(BASE_DIR, "announcement"),
    "sector"         : os.path.join(BASE_DIR, "sector"),
}

# ── 请求频率控制 ──────────────────────────────────────────────
REQUEST_DELAY   = 0.4   # 每次 API 调用后等待秒数
RETRY_TIMES     = 3     # 失败最多重试次数
RETRY_BACKOFF   = 1.5   # 退避倍率（第n次失败等待 n*RETRY_BACKOFF 秒）

# ── 日志 ─────────────────────────────────────────────────────
LOG_DIR   = os.path.join(os.path.dirname(__file__), "logs")
ERROR_LOG = os.path.join(LOG_DIR, "errors.log")

# ── 功能开关（False = 跳过该模块）──────────────────────────────
ENABLE = {
    "stock_info"      : True,
    "stock_daily"     : True,
    "stock_minute"    : True,   # 仅沪深300
    "fundamentals"    : True,   # 沪深300+中证500
    "capital_flow"    : True,
    "north_south"     : True,
    "margin"          : True,
    "futures_daily"   : True,
    "hk_daily"        : True,   # 港股通标的
    "macro"           : True,
    "news"            : True,
    "announcement"    : True,   # 仅沪深300
    "sector_flow"     : True,
}
