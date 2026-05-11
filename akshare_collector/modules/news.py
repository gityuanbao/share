"""
模块 9：财经新闻（近 2 年，2024-01-01 至今）
- 东方财富 CLS 电报快讯
- CCTV 财经新闻（按日期逐日拉取）
"""
import os
from datetime import date, timedelta
import akshare as ak
import pandas as pd
from tqdm import tqdm

import config
from utils.helpers import logger, log_error, retry, sleep, already_done, save_csv

# 新闻只取近 2 年
NEWS_START = "20240101"
NEWS_END   = config.END_DATE


@retry
def _fetch_cls_news() -> pd.DataFrame:
    """CLS 财联社电报，取最近全量（接口不支持按日期过滤，取后过滤）"""
    df = ak.stock_info_global_cls(symbol="全部")
    sleep()
    return df


@retry
def _fetch_cctv_news(date_str: str) -> pd.DataFrame:
    """CCTV 财经新闻，date_str 格式 'YYYYMMDD'"""
    df = ak.news_cctv(date=date_str)
    sleep()
    return df


def _date_range(start: str, end: str):
    """生成 YYYYMMDD 格式的日期列表。"""
    s = date(int(start[:4]), int(start[4:6]), int(start[6:]))
    e = date(int(end[:4]),   int(end[4:6]),   int(end[6:]))
    while s <= e:
        yield s.strftime("%Y%m%d")
        s += timedelta(days=1)


def run():
    logger.info("=== [news] 开始采集财经新闻 ===")

    # 1. CLS 电报快讯
    cls_out = os.path.join(config.DIRS["news"], "cls_telegraph.csv")
    if not already_done(cls_out):
        try:
            df = _fetch_cls_news()
            # 过滤 2024 年之后
            if "时间" in df.columns:
                df = df[df["时间"] >= "2024"]
            save_csv(df, cls_out, "news", "cls")
            logger.info(f"  CLS电报：{len(df)} 条 → {cls_out}")
        except Exception as e:
            log_error("news", "cls", e)
            logger.error(f"  CLS电报获取失败: {e}")
    else:
        logger.info(f"  已存在，跳过: cls_telegraph.csv")

    # 2. CCTV 财经新闻（逐日拉取，汇总到一个文件）
    cctv_out = os.path.join(config.DIRS["news"], "cctv_news.csv")
    if not already_done(cctv_out):
        all_rows = []
        dates = list(_date_range(NEWS_START, NEWS_END))
        for d in tqdm(dates, desc="CCTV新闻"):
            try:
                df = _fetch_cctv_news(d)
                if df is not None and not df.empty:
                    df["date"] = d
                    all_rows.append(df)
            except Exception as e:
                log_error("news", f"cctv_{d}", e)
        if all_rows:
            merged = pd.concat(all_rows, ignore_index=True)
            save_csv(merged, cctv_out, "news", "cctv")
            logger.info(f"  CCTV财经：{len(merged)} 条 → {cctv_out}")
        else:
            logger.warning("  CCTV新闻全部为空")
    else:
        logger.info(f"  已存在，跳过: cctv_news.csv")

    logger.info("=== [news] 完成 ===\n")
