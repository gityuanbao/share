"""
模块 8：宏观经济指标（全9类）
CPI / PPI / PMI制造 / PMI非制造 / GDP / M2 / 外汇储备 / 进出口 / 工业增加值
每类单独保存一个 CSV
"""
import os
import akshare as ak
import pandas as pd

import config
from utils.helpers import logger, log_error, retry, sleep, already_done, save_csv


# 接口映射表：(文件名, 调用函数, 描述)
MACRO_TASKS = [
    ("cpi.csv",                  lambda: ak.macro_china_cpi(),                        "CPI 居民消费价格指数"),
    ("ppi.csv",                  lambda: ak.macro_china_ppi(),                        "PPI 生产者价格指数"),
    ("pmi_manufacturing.csv",    lambda: ak.macro_china_pmi(),                        "PMI 制造业"),
    ("pmi_non_manufacturing.csv",lambda: ak.macro_china_non_man_pmi(),               "PMI 非制造业"),
    ("gdp.csv",                  lambda: ak.macro_china_gdp(),                        "GDP 季度国内生产总值"),
    ("m2.csv",                   lambda: ak.macro_china_money_supply(),               "M2 货币供应量"),
    ("fx_reserve.csv",           lambda: ak.macro_china_foreign_exchange_gold(),      "外汇储备 & 黄金储备"),
    ("exports_yoy.csv",          lambda: ak.macro_china_exports_yoy(),               "出口金额（同比）"),
    ("imports_yoy.csv",          lambda: ak.macro_china_imports_yoy(),               "进口金额（同比）"),
    ("trade_balance.csv",        lambda: ak.macro_china_trade_balance(),             "贸易差额"),
    ("industrial_output.csv",    lambda: ak.macro_china_industrial_production_yoy(), "工业增加值（同比）"),
]


def run():
    logger.info("=== [macro] 开始采集宏观经济指标 ===")
    for fname, fn, desc in MACRO_TASKS:
        out = os.path.join(config.DIRS["macro"], fname)
        if already_done(out):
            logger.info(f"  已存在，跳过: {fname}")
            continue
        try:
            df = fn()
            sleep()
            if df is None or df.empty:
                log_error("macro", fname, ValueError("空数据"))
                logger.warning(f"  {desc} 返回空数据")
                continue
            save_csv(df, out, "macro", fname)
            logger.info(f"  {desc}：{len(df)} 行 → {fname}")
        except Exception as e:
            log_error("macro", fname, e)
            logger.error(f"  {desc} 失败: {e}")
    logger.info("=== [macro] 完成 ===\n")
