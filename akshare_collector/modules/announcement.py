"""
模块 10：公司公告元信息（沪深300 成分股，2022 至今）
按日期逐日拉取全市场公告，过滤出沪深300成分股，合并后保存
接口：ak.stock_notice_report(symbol='全部', date='YYYYMMDD')
返回：代码/名称/公告标题/公告类型/公告日期/网址
"""
import os
from datetime import date, timedelta
import akshare as ak
import pandas as pd
from tqdm import tqdm

import config
from utils.helpers import logger, log_error, retry, sleep, already_done, save_csv

# 公告只取近 2 年（接口历史有限）
NOTICE_START = "20240101"
NOTICE_END = config.END_DATE


def _date_range(start: str, end: str):
    """生成 YYYYMMDD 格式的日期列表（工作日估计 + 直接用日历日）"""
    s = date(int(start[:4]), int(start[4:6]), int(start[6:]))
    e = date(int(end[:4]), int(end[4:6]), int(end[6:]))
    while s <= e:
        yield s.strftime("%Y%m%d")
        s += timedelta(days=1)


@retry
def _fetch_notice_by_date(date_str: str) -> pd.DataFrame:
    """按日期拉取全市场公告，date_str 格式 YYYYMMDD"""
    df = ak.stock_notice_report(symbol="全部", date=date_str)
    sleep()
    return df


def _load_hs300() -> set:
    path = os.path.join(config.DIRS["stock_info"], "hs300_cons.csv")
    if not os.path.exists(path):
        logger.warning("  hs300_cons.csv 不存在，请先运行 stock_info 模块")
        return set()
    df = pd.read_csv(path, dtype=str)
    col = "品种代码" if "品种代码" in df.columns else df.columns[0]
    return set(df[col].tolist())


def run():
    logger.info("=== [announcement] 开始采集沪深300 公司公告元信息 ===")

    hs300_codes = _load_hs300()
    if not hs300_codes:
        logger.error("  沪深300列表为空，跳过")
        return

    out = os.path.join(config.DIRS["announcement"], "hs300_notices.csv")
    if already_done(out):
        logger.info(f"  已存在，跳过: {out}")
        logger.info("=== [announcement] 完成 ===\n")
        return

    all_records = []
    dates = list(_date_range(NOTICE_START, NOTICE_END))
    success, fail = 0, 0

    for d in tqdm(dates, desc="公告采集"):
        try:
            df = _fetch_notice_by_date(d)
            if df is None or df.empty:
                continue
            # 过滤沪深300成分股
            code_col = "代码" if "代码" in df.columns else df.columns[0]
            # 去掉交易所后缀（如 000001 vs 000001.SZ）
            df["_clean_code"] = df[code_col].str.replace(r"\.[A-Z]+$", "", regex=True)
            df_filtered = df[df["_clean_code"].isin(hs300_codes)].drop(columns=["_clean_code"])
            if not df_filtered.empty:
                all_records.append(df_filtered)
                success += 1
        except Exception as e:
            log_error("announcement", d, e)
            fail += 1

    if all_records:
        result = pd.concat(all_records, ignore_index=True)
        save_csv(result, out, "announcement", "hs300")
        logger.info(f"  沪深300公告：共 {len(result)} 条 → {out}")
    else:
        logger.warning("  未采集到任何公告数据")

    logger.info(f"=== [announcement] 完成：成功{success}天 失败{fail}天 ===\n")
