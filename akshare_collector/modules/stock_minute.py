"""
模块 3：A 股 5 分钟线（仅沪深300 成分股，2020 至今）
每只股票保存为 data/stock/minute_5m/{code}_5m.csv
接口：新浪分钟线（ak.stock_zh_a_minute），稳定可用。
"""
import os
import akshare as ak
import pandas as pd
from tqdm import tqdm

import config
from utils.helpers import logger, log_error, retry, sleep, already_done, save_csv


def _sina_code(code: str) -> str:
    return ("sh" if code.startswith(("60", "68")) else "sz") + code


@retry
def _fetch_minute(code: str) -> pd.DataFrame:
    df = ak.stock_zh_a_minute(symbol=_sina_code(code), period="5", adjust="qfq")
    sleep()
    if df is not None and not df.empty:
        df["day"] = pd.to_datetime(df["day"])
        start = pd.to_datetime(config.START_DATE, format="%Y%m%d")
        df = df[df["day"] >= start].reset_index(drop=True)
        df["day"] = df["day"].astype(str)
    return df


def _load_hs300() -> list[str]:
    path = os.path.join(config.DIRS["stock_info"], "hs300_cons.csv")
    if not os.path.exists(path):
        logger.warning("  hs300_cons.csv 不存在，请先运行 stock_info 模块")
        return []
    df = pd.read_csv(path, dtype=str)
    col = "品种代码" if "品种代码" in df.columns else df.columns[0]
    return df[col].tolist()


def run():
    logger.info("=== [stock_minute] 开始采集沪深300 5分钟线 ===")
    codes = _load_hs300()
    if not codes:
        logger.error("  沪深300列表为空，跳过")
        return

    success, skip, fail = 0, 0, 0
    for code in tqdm(codes, desc="5分钟线"):
        out = os.path.join(config.DIRS["stock_minute"], f"{code}_5m.csv")
        if already_done(out):
            skip += 1
            continue
        try:
            df = _fetch_minute(code)
            if df is None or df.empty:
                log_error("stock_minute", code, ValueError("返回空数据"))
                fail += 1
                continue
            save_csv(df, out, "stock_minute", code)
            success += 1
        except Exception as e:
            log_error("stock_minute", code, e)
            logger.debug(f"  {code} 分钟线失败: {e}")
            fail += 1

    logger.info(f"=== [stock_minute] 完成：成功{success} 跳过{skip} 失败{fail} ===\n")
