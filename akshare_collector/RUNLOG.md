# 执行全过程复盘

> 记录从启动采集到排障修复的真实过程，作为下次运行的参考。
> 时间：2026-04-17

---

## 一、启动前发现：宏观模块接口名不对

脚本写完后先单独测试了 `macro` 模块，连续碰到三个 `AttributeError`：

| 原代码 | 实际正确接口名 |
|--------|--------------|
| `ak.macro_china_pmi_manufacturing()` | `ak.macro_china_pmi()` |
| `ak.macro_china_pmi_non_manufacturing()` | `ak.macro_china_non_man_pmi()` |
| `ak.macro_china_import_export()` | 不存在，需拆为三个接口：`macro_china_exports_yoy()` / `macro_china_imports_yoy()` / `macro_china_trade_balance()` |

**根因**：AKShare 1.18.x 的接口命名与旧版本有差异，直接用接口名猜测不可靠。

**修复方式**：`python3 -c "import akshare as ak; print([x for x in dir(ak) if 'pmi' in x.lower()])"` 过滤关键词，确认正确函数名后修改。

宏观模块修好后独立跑通，11 类指标全部写入 `data/macro/`。

---

## 二、港股通列表：两次接口失败

### 第一次失败
原始接口 `ak.stock_hk_connect_em()` 不存在，改为 `ak.stock_hk_ggt_components_em()`。

### 第二次失败（关键发现）
`stock_hk_ggt_components_em()` 也失败了，但错误不是 `AttributeError`，而是：

```
ProxyError: Unable to connect to proxy (push2.eastmoney.com)
RemoteDisconnected
```

这揭示了整个会话最核心的问题：**系统代理在拦截东方财富的服务器**。

**根因**：本机运行了 Clash/V2ray，监听 `127.0.0.1:7890`，Python 的 `requests` 库会自动读取系统代理，所有发往 `push2.eastmoney.com`、`push2his.eastmoney.com` 的请求全部被代理截断，返回 `RemoteDisconnected`。

**最终修复**：换用 `ak.stock_hk_spot()`，这是新浪财经的港股实时数据接口，返回全量 2745 只港股（含代码和名称），绕开了东财服务器，成功获取列表。

---

## 三、A 股日线：东财备用接口被代理拦截

`stock_daily.py` 的设计是「优先新浪，失败备用东财」。启动全量运行后，`errors.log` 里出现大量：

```
ProxyError: push2his.eastmoney.com ... RemoteDisconnected
```

这些错误来自**旧版进程**（代理问题未修复前启动的那次）。新浪接口本身工作正常，验证：

```bash
python3 -c "import akshare as ak; df = ak.stock_zh_a_daily(symbol='sz000007', adjust='qfq'); print(len(df))"
# → 7553  ✅
```

当前运行的新版进程（16:08 启动）已经使用修正后的新浪优先逻辑，运行稳定，每只股票约 1.1 秒，无新增代理错误。

---

## 四、正式启动全量采集

```bash
nohup python main.py > logs/full_run.log 2>&1 &
# PID: 32227
```

**模块1（stock_info）**：全部跳过（之前已完成），用时 0.2 分钟。

**模块2（stock_daily）**：正在运行。  
- 5506 只 A 股全量，速度 ≈ 1.1 秒/只  
- 预计约 100 分钟完成  
- 断点续传有效，之前测试跑过的股票全部跳过

---

## 五、边跑边修：提前排查后续模块

趁 stock_daily 在后台跑，提前逐一测试后续模块会调用的接口，发现并修复了 5 处问题：

### 5.1 港股日线：东财接口被代理拦截

`hk_daily.py` 原用 `ak.stock_hk_hist()`，测试确认被代理拦截：

```
ProxyError: 33.push2his.eastmoney.com ... RemoteDisconnected
```

**修复**：改用 `ak.stock_hk_daily()`（新浪财经港股历史接口），测试返回 5366 行，数据完整。

```python
# 修复前
df = ak.stock_hk_hist(symbol=code, period="daily", start_date=..., adjust="qfq")

# 修复后
df = ak.stock_hk_daily(symbol=code, adjust="qfq")
# 再手动过滤 start_date
```

### 5.2 行业板块：东财接口被代理拦截

`sector.py` 原用 `ak.stock_board_industry_name_em()` 和 `stock_board_industry_hist_em()`，两者都调用 `push2.eastmoney.com`，均被拦截。

**修复**：全部换为同花顺接口：
- `ak.stock_board_industry_name_ths()` → 90 个行业板块，成功
- `ak.stock_board_industry_index_ths(symbol=name, start_date=..., end_date=...)` → 历史指数数据，成功

### 5.3 融资融券：接口不存在

`capital_flow.py` 原用 `ak.stock_margin_sz_summary_em()`，抛 `AttributeError`。

**修复**：改为 `ak.stock_margin_sse()`（上交所官方融资融券汇总接口），返回 2000 行数据。

### 5.4 CLS 电报新闻：接口已改名

`news.py` 原用 `ak.news_em_cls_telegraph(symbol="全部")`，抛 `AttributeError`。

**修复**：改为 `ak.stock_info_global_cls(symbol="全部")`，成功获取 20 条最新电报。

### 5.5 CCTV 新闻：日期格式错误 + 公告接口逻辑重设计

- `news_cctv(date='YYYY-MM-DD')` 报错，正确格式是 `date='YYYYMMDD'`（无连字符）。
- `ak.stock_notice_report()` 不支持 `symbol=股票代码` 查询，实际是「按日期拉全市场公告」接口：`stock_notice_report(symbol='全部', date='YYYYMMDD')`。

**修复**：`announcement.py` 完全重写逻辑——改为按日期逐日拉取全市场公告，再过滤出沪深300成分股，汇总保存为一个文件 `hs300_notices.csv`。

---

## 六、全量接口验证

修复完成后，对所有用到的接口做了一次集中验证：

```
港股日线-新浪:     ✅ OK (5366 行)
行业板块列表-THS:  ✅ OK (90 行)
行业板块历史-THS:  ✅ OK (7 行，测试区间)
融资融券-SSE:      ✅ OK (2000 行)
北向资金:          ✅ OK (2651 行)
CCTV新闻:          ✅ OK (14 行)
CLS电报:           ✅ OK (20 行)
公告-按日期:       ✅ OK (11 行)
A股日线-新浪:      ✅ OK (5901 行)
A股5分钟-新浪:     ✅ OK (1970 行)
期货主力:          ✅ OK (7 行，测试区间)
财务报表-新浪:     ✅ OK (121 行)
```

所有接口全部绿灯。

---

## 七、核心规律总结

本次执行暴露了两类系统性问题，以后运行前可以提前规避：

### 规律一：东财接口 = 高风险

凡是函数名含 `_em` 后缀（East Money 缩写）的 AKShare 接口，都走 `push2.eastmoney.com` 系列域名。只要本机开了系统代理（Clash / V2ray / Surge 等），这些接口大概率失败。

**应对策略**：
1. 先检查是否有对应的新浪（`_sina`）或同花顺（`_ths`）版本
2. 没有替代时，可在运行前临时关闭系统代理，或配置代理白名单放行 `*.eastmoney.com`

### 规律二：接口名要运行时验证，不要凭经验猜

AKShare 版本迭代频繁，函数名会改变（如 `pmi_manufacturing` → `pmi`，`news_em_cls_telegraph` → `stock_info_global_cls`）。

**应对策略**：每次写新接口调用前，先用 `dir(ak)` + 关键词过滤确认函数名存在，再看 `help()` 确认参数格式。

---

## 八、当前状态（2026-04-17 16:20）

| 模块 | 状态 | 说明 |
|------|------|------|
| stock_info | ✅ 完成 | 已有缓存，跳过 |
| macro | ✅ 完成 | 11 类宏观指标全部写入 |
| stock_daily | 🔄 运行中 | 约 609/5506 (11%)，预计 ~80 分钟完成 |
| stock_minute | ⏳ 等待 | 代码已修复，等 stock_daily 完成后自动启动 |
| stock_fundamentals | ⏳ 等待 | 新浪接口，无代理问题 |
| capital_flow | ⏳ 等待 | 融资融券已修复为 SSE 接口 |
| futures_daily | ⏳ 等待 | 新浪期货接口，无代理问题 |
| hk_daily | ⏳ 等待 | 已修复为新浪港股接口 |
| news | ⏳ 等待 | CLS 接口名已修复，CCTV 日期格式已修复 |
| announcement | ⏳ 等待 | 逻辑已重写为按日期拉取 |
| sector | ⏳ 等待 | 已修复为同花顺接口 |

进程 PID 32227 稳定运行，全量跑完预计约 7-9 小时，输出落在 `data/` 目录，格式全部为 CSV。
