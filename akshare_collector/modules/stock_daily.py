"""
模块 2：A 股日线行情（全量 5500 只，前复权，2020 至今）
每只股票单独保存为 data/stock/daily/{code}_daily.csv

接口策略：优先新浪（稳定，无网络限制），失败时备用东方财富。
新浪接口代码格式：sz000001 / sh600519
"""
import os
import akshare as ak
import pandas as pd
from tqdm import tqdm

import config
from utils.helpers import logger, log_error, retry, sleep, already_done, save_csv


def _sina_code(code: str) -> str:
    """将6位纯数字代码转为新浪格式：60/68开头→sh，其余→sz"""
    return ("sh" if code.startswith(("60", "68")) else "sz") + code


@retry
def _fetch_daily(code: str) -> pd.DataFrame:
    """优先用新浪接口（稳定），失败备用东方财富。"""
    try:
        df = ak.stock_zh_a_daily(symbol=_sina_code(code), adjust="qfq")
        sleep()
        if df is not None and not df.empty:
            # 统一过滤时间范围
            df["date"] = pd.to_datetime(df["date"])
            start = pd.to_datetime(config.START_DATE, format="%Y%m%d")
            df = df[df["date"] >= start].reset_index(drop=True)
            df["date"] = df["date"].dt.strftime("%Y-%m-%d")
            return df
    except Exception:
        pass
    # 备用：东方财富
    df = ak.stock_zh_a_hist(
        symbol=code, period="daily",
        start_date=config.START_DATE, end_date=config.END_DATE,
        adjust="qfq",
    )
    sleep()
    return df


def _load_stock_list() -> list[str]:
    info_path = os.path.join(config.DIRS["stock_info"], "stock_info.csv")
    if not os.path.exists(info_path):
        logger.warning("  stock_info.csv 不存在，请先运行 stock_info 模块")
        return []
    df = pd.read_csv(info_path, dtype=str)
    # 列名可能是 'code' 或 '代码'
    col = "code" if "code" in df.columns else df.columns[0]
    return df[col].tolist()


def run():
    logger.info("=== [stock_daily] 开始采集 A 股日线行情 ===")
    codes = _load_stock_list()
    if not codes:
        logger.error("  股票列表为空，跳过")
        return

    success, skip, fail = 0, 0, 0
    for code in tqdm(codes, desc="A股日线"):
        out = os.path.join(config.DIRS["stock_daily"], f"{code}_daily.csv")
        if already_done(out):
            skip += 1
            continue
        try:
            df = _fetch_daily(code)
            if df is None or df.empty:
                log_error("stock_daily", code, ValueError("返回空数据"))
                fail += 1
                continue
            save_csv(df, out, "stock_daily", code)
            success += 1
        except Exception as e:
            log_error("stock_daily", code, e)
            logger.debug(f"  {code} 失败: {e}")
            fail += 1

    logger.info(f"=== [stock_daily] 完成：成功{success} 跳过{skip} 失败{fail} ===\n")
