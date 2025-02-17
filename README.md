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
python -m core.monitor
```

## 配置说明
编辑 `config.yml` 设置：
- API密钥（Tushare/DeepSeek）
- 缓存策略（启用/禁用）
- 交易参数（持仓周期/止盈止损）
- 风险控制参数

## 许可证
MIT License
