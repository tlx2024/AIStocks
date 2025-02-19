import os
import yaml

def load_config():
    config_path = os.path.join(os.path.dirname(__file__), 'config.yml')
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

# 加载配置
_config = load_config()

# API配置
TUSHARE_TOKEN = _config['api']['tushare']['token']
DEEPSEEK_API_KEY = _config['api']['deepseek']['api_key']
DEEPSEEK_API_ENDPOINT = _config['api']['deepseek']['endpoint']

# 数据缓存配置
CACHE_DIR = _config['cache']['directory']
USE_CACHE = _config['cache']['use_cache']

# 策略参数配置
STRATEGY_CONFIG = {
    'min_price': _config['strategy']['min_price'],
    'max_price': _config['strategy']['max_price'],
    'min_turnover': _config['strategy']['min_turnover'],
    'min_market_cap': _config['strategy']['min_market_cap'],
    'max_pe': _config['strategy']['max_pe'],
    'min_return': _config['strategy']['min_return'],
    'min_volume': _config['strategy']['min_volume'],
    'take_profit': 1.1,  # 止盈比例，默认为1.1（10%收益）
    'stop_loss': 0.95    # 止损比例，默认为0.95（5%损失）
}

# 市场分析配置
MARKET_ANALYSIS_CONFIG = {
    'macro_factors': [
        '经济增长',
        '通货膨胀',
        '货币政策',
        '财政政策',
        '就业数据'
    ],
    'policy_factors': [
        '监管政策',
        '产业政策',
        '金融政策',
        '财税政策'
    ],
    'industry_factors': [
        '行业景气度',
        '产业链状况',
        '技术创新',
        '竞争格局'
    ],
    'market_factors': [
        '市场情绪',
        '资金流向',
        '估值水平',
        '技术面分析'
    ],
    'international_factors': [
        '全球经济',
        '地缘政治',
        '国际贸易',
        '大宗商品'
    ]
}

# 幻方策略专用配置
QUANT_CONFIG = {
    'data_requirements': {
        'daily': ['开盘价', '收盘价', '最高价', '最低价', '成交量', '成交额', '换手率'],
        'fundamental': ['市盈率-动态', '归母净利润增长率'],
        'alternative': ['研报覆盖数']
    },
    'backtest_range': ('20200101', '20241231')
}

# 确保变量在模块级别可用
__all__ = ['TUSHARE_TOKEN', 'DEEPSEEK_API_KEY', 'DEEPSEEK_API_ENDPOINT', 'CACHE_DIR', 'USE_CACHE', 'STRATEGY_CONFIG', 'MARKET_ANALYSIS_CONFIG', 'QUANT_CONFIG']
