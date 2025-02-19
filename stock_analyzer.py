# stock_analyzer.py
import akshare as ak
import pandas as pd
import talib
import time
from functools import lru_cache

class StockAnalyzer:
    def __init__(self):
        self.historical_days = 180
        self.retry_times = 3  # 添加重试机制
        self.industry_benchmark = {'上证指数': 'sh000001'}  # 行业基准指数

    @lru_cache(maxsize=50)  # 添加缓存
    def get_stock_data(self, symbol):
        """增强版数据获取，支持重试和备用接口"""
        attempts = 0
        while attempts < self.retry_times:
            try:
                # 使用更稳定的历史数据接口
                hist_data = ak.stock_zh_a_daily(symbol=symbol, adjust="hfq").tail(self.historical_days)
                
                # 实时数据（备用接口）
                try:
                    spot_data = ak.stock_zh_a_spot_em()
                    spot = spot_data[spot_data['代码'] == symbol].iloc[0].to_dict()
                except:
                    spot = ak.stock_zh_a_spot(symbol=symbol).iloc[0].to_dict()
                
                # 财务数据（添加多个数据源）
                finance_data = self._get_financial_data(symbol)
                
                return {
                    'symbol': symbol,
                    'spot': spot,
                    'historical': hist_data,
                    'financial': finance_data,
                    'last_update': pd.Timestamp.now()
                }
            except Exception as e:
                print(f"数据获取失败（尝试 {attempts+1}）: {e}")
                time.sleep(1)
                attempts += 1
        return None

    def _get_financial_data(self, symbol):
        """获取财务数据（多数据源备份）"""
        try:
            # 主要数据源
            finance = ak.stock_financial_analysis_indicator(symbol)
            if not finance.empty:
                return finance.iloc[-1].to_dict()
            
            # 备用数据源
            return ak.stock_financial_report_sina(stock=symbol).iloc[-1].to_dict()
        except:
            return {}

    def analyze_technical(self, hist_data):
        """增强技术分析"""
        df = hist_data.copy()
        # 趋势指标
        df['MA5'] = df['close'].rolling(5).mean()
        df['MA20'] = df['close'].rolling(20).mean()
        df['EMA12'] = talib.EMA(df['close'], timeperiod=12)
        df['EMA26'] = talib.EMA(df['close'], timeperiod=26)
        
        # 动量指标
        df['MACD'], df['MACD_Signal'], _ = talib.MACD(df['close'])
        df['RSI'] = talib.RSI(df['close'])
        df['STOCH_K'], df['STOCH_D'] = talib.STOCH(df['high'], df['low'], df['close'])
        
        # 波动率指标
        df['BB_upper'], df['BB_middle'], df['BB_lower'] = talib.BBANDS(df['close'])
        
        # 成交量分析
        df['OBV'] = talib.OBV(df['close'], df['vol'])
        
        latest = df.iloc[-1]
        return {
            'trend': self._get_trend_status(df),
            'momentum': {
                'macd': latest['MACD'],
                'rsi': latest['RSI'],
                'stochastic': (latest['STOCH_K'], latest['STOCH_D'])
            },
            'volatility': {
                'bollinger_band': (latest['BB_upper'], latest['BB_middle'], latest['BB_lower']),
                'atr': talib.ATR(df['high'], df['low'], df['close']).iloc[-1]
            },
            'volume_analysis': {
                'obv_trend': '上升' if df['OBV'].iloc[-1] > df['OBV'].iloc[-5] else '下降',
                'volume_change': df['vol'].pct_change().iloc[-1]
            }
        }

    def _get_trend_status(self, df):
        """综合判断趋势状态"""
        ma_status = '上涨' if df['MA5'].iloc[-1] > df['MA20'].iloc[-1] else '下跌'
        ema_crossover = '金叉' if df['EMA12'].iloc[-1] > df['EMA26'].iloc[-1] else '死叉'
        return f"{ma_status}趋势（{ema_crossover}）"

    def analyze_fundamental(self, finance_data):
        """增强基本面分析"""
        analysis = {
            'valuation': {
                'pe_ratio': finance_data.get('市盈率', 0),
                'pb_ratio': finance_data.get('市净率', 0),
                'ps_ratio': finance_data.get('市销率', 0)
            },
            'profitability': {
                'roe': finance_data.get('净资产收益率', 0),
                'gross_margin': finance_data.get('销售毛利率', 0)
            },
            'growth': {
                'revenue_growth': finance_data.get('营业收入同比增长率', 0),
                'net_profit_growth': finance_data.get('净利润同比增长率', 0)
            }
        }
        return analysis

    def generate_advice(self, stock_data, market_trend):
        """生成量化建议"""
        score = 0
        factors = []
        
        # 技术面评分（0-40分）
        tech_score, tech_factors = self._evaluate_technical(stock_data['historical'])
        score += tech_score
        factors.extend(tech_factors)
        
        # 基本面评分（0-30分）
        fund_score, fund_factors = self._evaluate_fundamental(stock_data['financial'])
        score += fund_score
        factors.extend(fund_factors)
        
        # 市场环境评分（0-30分）
        market_score, market_factors = self._evaluate_market(market_trend)
        score += market_score
        factors.extend(market_factors)
        
        return {
            'score': score,
            'factors': factors,
            'recommendation': self._get_recommendation(score),
            'risk_warning': self._get_risk_warning(stock_data)
        }

    def _evaluate_technical(self, hist_data):
        """技术面量化评分"""
        score = 0
        factors = []
        
        # 趋势评分（0-15分）
        if self._get_trend_status(hist_data).startswith('上涨'):
            score += 10
            factors.append('处于上升趋势')
            if '金叉' in self._get_trend_status(hist_data):
                score += 5
                factors.append('EMA金叉形成')
        
        # 动量评分（0-15分）
        rsi = hist_data['RSI'].iloc[-1]
        if 30 < rsi < 70:
            score += 5
            factors.append('RSI处于合理区间')
        elif rsi > 70:
            score -= 5
            factors.append('RSI超买')
        
        # 波动率评分（0-10分）
        if hist_data['close'].iloc[-1] > hist_data['BB_upper'].iloc[-1]:
            score -= 3
            factors.append('突破布林带上轨')
        elif hist_data['close'].iloc[-1] < hist_data['BB_lower'].iloc[-1]:
            score += 5
            factors.append('触及布林带下轨')
        
        return min(max(score, 0), 40), factors

    def _get_recommendation(self, score):
        """根据总分生成建议"""
        if score >= 70:
            return '强烈推荐（逢低布局）'
        elif score >= 50:
            return '谨慎推荐（关注支撑位）'
        elif score >= 30:
            return '中性（观望为宜）'
        else:
            return '减持（注意风险）'

    def _get_risk_warning(self, stock_data):
        """风险提示"""
        warnings = []
        if stock_data['historical']['close'].iloc[-1] < stock_data['historical']['MA20'].iloc[-1]:
            warnings.append('股价处于年线下方')
        if stock_data['financial'].get('资产负债率', 0) > 60:
            warnings.append('资产负债率偏高')
        return warnings if warnings else ['暂无显著风险']