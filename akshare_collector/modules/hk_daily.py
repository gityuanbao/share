"""
模块 7：港股日线（港股通标的，约 500 只，前复权，2020 至今）
每只股票保存为 data/hk_stock/daily/{code}_daily.csv
"""
import os
import akshare as ak
import pandas as pd
from tqdm import tqdm

import config
from utils.helpers import logger, log_error, retry, sleep, already_done, save_csv


@retry
def _fetch_hk_daily(code: str) -> pd.DataFrame:
    """使用新浪港股接口（避开被代理拦截的东财接口）"""
    df = ak.stock_hk_daily(symbol=code, adjust="qfq")
    sleep()
    if df is not None and not df.empty:
        df["date"] = pd.to_datetime(df["date"])
        start = pd.to_datetime(config.START_DATE, format="%Y%m%d")
        df = df[df["date"] >= start].reset_index(drop=True)
        df["date"] = df["date"].dt.strftime("%Y-%m-%d")
    return df


def _load_hk_codes() -> list[str]:
    path = os.path.join(config.DIRS["hk_info"], "hk_connect.csv")
    if not os.path.exists(path):
        logger.warning("  hk_connect.csv 不存在，请先运行 stock_info 模块")
        return []
    df = pd.read_csv(path, dtype=str)
    # stock_hk_ggt_components_em 返回的列名为 '代码'
    col = "代码" if "代码" in df.columns else df.columns[0]
    codes = df[col].tolist()
    return [c.zfill(5) for c in codes]


def run():
    logger.info("=== [hk_daily] 开始采集港股通日线行情 ===")
    codes = _load_hk_codes()
    if not codes:
        logger.error("  港股通列表为空，跳过")
        return

    success, skip, fail = 0, 0, 0
    for code in tqdm(codes, desc="港股日线"):
        out = os.path.join(config.DIRS["hk_daily"], f"{code}_daily.csv")
        if already_done(out):
            skip += 1
            continue
        try:
            df = _fetch_hk_daily(code)
            if df is None or df.empty:
                log_error("hk_daily", code, ValueError("空数据"))
                fail += 1
                continue
            save_csv(df, out, "hk_daily", code)
            success += 1
        except Exception as e:
            log_error("hk_daily", code, e)
            logger.debug(f"  {code} 港股日线失败: {e}")
            fail += 1

    logger.info(f"=== [hk_daily] 完成：成功{success} 跳过{skip} 失败{fail} ===\n")
