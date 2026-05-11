"""
模块 11：行业/板块行情数据
- 同花顺行业板块历史日行情（2020 至今，避开被代理拦截的东财接口）
- 行业列表自动拉取，无需硬编码
"""
import os
import akshare as ak
import pandas as pd
from tqdm import tqdm

import config
from utils.helpers import logger, log_error, retry, sleep, already_done, save_csv


@retry
def _fetch_board_list() -> pd.DataFrame:
    """同花顺行业板块列表，返回 name/code 两列，共约90个板块"""
    df = ak.stock_board_industry_name_ths()
    sleep()
    return df


@retry
def _fetch_board_hist(name: str) -> pd.DataFrame:
    """同花顺行业板块历史指数数据"""
    df = ak.stock_board_industry_index_ths(
        symbol=name,
        start_date=config.START_DATE,
        end_date=config.END_DATE,
    )
    sleep()
    return df


def run():
    logger.info("=== [sector] 开始采集行业板块行情 ===")

    # 获取所有行业板块名称
    boards_out = os.path.join(config.DIRS["sector"], "board_list.csv")
    try:
        boards_df = _fetch_board_list()
        save_csv(boards_df, boards_out, "sector", "board_list")
        names = boards_df.iloc[:, 0].tolist()
        logger.info(f"  共 {len(names)} 个行业板块")
    except Exception as e:
        log_error("sector", "board_list", e)
        logger.error(f"  获取板块列表失败: {e}")
        return

    # 逐板块拉历史行情
    success, skip, fail = 0, 0, 0
    for name in tqdm(names, desc="板块行情"):
        safe = name.replace("/", "_").replace(" ", "")
        out = os.path.join(config.DIRS["sector"], f"{safe}_daily.csv")
        if already_done(out):
            skip += 1
            continue
        try:
            df = _fetch_board_hist(name)
            if df is None or df.empty:
                log_error("sector", name, ValueError("空数据"))
                fail += 1
                continue
            save_csv(df, out, "sector", name)
            success += 1
        except Exception as e:
            log_error("sector", name, e)
            logger.debug(f"  {name} 板块行情失败: {e}")
            fail += 1

    logger.info(f"=== [sector] 完成：成功{success} 跳过{skip} 失败{fail} ===\n")
