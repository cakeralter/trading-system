# Trading System 交易系统技能

这是一个面向股票、ETF 等公开市场的低频波段交易规则执行仓库。它的目标不是预测收益，也不是给出买卖建议，而是把候选标的评分、仓位计算、风险检查和交易复盘统一到一套可重复执行的规则里。

## 能力范围

- 候选标的评分：按 100 分模型评估市场环境、趋势结构、买点质量、盈亏比、成交量、流动性、板块强度和组合适配度。
- 单笔交易检查：核对入场价、止损价、第一目标价、R 倍数、市场状态和组合风险。
- 仓位计算：根据账户总资产、单笔最大账户风险和止损幅度计算建议买入金额。
- 持仓复盘：检查当前 R 倍数、止损状态、止盈状态和组合风险影响。
- 交易回放：计算实际 R 结果，区分系统内正常亏损和执行错误。
- 周/月复盘：统计胜率、平均盈利 R、平均亏损 R、期望值、执行率、回撤和熔断状态。

## 重要边界

- 本仓库只提供交易系统规则执行，不构成任何投资建议。
- 评分是规则匹配度，不是上涨概率或收益预测。
- 不会凭空编造实时行情数据；缺少价格、成交量、均线、账户或持仓数据时，应明确补充数据或标注假设。
- 硬性过滤条件优先于评分结果。触发硬过滤时，即使总分较高，也不能按普通候选标的处理。

## 目录结构

```text
.
├── SKILL.md                         # Codex 技能入口与执行流程
├── agents/
│   └── openai.yaml                  # OpenAI 侧技能展示与默认提示配置
├── references/
│   ├── trading-system-manual.md     # 中文交易系统完整手册
│   ├── scoring-model.md             # 100 分评分模型与硬过滤规则
│   ├── risk-rules.md                # 仓位、止损、组合风险和熔断规则
│   └── templates.md                 # 评分、计划、持仓复盘、交易回放模板
└── scripts/
    └── score_candidates.py          # 批量 CSV 候选标的评分脚本
```

## 快速开始

批量评分脚本只依赖 Python 标准库，可直接运行：

```bash
python3 scripts/score_candidates.py candidates.csv
```

输出到 CSV 文件：

```bash
python3 scripts/score_candidates.py candidates.csv -o scored.csv
```

输出 JSON：

```bash
python3 scripts/score_candidates.py candidates.csv --json
```

带账户规模和单笔风险计算建议仓位：

```bash
python3 scripts/score_candidates.py candidates.csv --account 100000 --risk 1 -o scored.csv
```

`--risk` 可以传小数或百分数。`0.01` 和 `1` 都表示 1% 单笔账户风险。

## CSV 字段

推荐输入字段：

```text
symbol,name,price,entry,stop_loss,target1,ma20,ma60,volume,avg_volume_20,
support,resistance,market_score,trend_score,buy_point_score,volume_score,
liquidity_score,sector_score,portfolio_score,sector,current_sector_exposure
```

常用字段说明：

| 字段 | 说明 |
|---|---|
| `symbol` / `name` | 标的代码和名称 |
| `price` / `entry` | 当前价格或计划买入价；`entry` 优先用于风险计算 |
| `stop_loss` | 止损价 |
| `target1` | 第一目标价 |
| `ma20` / `ma60` | 20 日、60 日均线，用于趋势结构推导 |
| `volume` / `avg_volume_20` | 当前成交量与 20 日均量，用于成交量评分 |
| `support` / `resistance` | 支撑位和压力位 |
| `market_score` | 市场评分，0-10 |
| `trend_score` | 趋势分，可直接给分，也可由均线和支撑位推导 |
| `buy_point_score` | 买点质量分 |
| `volume_score` | 成交量分 |
| `liquidity_score` | 流动性分 |
| `sector_score` | 板块或主题强度分 |
| `portfolio_score` | 与当前组合的适配度 |
| `current_sector_exposure` | 当前同板块仓位占比，用于集中度过滤 |

如果直接提供组件分数，脚本会优先使用输入分数；否则会根据价格、均线、成交量、买点类型等字段做保守推导。

## 评分模型

总分为 100 分：

| 维度 | 分值 |
|---|---:|
| 市场环境 | 20 |
| 趋势结构 | 20 |
| 买点质量 | 20 |
| 风险收益比 | 15 |
| 成交量行为 | 10 |
| 流动性 | 5 |
| 板块/主题强度 | 5 |
| 组合适配度 | 5 |

分数等级：

| 分数 | 结论 |
|---:|---|
| 85-100 | high-quality candidate |
| 70-84 | watchlist candidate |
| 60-69 | wait for confirmation |
| 低于 60 | eliminated or low priority |

## 硬性过滤

以下情况会触发硬过滤或限制激进操作：

- 没有有效止损位。
- 第一目标价低于 2R。
- 流动性过低。
- 趋势明显破坏。
- 市场评分低于 4，却仍计划正常或激进仓位。
- 同板块或同逻辑暴露超过系统集中度限制。
- 已触发连续亏损、回撤超限、止损执行失效等熔断条件。

## 仓位计算

核心公式：

```text
stop_loss_pct = abs(entry - stop_loss) / entry
initial_1R = abs(entry - stop_loss)
target_r = abs(first_target - entry) / initial_1R
buy_amount = account_equity * max_account_risk_per_trade / stop_loss_pct
worst_case_loss = buy_amount * stop_loss_pct
position_pct = buy_amount / account_equity
```

如果止损幅度为 0 或无法计算，交易无效。计算出的仓位还需要再套用单票仓位、同方向仓位、组合理论亏损和熔断规则。

## 输出字段

批量评分脚本会输出：

- `total_score`：总分
- `grade`：系统结论
- `hard_filters`：触发的硬过滤
- 各维度分数：`market_points`、`trend_points`、`buy_point_points`、`risk_reward_points` 等
- `initial_1r`：初始 1R
- `target_r`：第一目标价对应 R 倍数
- `suggested_buy_amount`：建议买入金额，仅在提供 `--account` 和 `--risk` 时计算
- `position_pct`：建议仓位占账户比例
- `worst_case_loss`：最坏情况下亏损金额

## 参考文档

- `references/trading-system-manual.md`：完整中文交易系统手册。
- `references/scoring-model.md`：评分模型、等级、硬过滤和 CSV 字段。
- `references/risk-rules.md`：仓位、止损、组合限制和熔断规则。
- `references/templates.md`：候选评分、交易计划、持仓复盘和周期复盘模板。

## 免责声明

本项目用于交易流程建设、规则执行和复盘辅助，不提供任何保证收益的信号，也不替代独立判断、投资顾问意见或风险承受能力评估。任何规则都应先经过历史样本验证和小仓试运行，再进入正式资金执行。
