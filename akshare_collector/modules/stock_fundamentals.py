"""
模块 4：基本面财务数据（沪深300 + 中证500 成分股，约 800 只）
- 利润表（income）
- 资产负债表（balance）
- 现金流量表（cashflow）
每只股票三张表各存一个 CSV
"""
import os
import akshare as ak
import pandas as pd
from tqdm import tqdm

import config
from utils.helpers import logger, log_error, retry, sleep, already_done, save_csv


@retry
def _fetch_income(code: str) -> pd.DataFrame:
    df = ak.stock_financial_report_sina(stock=code, symbol="利润表")
    sleep()
    return df


@retry
def _fetch_balance(code: str) -> pd.DataFrame:
    df = ak.stock_financial_report_sina(stock=code, symbol="资产负债表")
    sleep()
    return df


@retry
def _fetch_cashflow(code: str) -> pd.DataFrame:
    df = ak.stock_financial_report_sina(stock=code, symbol="现金流量表")
    sleep()
    return df


def _load_universe() -> list[str]:
    """合并沪深300 + 中证500，去重，约 800 只。"""
    codes = set()
    for fname, col_guess in [("hs300_cons.csv", "品种代码"), ("zz500_cons.csv", "品种代码")]:
        path = os.path.join(config.DIRS["stock_info"], fname)
        if not os.path.exists(path):
            continue
        df = pd.read_csv(path, dtype=str)
        col = col_guess if col_guess in df.columns else df.columns[0]
        codes.update(df[col].tolist())
    return list(codes)


def run():
    logger.info("=== [fundamentals] 开始采集基本面财务数据（沪深300+中证500）===")
    codes = _load_universe()
    if not codes:
        logger.error("  成分股列表为空，跳过")
        return

    fetchers = {
        "income"   : _fetch_income,
        "balance"  : _fetch_balance,
        "cashflow" : _fetch_cashflow,
    }

    success, skip, fail = 0, 0, 0
    for code in tqdm(codes, desc="基本面"):
        for name, fn in fetchers.items():
            out = os.path.join(config.DIRS["fundamentals"], f"{code}_{name}.csv")
            if already_done(out):
                skip += 1
                continue
            try:
                df = fn(code)
                if df is None or df.empty:
                    log_error("fundamentals", f"{code}_{name}", ValueError("空数据"))
                    fail += 1
                    continue
                save_csv(df, out, "fundamentals", f"{code}_{name}")
                success += 1
            except Exception as e:
                log_error("fundamentals", f"{code}_{name}", e)
                logger.debug(f"  {code} {name} 失败: {e}")
                fail += 1

    logger.info(f"=== [fundamentals] 完成：成功{success} 跳过{skip} 失败{fail} ===\n")
