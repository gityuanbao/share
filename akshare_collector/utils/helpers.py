"""
工具模块：日志、重试、限速、进度
"""
import os
import time
import logging
import functools
from datetime import datetime

import config


# ── 日志初始化 ────────────────────────────────────────────────
def _init_logger() -> logging.Logger:
    os.makedirs(config.LOG_DIR, exist_ok=True)
    fmt = "%(asctime)s [%(levelname)s] %(message)s"
    logging.basicConfig(
        level=logging.INFO,
        format=fmt,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(
                os.path.join(config.LOG_DIR,
                             f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
                encoding="utf-8",
            ),
        ],
    )
    return logging.getLogger("collector")

logger = _init_logger()


def log_error(module: str, key: str, exc: Exception) -> None:
    """把失败条目追加写入 errors.log，不中断主流程。"""
    os.makedirs(config.LOG_DIR, exist_ok=True)
    with open(config.ERROR_LOG, "a", encoding="utf-8") as f:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"{ts}\t{module}\t{key}\t{type(exc).__name__}: {exc}\n")


# ── 重试装饰器 ─────────────────────────────────────────────────
def retry(func):
    """指数退避重试，最多 config.RETRY_TIMES 次。"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        last_exc = None
        for attempt in range(1, config.RETRY_TIMES + 1):
            try:
                return func(*args, **kwargs)
            except Exception as exc:
                last_exc = exc
                wait = attempt * config.RETRY_BACKOFF
                logger.warning(f"[retry {attempt}/{config.RETRY_TIMES}] "
                               f"{func.__name__} 失败: {exc}，{wait:.1f}s 后重试")
                time.sleep(wait)
        raise last_exc
    return wrapper


# ── 限速工具 ──────────────────────────────────────────────────
def sleep():
    """每次 API 调用后调用，避免被限速。"""
    time.sleep(config.REQUEST_DELAY)


# ── 目录确保 & CSV 断点续传 ────────────────────────────────────
def ensure_dirs():
    for d in config.DIRS.values():
        os.makedirs(d, exist_ok=True)


def already_done(filepath: str) -> bool:
    """文件存在且非空则视为已完成，跳过。"""
    return os.path.exists(filepath) and os.path.getsize(filepath) > 0


def save_csv(df, filepath: str, module: str = "", key: str = "") -> bool:
    """保存 DataFrame 为 CSV，失败时记录日志并返回 False。"""
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        df.to_csv(filepath, index=False, encoding="utf-8-sig")
        return True
    except Exception as exc:
        log_error(module, key, exc)
        logger.error(f"保存失败 {filepath}: {exc}")
        return False
