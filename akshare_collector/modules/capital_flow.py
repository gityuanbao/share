"""
模块 5：资金流向
- 北向/南向资金（沪深港通每日净买入）
- 融资融券汇总（每日市场合计数据）
- 行业板块资金流排行
- 概念板块资金流排行
"""
import os
import akshare as ak
import pandas as pd

import config
from utils.helpers import logger, log_error, retry, sleep, already_done, save_csv


@retry
def _fetch_north_south(direction: str) -> pd.DataFrame:
    """direction: '沪股通' / '深股通' / '沪深港通'"""
    df = ak.stock_hsgt_hist_em(symbol=direction)
    sleep()
    return df


@retry
def _fetch_margin() -> pd.DataFrame:
    """融资融券市场汇总 - 使用上交所官方接口"""
    df = ak.stock_margin_sse()
    sleep()
    return df


@retry
def _fetch_industry_flow(indicator: str) -> pd.DataFrame:
    """indicator: '今日' / '3日' / '5日' / '10日'"""
    df = ak.stock_sector_fund_flow_rank(indicator=indicator, sector_type="行业资金流")
    sleep()
    return df


@retry
def _fetch_concept_flow(indicator: str) -> pd.DataFrame:
    df = ak.stock_sector_fund_flow_rank(indicator=indicator, sector_type="概念资金流")
    sleep()
    return df


def run():
    logger.info("=== [capital_flow] 开始采集资金流向数据 ===")

    # 1. 北向/南向资金
    for direction in ["沪股通", "深股通"]:
        fname = direction.replace("/", "_") + "_hist.csv"
        out = os.path.join(config.DIRS["capital_flow"], fname)
        if not already_done(out):
            try:
                df = _fetch_north_south(direction)
                save_csv(df, out, "capital_flow", direction)
                logger.info(f"  {direction}：{len(df)} 行 → {out}")
            except Exception as e:
                log_error("capital_flow", direction, e)
                logger.error(f"  {direction} 失败: {e}")
        else:
            logger.info(f"  已存在，跳过: {out}")

    # 2. 融资融券汇总
    out_margin = os.path.join(config.DIRS["capital_flow"], "margin_summary.csv")
    if not already_done(out_margin):
        try:
            df = _fetch_margin()
            save_csv(df, out_margin, "capital_flow", "margin")
            logger.info(f"  融资融券汇总：{len(df)} 行 → {out_margin}")
        except Exception as e:
            log_error("capital_flow", "margin", e)
            logger.error(f"  融资融券获取失败: {e}")
    else:
        logger.info(f"  已存在，跳过: {out_margin}")

    # 3. 行业资金流（各周期）
    for ind in ["今日", "3日", "5日", "10日"]:
        out = os.path.join(config.DIRS["sector"], f"industry_flow_{ind}.csv")
        if not already_done(out):
            try:
                df = _fetch_industry_flow(ind)
                save_csv(df, out, "sector_flow", f"industry_{ind}")
                logger.info(f"  行业资金流-{ind}：{len(df)} 行")
            except Exception as e:
                log_error("sector_flow", f"industry_{ind}", e)
                logger.error(f"  行业资金流-{ind} 失败: {e}")
        else:
            logger.info(f"  已存在，跳过: industry_flow_{ind}.csv")

    # 4. 概念资金流（各周期）
    for ind in ["今日", "3日", "5日", "10日"]:
        out = os.path.join(config.DIRS["sector"], f"concept_flow_{ind}.csv")
        if not already_done(out):
            try:
                df = _fetch_concept_flow(ind)
                save_csv(df, out, "sector_flow", f"concept_{ind}")
                logger.info(f"  概念资金流-{ind}：{len(df)} 行")
            except Exception as e:
                log_error("sector_flow", f"concept_{ind}", e)
                logger.error(f"  概念资金流-{ind} 失败: {e}")
        else:
            logger.info(f"  已存在，跳过: concept_flow_{ind}.csv")

    logger.info("=== [capital_flow] 完成 ===\n")
