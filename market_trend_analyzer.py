import pandas as pd
import numpy as np
from datetime import datetime, timedelta
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

    def get_selected_stocks(self, market_analysis):
        """获取推荐股票列表"""
        try:
            # 获取行业板块资金流向
            industry_funds = ak.stock_sector_fund_flow_rank()
            if industry_funds is not None and not industry_funds.empty:
                # 确保列名存在
                required_columns = ['名称', '今日涨跌幅', '今日主力净流入-净额']
                if not all(col in industry_funds.columns for col in required_columns):
                    print(f"行业数据缺少必要列，实际列名: {industry_funds.columns.tolist()}")
                    return []
                
                # 重命名列
                industry_funds = industry_funds.rename(columns={'名称': '行业'})
                
                # 获取资金流入最多的前3个行业
                industry_funds['今日涨跌幅'] = industry_funds['今日涨跌幅'].astype(float)
                industry_funds['今日主力净流入-净额'] = industry_funds['今日主力净流入-净额'].astype(float)
                
                # 按主力资金净流入排序
                top_industries = industry_funds.sort_values('今日主力净流入-净额', ascending=False).head(3)
                
                selected_stocks = []
                for _, industry in top_industries.iterrows():
                    try:
                        # 获取行业成分股
                        stocks = self._get_industry_stocks(industry['行业'])
                        if stocks:
                            # 分析每只股票
                            for stock in stocks[:10]:  # 每个行业取前10只股票分析
                                try:
                                    analysis = self._analyze_stock(stock)
                                    if self._is_stock_qualified(analysis):
                                        selected_stocks.append({
                                            'code': stock,
                                            'name': self._get_stock_name(stock),
                                            'industry': industry['行业'],
                                            'reason': self._generate_selection_reason(analysis)
                                        })
                                except Exception as e:
                                    print(f"分析股票 {stock} 失败: {str(e)}")
                                    continue
                                
                                if len(selected_stocks) >= 5:  # 最多选5只股票
                                    break
                    except Exception as e:
                        print(f"处理行业 {industry['行业']} 失败: {str(e)}")
                        continue
                        
                return selected_stocks[:5]  # 返回前5只股票
                
            return []
            
        except Exception as e:
            print(f"选股过程出错: {str(e)}")
            return []
            
    def _get_industry_stocks(self, industry_name):
        """获取行业成分股"""
        try:
            # 获取行业成分股
            stocks = ak.stock_sector_detail(industry_name)
            if stocks is not None and not stocks.empty:
                return stocks['股票代码'].tolist()
            return []
        except:
            return []
            
    def _analyze_stock(self, stock_code):
        """分析单只股票"""
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=60)).strftime('%Y%m%d')
        
        # 获取股票数据
        df = ak.stock_zh_a_hist(symbol=stock_code, period="daily",
                              start_date=start_date, end_date=end_date,
                              adjust="qfq")
        
        if df.empty or len(df) < 20:
            raise ValueError("数据不足")
            
        # 重命名列
        df = df.rename(columns={
            '日期': 'date',
            '开盘': 'open',
            '收盘': 'close',
            '最高': 'high',
            '最低': 'low',
            '成交量': 'volume'
        })
        
        # 计算技术指标
        df['MA5'] = df['close'].rolling(window=5).mean()
        df['MA10'] = df['close'].rolling(window=10).mean()
        df['MA20'] = df['close'].rolling(window=20).mean()
        
        # 计算MACD
        exp1 = df['close'].ewm(span=12, adjust=False).mean()
        exp2 = df['close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = exp1 - exp2
        df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        
        # 计算RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        return df.iloc[-1]
        
    def _is_stock_qualified(self, analysis):
        """判断股票是否符合选股条件"""
        # 价格趋势
        price_trend = analysis['close'] > analysis['MA5'] > analysis['MA10'] > analysis['MA20']
        
        # MACD金叉
        macd_cross = analysis['MACD'] > analysis['Signal']
        
        # RSI不过高
        rsi_good = 30 < analysis['RSI'] < 70
        
        return price_trend and macd_cross and rsi_good
        
    def _generate_selection_reason(self, analysis):
        """生成选股理由"""
        reasons = []
        
        # 趋势分析
        if analysis['close'] > analysis['MA5'] > analysis['MA10'] > analysis['MA20']:
            reasons.append("多头排列，趋势向上")
        
        # MACD分析
        if analysis['MACD'] > analysis['Signal']:
            reasons.append("MACD金叉形成")
        
        # RSI分析
        if 30 < analysis['RSI'] < 70:
            reasons.append("RSI处于良好区间")
        
        return "，".join(reasons)
        
    def _get_stock_name(self, stock_code):
        """获取股票名称"""
        try:
            stock_info = ak.stock_individual_info_em(symbol=stock_code)
            if stock_info is not None and not stock_info.empty:
                return stock_info.iloc[0]['value']
            return stock_code
        except:
            return stock_code

    def get_start_date(self):
        """获取开始日期（30天前）"""
        return (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')
        
    def get_end_date(self):
        """获取结束日期（今天）"""
        return datetime.now().strftime('%Y%m%d')


# market_analysis.py 新增方法
class MarketAnalyzer:
    def analyze_individual_stock(self, symbol):
        """增强版个股分析"""
        try:
            stock_data = self.stock_analyzer.get_stock_data(symbol)
            if not stock_data:
                return {"error": "无法获取股票数据"}
                
            market_data = self.fetch_market_data()
            if not market_data:
                return {"error": "无法获取市场数据"}
                
            market_analysis = self.analyze_market_data(market_data)
            
            # 添加行业对比分析
            industry_analysis = self._compare_with_industry(symbol, stock_data)
            
            return {
                'basic_info': {
                    'name': stock_data['spot'].get('名称'),
                    'price': stock_data['spot'].get('最新价'),
                    'change': stock_data['spot'].get('涨跌幅')
                },
                'technical': self.stock_analyzer.analyze_technical(stock_data['historical']),
                'fundamental': self.stock_analyzer.analyze_fundamental(stock_data['financial']),
                'market_context': {
                    'trend_stage': market_analysis.get('market_stage', {}),
                    'industry_comparison': industry_analysis
                },
                'advice': self.stock_analyzer.generate_advice(stock_data, market_analysis)
            }
        except Exception as e:
            print(f"个股分析失败: {e}")
            return {"error": "分析过程出现异常"}

    def _compare_with_industry(self, symbol, stock_data):
        """行业对比分析"""
        try:
            # 获取行业指数数据
            industry_index = ak.stock_board_industry_index_ths()
            # 获取个股所属行业（示例逻辑）
            industry = industry_index[industry_index['股票代码'] == symbol]['行业'].iloc[0]
            
            # 获取行业指数行情
            index_data = ak.stock_zh_index_daily_em(symbol=self.stock_analyzer.industry_benchmark[industry])
            
            # 计算相对强弱
            stock_return = stock_data['historical']['close'].pct_change(periods=20).iloc[-1]
            index_return = index_data['close'].pct_change(periods=20).iloc[-1]
            
            return {
                'industry': industry,
                'relative_strength': stock_return - index_return,
                'industry_rank': '前10%'  # 示例数据
            }
        except:
            return {"error": "行业分析失败"}