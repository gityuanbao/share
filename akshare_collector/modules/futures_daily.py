"""
模块 6：期货主力合约日线（全量约 60 个主力品种，2020 至今）
每个品种保存为 data/futures/daily/{symbol}_daily.csv
"""
import os
import akshare as ak
import pandas as pd
from tqdm import tqdm

import config
from utils.helpers import logger, log_error, retry, sleep, already_done, save_csv


# 手动维护主力合约映射（新浪格式），确保稳定可用
FUTURES_SYMBOLS = [
    # 金属
    "螺纹钢主力", "热轧卷板主力", "铁矿石主力", "焦煤主力", "焦炭主力",
    "铜主力", "铝主力", "锌主力", "铅主力", "镍主力", "锡主力",
    "不锈钢主力", "硅铁主力", "锰硅主力",
    # 能源化工
    "原油主力", "燃料油主力", "沥青主力", "天然橡胶主力", "合成橡胶主力",
    "甲醇主力", "PTA主力", "乙二醇主力", "苯乙烯主力", "液化石油气主力",
    "低硫燃料油主力", "纯碱主力", "烧碱主力",
    # 农产品
    "豆一主力", "豆二主力", "豆油主力", "豆粕主力", "玉米主力",
    "玉米淀粉主力", "棕榈油主力", "菜籽油主力", "菜粕主力",
    "棉花主力", "白糖主力", "苹果主力", "红枣主力", "花生主力",
    "鸡蛋主力", "生猪主力",
    # 金融
    "沪深300股指主力", "上证50股指主力", "中证500股指主力",
    "10年期国债主力", "5年期国债主力", "2年期国债主力",
    # 贵金属
    "黄金主力", "白银主力",
    # 其他
    "玻璃主力", "纸浆主力", "木材主力", "尿素主力",
]


@retry
def _fetch_futures(symbol: str) -> pd.DataFrame:
    df = ak.futures_main_sina(symbol=symbol, start_date=config.START_DATE, end_date=config.END_DATE)
    sleep()
    return df


def run():
    logger.info("=== [futures_daily] 开始采集期货主力合约日线 ===")

    # 同时保存品种列表
    info_out = os.path.join(config.DIRS["futures_info"], "futures_symbols.csv")
    if not already_done(info_out):
        pd.DataFrame({"symbol": FUTURES_SYMBOLS}).to_csv(info_out, index=False, encoding="utf-8-sig")

    success, skip, fail = 0, 0, 0
    for symbol in tqdm(FUTURES_SYMBOLS, desc="期货日线"):
        safe_name = symbol.replace("/", "_").replace(" ", "")
        out = os.path.join(config.DIRS["futures_daily"], f"{safe_name}_daily.csv")
        if already_done(out):
            skip += 1
            continue
        try:
            df = _fetch_futures(symbol)
            if df is None or df.empty:
                log_error("futures_daily", symbol, ValueError("空数据"))
                fail += 1
                continue
            save_csv(df, out, "futures_daily", symbol)
            success += 1
        except Exception as e:
            log_error("futures_daily", symbol, e)
            logger.debug(f"  {symbol} 失败: {e}")
            fail += 1

    logger.info(f"=== [futures_daily] 完成：成功{success} 跳过{skip} 失败{fail} ===\n")
