import pandas as pd
import numpy as np
from datetime import datetime
import akshare as ak
import talib

class MarketTrendAnalyzer:
    """市场趋势分析器"""
    
    def __init__(self):
        self.index_symbols = {
            '上证指数': 'sh000001',
            '深证成指': 'sz399001',
            '创业板指': 'sz399006'
            # 暂时移除北证50，因为数据获取不稳定
        }
        
    def get_market_indicators(self):
        """获取市场综合指标"""
        try:
            # 1. 指数动态分析
            indices_analysis = self._analyze_indices()
            
            # 2. 资金流向分析
            fund_flow = self._analyze_fund_flow()
            
            # 3. 市场情绪指标
            sentiment = self._analyze_market_sentiment()
            
            # 4. 确定市场阶段
            market_stage = self._determine_market_stage(indices_analysis, fund_flow, sentiment)
            
            return {
                'indices_analysis': indices_analysis,
                'fund_flow': fund_flow,
                'market_sentiment': sentiment,
                'market_stage': market_stage
            }
        except Exception as e:
            print(f"获取市场指标失败: {e}")
            return {
                'indices_analysis': {},
                'fund_flow': {},
                'market_sentiment': {},
                'market_stage': {'stage': '未知', 'score': 50, 'suggestion': '建议观望'}
            }
    
    def _analyze_indices(self):
        """分析主要指数走势"""
        indices_data = {}
        
        for name, symbol in self.index_symbols.items():
            try:
                # 使用新的指数行情接口
                df = ak.stock_zh_index_daily_em(symbol=symbol)
                if df.empty:
                    continue
                    
                # 确保列名统一
                df.columns = [col.lower() for col in df.columns]
                
                # 计算技术指标
                df['ma5'] = df['close'].rolling(5).mean()
                df['ma10'] = df['close'].rolling(10).mean()
                df['ma20'] = df['close'].rolling(20).mean()
                
                # 计算MACD
                df['macd'], df['signal'], df['hist'] = talib.MACD(df['close'])
                
                # 计算RSI
                df['rsi'] = talib.RSI(df['close'])
                
                # 识别支撑压力位
                recent_data = df.tail(20)
                support = recent_data['low'].min()
                resistance = recent_data['high'].max()
                
                indices_data[name] = {
                    'current_price': float(df['close'].iloc[-1]),
                    'change_pct': float((df['close'].iloc[-1] - df['close'].iloc[-2]) / df['close'].iloc[-2] * 100),
                    'ma_system': {
                        'ma5': float(df['ma5'].iloc[-1]),
                        'ma10': float(df['ma10'].iloc[-1]),
                        'ma20': float(df['ma20'].iloc[-1])
                    },
                    'technical': {
                        'macd': float(df['macd'].iloc[-1]),
                        'rsi': float(df['rsi'].iloc[-1])
                    },
                    'support_resistance': {
                        'support': float(support),
                        'resistance': float(resistance)
                    }
                }
            except Exception as e:
                print(f"获取{name}数据失败: {e}")
                
        return indices_data
    
    def _analyze_fund_flow(self):
        """分析资金流向"""
        try:
            # 北向资金（使用备用接口）
            try:
                north_flow = ak.stock_hsgt_hist_em()
                if '当日资金流入' in north_flow.columns:
                    net_flow = float(north_flow['当日资金流入'].iloc[-1])
                elif '当日净流入' in north_flow.columns:
                    net_flow = float(north_flow['当日净流入'].iloc[-1])
                elif '净买额' in north_flow.columns:
                    net_flow = float(north_flow['净买额'].iloc[-1])
                else:
                    net_flow = 0
                    
                north_flow_today = {
                    'today_net': net_flow,
                    'trend': self._calculate_flow_trend(pd.Series([net_flow]))
                }
            except Exception as e:
                print(f"获取北向资金数据失败: {e}")
                north_flow_today = {'today_net': 0, 'trend': 'unknown'}
            
            # 主力资金（使用大单成交数据）
            try:
                stock_flow = ak.stock_fund_flow_individual()  # 使用个股资金流数据汇总
                if not stock_flow.empty:
                    main_net = stock_flow['主力净流入'].sum() if '主力净流入' in stock_flow.columns else 0
                    main_force = {
                        'today_net': float(main_net),
                        'trend': 'inflow' if main_net > 0 else 'outflow'
                    }
                else:
                    main_force = {'today_net': 0, 'trend': 'unknown'}
            except Exception as e:
                print(f"获取主力资金数据失败: {e}")
                main_force = {'today_net': 0, 'trend': 'unknown'}
            
            # 两融余额（使用深市两融数据）
            try:
                margin_data = ak.stock_margin_underlying_info_szse()  # 使用深市两融数据
                if not margin_data.empty:
                    total_margin = margin_data['融资余额'].sum() if '融资余额' in margin_data.columns else 0
                    margin = {
                        'total': float(total_margin),
                        'change': 0  # 暂时不计算变化率
                    }
                else:
                    margin = {'total': 0, 'change': 0}
            except Exception as e:
                print(f"获取两融数据失败: {e}")
                margin = {'total': 0, 'change': 0}
            
            return {
                'north_fund': north_flow_today,
                'main_force': main_force,
                'margin': margin
            }
        except Exception as e:
            print(f"获取资金流向数据失败: {e}")
            return {
                'north_fund': {'today_net': 0, 'trend': 'unknown'},
                'main_force': {'today_net': 0, 'trend': 'unknown'},
                'margin': {'total': 0, 'change': 0}
            }
    
    def _analyze_market_sentiment(self):
        """分析市场情绪"""
        try:
            # 获取涨跌停数据（使用备用接口）
            stock_data = ak.stock_zh_a_spot_em()  # 获取A股实时行情
            
            # 计算涨跌停数量
            up_limit = len(stock_data[stock_data['涨跌幅'] >= 9.9])
            down_limit = len(stock_data[stock_data['涨跌幅'] <= -9.9])
            
            # 计算涨跌停比例
            up_down_ratio = up_limit / max(down_limit, 1)
            
            # 计算简单情绪指标
            sentiment_score = self._calculate_sentiment_score(up_down_ratio)
            
            return {
                'up_down_ratio': up_down_ratio,
                'sentiment_score': sentiment_score,
                'sentiment_level': self._get_sentiment_level(sentiment_score)
            }
        except Exception as e:
            print(f"获取市场情绪数据失败: {e}")
            return {
                'up_down_ratio': 1.0,
                'sentiment_score': 50,
                'sentiment_level': '中性'
            }
    
    def _calculate_flow_trend(self, series):
        """计算资金流向趋势"""
        if isinstance(series, pd.Series) and len(series) >= 5:
            recent_sum = series.tail(5).sum()
            return 'inflow' if recent_sum > 0 else 'outflow'
        return 'unknown'
    
    def _calculate_sentiment_score(self, up_down_ratio):
        """计算情绪得分"""
        # 基于涨跌停比例计算情绪得分（0-100）
        base_score = 50
        if up_down_ratio > 1:
            sentiment_score = min(base_score + (up_down_ratio - 1) * 25, 100)
        else:
            sentiment_score = max(base_score - (1 - up_down_ratio) * 25, 0)
        return sentiment_score
    
    def _get_sentiment_level(self, score):
        """获取情绪水平描述"""
        if score >= 80:
            return '极度贪婪'
        elif score >= 60:
            return '偏向贪婪'
        elif score >= 40:
            return '中性'
        elif score >= 20:
            return '偏向恐慌'
        else:
            return '极度恐慌'
    
    def _evaluate_technical_factors(self, indices_analysis):
        """评估技术面因素"""
        score = 50  # 基础分
        
        # 以上证指数为主要参考
        main_index = indices_analysis.get('上证指数', {})
        if main_index:
            # MACD
            if main_index['technical']['macd'] > 0:
                score += 10
            
            # RSI
            rsi = main_index['technical']['rsi']
            if 40 <= rsi <= 60:
                score += 5
            elif rsi > 70:
                score -= 5
            elif rsi < 30:
                score -= 5
            
            # 均线系统
            ma_system = main_index['ma_system']
            if ma_system['ma5'] > ma_system['ma10'] > ma_system['ma20']:
                score += 15
            elif ma_system['ma5'] < ma_system['ma10'] < ma_system['ma20']:
                score -= 15
        
        return min(max(score, 0), 100)
    
    def _evaluate_fund_factors(self, fund_flow):
        """评估资金面因素"""
        score = 50  # 基础分
        
        # 北向资金
        north_fund = fund_flow.get('north_fund', {})
        if north_fund['trend'] == 'inflow':
            score += 15
        elif north_fund['trend'] == 'outflow':
            score -= 15
        
        # 主力资金
        main_force = fund_flow.get('main_force', {})
        if main_force['trend'] == 'inflow':
            score += 15
        elif main_force['trend'] == 'outflow':
            score -= 15
        
        # 两融余额
        margin = fund_flow.get('margin', {})
        if margin.get('change', 0) > 0:
            score += 10
        elif margin.get('change', 0) < 0:
            score -= 10
        
        return min(max(score, 0), 100)
        
    def _determine_market_stage(self, indices_analysis, fund_flow, sentiment):
        """判断市场所处阶段"""
        try:
            # 技术面评分
            tech_score = self._evaluate_technical_factors(indices_analysis)
            
            # 资金面评分
            fund_score = self._evaluate_fund_factors(fund_flow)
            
            # 情绪面评分
            sentiment_score = sentiment.get('sentiment_score', 50)
            
            # 综合评分
            total_score = tech_score * 0.4 + fund_score * 0.4 + sentiment_score * 0.2
            
            # 判断市场阶段
            if total_score >= 70:
                return {'stage': '上升', 'score': total_score, 'suggestion': '优先选择高弹性科技股'}
            elif total_score <= 30:
                return {'stage': '下跌', 'score': total_score, 'suggestion': '侧重防御性板块'}
            else:
                return {'stage': '震荡', 'score': total_score, 'suggestion': '均衡配置'}
        except Exception as e:
            print(f"市场阶段判断失败: {e}")
            return {'stage': '未知', 'score': 50, 'suggestion': '建议观望'}
