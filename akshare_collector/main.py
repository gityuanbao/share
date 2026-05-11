"""
主入口：按优先级顺序调度所有采集模块。
每个模块独立运行，单个失败不影响后续。

用法：
    python main.py              # 运行全部已启用模块
    python main.py stock_daily  # 只运行指定模块
"""
import sys
import time
from datetime import datetime

import config
from utils.helpers import logger, ensure_dirs

# 按执行顺序注册所有模块
MODULES = [
    ("stock_info",    "modules.stock_info",         "股票基础信息（A股列表/沪深300/中证500/港股通）"),
    ("stock_daily",   "modules.stock_daily",        "A股日线行情（全量5500只，前复权）"),
    ("stock_minute",  "modules.stock_minute",       "A股5分钟线（仅沪深300，前复权）"),
    ("fundamentals",  "modules.stock_fundamentals", "基本面财务（沪深300+中证500，3张表）"),
    ("capital_flow",  "modules.capital_flow",       "资金流向（北向资金/融资融券/行业概念流）"),
    ("futures_daily", "modules.futures_daily",      "期货主力合约日线（约60品种）"),
    ("hk_daily",      "modules.hk_daily",           "港股日线（港股通约500只，前复权）"),
    ("macro",         "modules.macro",              "宏观经济指标（CPI/PPI/PMI/GDP/M2等9类）"),
    ("news",          "modules.news",               "财经新闻（CLS电报+CCTV，近2年）"),
    ("announcement",  "modules.announcement",       "公司公告元信息（沪深300）"),
    ("sector",        "modules.sector",             "行业板块行情（东方财富全行业日线）"),
]


def _import_and_run(module_path: str):
    import importlib
    mod = importlib.import_module(module_path)
    mod.run()


def main():
    t0 = time.time()
    logger.info("=" * 60)
    logger.info(f"  AKShare 数据采集启动  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"  时间范围: {config.START_DATE} → {config.END_DATE}")
    logger.info("=" * 60 + "\n")

    ensure_dirs()

    # 过滤：命令行指定了模块名则只跑那个
    target = sys.argv[1] if len(sys.argv) > 1 else None

    for key, path, desc in MODULES:
        # 命令行过滤
        if target and key != target:
            continue
        # 配置开关过滤
        if not config.ENABLE.get(key, True):
            logger.info(f"[跳过] {key}（已在 config 中禁用）")
            continue

        logger.info(f"▶ 启动模块: {key} — {desc}")
        t_mod = time.time()
        try:
            _import_and_run(path)
        except Exception as e:
            logger.error(f"  模块 {key} 异常退出: {e}")
        elapsed = time.time() - t_mod
        logger.info(f"  耗时: {elapsed/60:.1f} 分钟\n")

    total = time.time() - t0
    logger.info("=" * 60)
    logger.info(f"  全部模块完成  总耗时: {total/3600:.2f} 小时")
    logger.info(f"  错误日志: {config.ERROR_LOG}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
