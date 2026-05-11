"""
模块 1：股票基础信息
- 全量 A 股代码 + 名称
- 沪深300 / 中证500 成分股列表（供其他模块引用）
- 港股通标的列表
"""
import os
import akshare as ak
import pandas as pd

import config
from utils.helpers import logger, log_error, retry, sleep, already_done, save_csv


@retry
def _fetch_a_stock_list() -> pd.DataFrame:
    df = ak.stock_info_a_code_name()
    sleep()
    return df


@retry
def _fetch_hs300() -> pd.DataFrame:
    df = ak.index_stock_cons(symbol="000300")
    sleep()
    return df


@retry
def _fetch_zz500() -> pd.DataFrame:
    df = ak.index_stock_cons(symbol="000905")
    sleep()
    return df


@retry
def _fetch_hk_connect() -> pd.DataFrame:
    """用新浪港股全量列表（含代码/名称），过滤主板（5位代码）。"""
    df = ak.stock_hk_spot()
    sleep()
    # 只保留代码和中英文名称两列，去重
    keep = [c for c in ["代码", "中文名称", "英文名称"] if c in df.columns]
    return df[keep].drop_duplicates(subset=["代码"]) if keep else df


def run():
    logger.info("=== [stock_info] 开始采集股票基础信息 ===")

    # 1. 全量 A 股列表
    out = os.path.join(config.DIRS["stock_info"], "stock_info.csv")
    if not already_done(out):
        try:
            df = _fetch_a_stock_list()
            save_csv(df, out, "stock_info", "a_stock_list")
            logger.info(f"  全量A股：{len(df)} 只 → {out}")
        except Exception as e:
            log_error("stock_info", "a_stock_list", e)
            logger.error(f"  全量A股获取失败: {e}")
    else:
        logger.info(f"  已存在，跳过: {out}")

    # 2. 沪深300 成分股
    out300 = os.path.join(config.DIRS["stock_info"], "hs300_cons.csv")
    if not already_done(out300):
        try:
            df = _fetch_hs300()
            save_csv(df, out300, "stock_info", "hs300")
            logger.info(f"  沪深300成分股：{len(df)} 只 → {out300}")
        except Exception as e:
            log_error("stock_info", "hs300", e)
            logger.error(f"  沪深300获取失败: {e}")
    else:
        logger.info(f"  已存在，跳过: {out300}")

    # 3. 中证500 成分股
    out500 = os.path.join(config.DIRS["stock_info"], "zz500_cons.csv")
    if not already_done(out500):
        try:
            df = _fetch_zz500()
            save_csv(df, out500, "stock_info", "zz500")
            logger.info(f"  中证500成分股：{len(df)} 只 → {out500}")
        except Exception as e:
            log_error("stock_info", "zz500", e)
            logger.error(f"  中证500获取失败: {e}")
    else:
        logger.info(f"  已存在，跳过: {out500}")

    # 4. 港股通标的
    out_hk = os.path.join(config.DIRS["hk_info"], "hk_connect.csv")
    if not already_done(out_hk):
        try:
            df = _fetch_hk_connect()
            save_csv(df, out_hk, "stock_info", "hk_connect")
            logger.info(f"  港股通标的：{len(df)} 只 → {out_hk}")
        except Exception as e:
            log_error("stock_info", "hk_connect", e)
            logger.error(f"  港股通获取失败: {e}")
    else:
        logger.info(f"  已存在，跳过: {out_hk}")

    logger.info("=== [stock_info] 完成 ===\n")
