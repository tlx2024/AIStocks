# 智能股票交易系统

## 项目结构
```
stock_trading/
├── data_cache/               # 数据缓存目录
├── config.yml                # 配置文件（API密钥/策略参数）
├── requirements.txt          # Python依赖列表
├── changelog.md              # 更新日志
│
├── core/
│   ├── monitor.py            # 策略监控主程序
│   ├── data_fetcher.py       # 多源数据获取模块
│   ├── strategy.py           # 量化策略实现
│   ├── report_generator.py   # 报告生成模块
│   └── config.py             # 配置加载模块
│
└── utils/
    ├── analyzer.py           # 数据分析工具
    └── visualizer.py         # 数据可视化工具

## 核心模块说明

### 📊 data_fetcher.py
- 集成Tushare/AKShare/Baostock等多数据源
- 实现自动缓存机制（日级/分钟级数据）
- 支持股票基础数据、财务数据、行情数据获取

### 🤖 strategy.py
- 实现增强型量化策略（EnhancedQuantStrategy）
- 包含技术指标计算模块：
  - MACD动量分析
  - 布林带波动率计算
  - RSI超买超卖检测
- 动态信号生成系统

### 👁️ monitor.py
- 基于APScheduler的定时任务系统
- 实时监控模块功能：
  - 自动数据更新
  - 策略信号生成
  - 异常预警系统
  - 结果持久化存储

### 📈 report_generator.py
- 自动生成可视化报告（Excel/HTML格式）
- 包含收益曲线、持仓分析、风险指标等模块

## 快速开始
```bash
# 安装依赖
pip install -r requirements.txt

# 配置API密钥（编辑config.yml）
cp config.example.yml config.yml

# 启动监控系统
python monitor.py

# 启动策略系统
python main.py  --strategy enhanced
```

## 配置说明
编辑 `config.yml` 设置：
- API密钥（Tushare/DeepSeek）
- 缓存策略（启用/禁用）
- 交易参数（持仓周期/止盈止损）
- 风险控制参数

## 许可证
MIT License

## 中长期投资优化建议

### 基本面增强模块
1. **财务健康度分析**  
   - 整合ROE/毛利率/现金流等财务指标
   - 构建杜邦分析体系
   - 财务造假预警系统（Benford定律应用）

2. **估值模型集成**  
   - DCF现金流折现模型
   - 相对估值矩阵（PE/PB/PS横向对比）
   - 行业特定估值框架

### 风险管理体系
```python
# 示例：动态止损策略
def dynamic_stoploss(portfolio):
    volatility = calculate_30d_volatility()
    base_stop = 0.85  # 基准止损线
    dynamic_adjust = volatility * 2  # 波动率调整因子
    return max(base_stop, 1 - dynamic_adjust)
```
- 波动率自适应仓位控制
- 黑天鹅事件压力测试
- 跨资产相关性监控

### 智能配置建议
1. **行业生命周期适配**  
   - 初创期→成长型策略
   - 成熟期→红利再投资策略
   - 衰退期→做空对冲策略

2. **经济周期引擎**  
   - 美林时钟量化版
   - 宏观指标领先系统（PMI/CPI/M2）
   - 政策文本分析（NLP处理央行报告）

### 技术演进路线
| 阶段 | 功能开发 | 技术目标 |
|------|----------|----------|
| 1.0  | 基础量化框架 | 策略回测年化收益>15% |
| 2.0  | AI增强模块 | 预测准确率>65% |
| 3.0  | 智能风控系统 | 最大回撤<20% |
