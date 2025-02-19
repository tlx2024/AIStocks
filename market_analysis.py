import os
import json
import requests
from datetime import datetime, timedelta
import akshare as ak
import pandas as pd
from config import DEEPSEEK_API_KEY, MARKET_ANALYSIS_CONFIG, DEEPSEEK_API_ENDPOINT

class StockAnalyzer:
    def __init__(self):
        self.api = ak

    def get_stock_data(self, symbol):
        """获取股票数据"""
        try:
            # 自动补全股票代码后缀
            if not symbol.endswith(('.SH', '.SZ')):
                symbol += '.SH' if symbol.startswith(('6', '9')) else '.SZ'
            
            # 获取股票基本信息
            stock_info = self.api.stock_individual_info_em(symbol=symbol)
            
            # 获取日K线数据
            daily_data = self.api.stock_zh_a_hist(symbol=symbol, period="daily", 
                                                adjust="qfq").tail(30)
            
            # 获取实时行情
            realtime_data = self.api.stock_zh_a_spot_em().query(f"代码 == '{symbol}'")
            
            # 获取主力资金流向
            capital_flow = self.api.stock_individual_fund_flow(symbol)
            
            return {
                "info": stock_info,
                "daily_data": daily_data,
                "realtime": realtime_data,
                "capital_flow": capital_flow
            }
        except Exception as e:
            raise Exception(f"获取股票数据失败: {str(e)}")

    def analyze_technical_indicators(self, daily_data):
        """分析技术指标"""
        try:
            # 计算MA5, MA10, MA20
            daily_data['MA5'] = daily_data['收盘'].rolling(window=5).mean()
            daily_data['MA10'] = daily_data['收盘'].rolling(window=10).mean()
            daily_data['MA20'] = daily_data['收盘'].rolling(window=20).mean()
            
            # 计算MACD
            exp1 = daily_data['收盘'].ewm(span=12, adjust=False).mean()
            exp2 = daily_data['收盘'].ewm(span=26, adjust=False).mean()
            macd = exp1 - exp2
            signal = macd.ewm(span=9, adjust=False).mean()
            
            # 获取最新数据
            latest = daily_data.iloc[-1]
            prev = daily_data.iloc[-2]
            
            analysis = []
            
            # 分析均线
            if latest['收盘'] > latest['MA5'] > latest['MA10']:
                analysis.append("短期均线呈现上升趋势")
            elif latest['收盘'] < latest['MA5'] < latest['MA10']:
                analysis.append("短期均线呈现下降趋势")
                
            # 分析MACD
            if macd.iloc[-1] > signal.iloc[-1] and macd.iloc[-2] <= signal.iloc[-2]:
                analysis.append("MACD金叉，可能存在上涨机会")
            elif macd.iloc[-1] < signal.iloc[-1] and macd.iloc[-2] >= signal.iloc[-2]:
                analysis.append("MACD死叉，注意下跌风险")
                
            # 分析成交量
            vol_ma5 = daily_data['成交量'].rolling(window=5).mean()
            if latest['成交量'] > vol_ma5.iloc[-1] * 1.5:
                analysis.append("成交量显著放大，需密切关注")
                
            return analysis
            
        except Exception as e:
            raise Exception(f"技术分析失败: {str(e)}")

    def generate_advice(self, stock_data, market_analysis):
        """生成投资建议"""
        try:
            # 获取股票基本信息
            stock_info = stock_data['info']
            
            # 获取最新行情
            realtime = stock_data['realtime'].iloc[0]
            
            # 获取主力资金流向
            flow = stock_data['capital_flow'].iloc[0]
            
            # 获取技术分析结果
            technical_analysis = self.analyze_technical_indicators(stock_data['daily_data'])
            
            # 整合分析结果
            result = []
            
            # 添加基本信息
            result.append(f"股票名称: {stock_info.iloc[0]['value']}")
            result.append(f"所属行业: {stock_info.iloc[3]['value']}")
            result.append(f"主营业务: {stock_info.iloc[7]['value']}")
            
            # 添加最新行情
            result.append(f"\n最新价格: {realtime['最新价']} ({realtime['涨跌幅']}%)")
            result.append(f"成交额: {realtime['成交额']/100000000:.2f}亿")
            
            # 添加资金流向
            result.append(f"\n主力净流入: {flow['主力净流入']/100000000:.2f}亿")
            result.append(f"主力净占比: {flow['主力净占比']}%")
            
            # 添加技术分析结果
            result.append("\n技术分析:")
            for analysis in technical_analysis:
                result.append(f"- {analysis}")
            
            # 添加市场分析结果
            result.append("\n市场分析:")
            for key, value in market_analysis.items():
                result.append(f"- {key}: {value}")
            
            return "\n".join(result)
            
        except Exception as e:
            raise Exception(f"生成投资建议失败: {str(e)}")


class MarketAnalyzer:
    def __init__(self):
        self.api_key = DEEPSEEK_API_KEY
        self.config = MARKET_ANALYSIS_CONFIG
        self.stock_analyzer = StockAnalyzer()

    def fetch_market_data(self):
        """获取市场数据"""
        try:
            # 获取大盘指数数据
            indices = {
                '上证指数': ak.stock_zh_index_daily_em(symbol="sh000001"),
                '深证成指': ak.stock_zh_index_daily_em(symbol="sz399001"),
                '创业板指': ak.stock_zh_index_daily_em(symbol="sz399006")
            }
            
            # 获取北向资金数据 (使用新的API)
            try:
                north_money = ak.stock_hsgt_north_net_flow_in_em()  # 新的API
            except:
                try:
                    north_money = ak.stock_hsgt_hist_em()  # 备选API
                except:
                    print("无法获取北向资金数据")
                    north_money = pd.DataFrame()
            
            # 获取行业资金流向 (使用新的API)
            try:
                industry_flow = ak.stock_sector_fund_flow_rank()  # 新的API
            except:
                try:
                    industry_flow = ak.stock_sector_detail()  # 备选API
                except:
                    print("无法获取行业资金流向数据")
                    industry_flow = pd.DataFrame()
            
            return {
                'indices': indices,
                'north_money': north_money,
                'industry_flow': industry_flow
            }
        except Exception as e:
            print(f"获取市场数据失败: {e}")
            return None
            
    def analyze_market_data(self, market_data):
        """分析市场数据"""
        if not market_data:
            return None
            
        analysis = {
            'market_trend': self._analyze_market_trend(market_data['indices']),
            'capital_flow': self._analyze_capital_flow(market_data['north_money'], market_data['industry_flow']),
            'sector_performance': self._analyze_sector_performance(market_data['industry_flow'])
        }
        return analysis
        
    def _analyze_market_trend(self, indices):
        """分析市场趋势"""
        trends = {}
        for name, data in indices.items():
            if data is not None and not data.empty:
                try:
                    # 计算20日均线
                    data['MA20'] = data['close'].rolling(20).mean()
                    # 计算当前趋势
                    current_price = data['close'].iloc[-1]
                    ma20 = data['MA20'].iloc[-1]
                    trend = "上升" if current_price > ma20 else "下降"
                    
                    # 计算涨跌幅
                    price_change = (data['close'].iloc[-1] - data['close'].iloc[-2]) / data['close'].iloc[-2] * 100
                    volume_change = (data['volume'].iloc[-1] - data['volume'].iloc[-2]) / data['volume'].iloc[-2] * 100
                    
                    trends[name] = {
                        'trend': trend,
                        'price_change': price_change,
                        'volume_change': volume_change
                    }
                except Exception as e:
                    print(f"处理指数 {name} 数据时出错: {e}")
                    print(f"可用的列: {data.columns.tolist()}")
        return trends
        
    def _analyze_capital_flow(self, north_money, industry_flow):
        """分析资金流向"""
        result = {'north_money_net': 0, 'industry_flow': {}}
        
        # 分析北向资金
        if not north_money.empty:
            try:
                if '净流入' in north_money.columns:
                    result['north_money_net'] = north_money['净流入'].iloc[-1]
                elif '净买额' in north_money.columns:
                    result['north_money_net'] = north_money['净买额'].iloc[-1]
            except:
                print("处理北向资金数据失败")
        
        # 分析行业资金流向
        if not industry_flow.empty:
            try:
                # 尝试不同的可能的列名
                flow_column = None
                for col in ['净流入', '净流入额', '净买入']:
                    if col in industry_flow.columns:
                        flow_column = col
                        break
                
                if flow_column:
                    result['industry_flow'] = industry_flow.sort_values(flow_column, ascending=False).head(5).to_dict('records')
            except:
                print("处理行业资金流向数据失败")
        
        return result
        
    def _analyze_sector_performance(self, industry_flow):
        """分析行业表现"""
        if industry_flow.empty:
            return {}
            
        try:
            # 尝试不同的可能的列名
            flow_column = None
            for col in ['净流入', '净流入额', '净买入']:
                if col in industry_flow.columns:
                    flow_column = col
                    break
            
            if flow_column:
                # 按资金净流入排序
                sorted_sectors = industry_flow.sort_values(flow_column, ascending=False)
                return {
                    'top_sectors': sorted_sectors.head(5).to_dict('records'),
                    'bottom_sectors': sorted_sectors.tail(5).to_dict('records')
                }
        except:
            print("处理行业表现数据失败")
        
        return {}
        
    def analyze_individual_stock(self, symbol):
        """分析单个股票"""
        stock_data = self.stock_analyzer.get_stock_data(symbol)
        if not stock_data:
            return None
            
        market_data = self.fetch_market_data()
        market_analysis = self.analyze_market_data(market_data)
        
        return {
            'stock_analysis': self.stock_analyzer.generate_advice(stock_data, market_analysis),
            'market_context': {
                'trend': market_analysis['market_trend'],
                'stage': market_analysis.get('market_stage', {})
            }
        }
        
    def analyze_stock(self, symbol):
        try:
            # 确保股票代码格式正确
            if not symbol.startswith(('600', '601', '602', '603', '605', '688', '000', '002', '300')):
                raise ValueError("无效的股票代码格式")

            # 添加市场后缀
            if symbol.startswith(('600', '601', '602', '603', '605', '688')):
                full_symbol = f"{symbol}.SH"
            else:
                full_symbol = f"{symbol}.SZ"

            # 获取更长时间范围的历史数据以确保有足够数据计算指标
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=180)).strftime('%Y%m%d')
            
            # 使用akshare获取股票数据
            df = ak.stock_zh_a_hist(symbol=symbol, period="daily", 
                                  start_date=start_date, end_date=end_date, 
                                  adjust="qfq")
            
            if df.empty or len(df) < 30:  # 确保至少有30天的数据
                raise ValueError("获取不到足够的历史数据")

            # 重命名列以匹配计算需求
            df = df.rename(columns={
                '日期': 'date',
                '开盘': 'open',
                '收盘': 'close',
                '最高': 'high',
                '最低': 'low',
                '成交量': 'volume'
            })
            
            # 按日期排序，确保数据顺序正确
            df = df.sort_values('date')
            
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
            
            # 获取最新数据进行分析
            latest = df.iloc[-1]
            prev = df.iloc[-2]
            
            # 生成分析报告
            analysis = {
                'code': symbol,
                'name': self.get_stock_name(symbol),
                'price': latest['close'],
                'change': ((latest['close'] - prev['close']) / prev['close'] * 100),
                'ma5': latest['MA5'],
                'ma10': latest['MA10'],
                'ma20': latest['MA20'],
                'rsi': latest['RSI'],
                'macd': latest['MACD'],
                'macd_signal': latest['Signal'],
                'volume': latest['volume'],
                'date': latest['date']
            }
            
            # 生成趋势分析
            trend = self.analyze_trend(df)
            analysis['trend'] = trend
            
            return analysis
            
        except Exception as e:
            raise Exception(f"股票分析失败: {str(e)}")
            
    def analyze_trend(self, df):
        """分析股票趋势"""
        latest = df.iloc[-1]
        
        # 趋势判断
        trend = []
        
        # MA趋势
        if latest['close'] > latest['MA5'] > latest['MA10'] > latest['MA20']:
            trend.append("强势上涨趋势")
        elif latest['close'] < latest['MA5'] < latest['MA10'] < latest['MA20']:
            trend.append("强势下跌趋势")
        elif latest['close'] > latest['MA20']:
            trend.append("整体偏强")
        elif latest['close'] < latest['MA20']:
            trend.append("整体偏弱")
            
        # MACD趋势
        if latest['MACD'] > latest['Signal']:
            trend.append("MACD金叉形成")
        elif latest['MACD'] < latest['Signal']:
            trend.append("MACD死叉形成")
            
        # RSI分析
        if latest['RSI'] > 70:
            trend.append("RSI超买")
        elif latest['RSI'] < 30:
            trend.append("RSI超卖")
        else:
            trend.append("RSI处于中性区间")
            
        return " | ".join(trend)
        
    def get_stock_name(self, symbol):
        """获取股票名称"""
        try:
            # 使用akshare获取股票基本信息
            if symbol.startswith(('600', '601', '602', '603', '605', '688')):
                market = 'sh'
            else:
                market = 'sz'
                
            stock_info = ak.stock_individual_info_em(symbol=f"{symbol}")
            if stock_info is not None and not stock_info.empty:
                return stock_info.iloc[0]['value']  # 返回股票名称
            return symbol  # 如果获取失败，返回股票代码
            
        except Exception as e:
            return symbol  # 出错时返回股票代码
            
    def generate_market_report(self, selected_stocks, market_analysis):
        print("正在构建API请求...")
        prompt = self._build_analysis_prompt(selected_stocks, market_analysis)
        print(f"请求提示词内容:\n{prompt[:500]}...")  # 打印前500字符
        
        print("正在调用DeepSeek API...")
        response = self._call_deepseek_api(prompt)
        
        if response:
            print("API调用成功，正在解析响应...")
            try:
                return response['choices'][0]['message']['content']
            except KeyError:
                print("响应格式异常，完整响应:")
                print(json.dumps(response, indent=2))
        return None
        
    def _build_analysis_prompt(self, selected_stocks, market_analysis):
        """构建分析提示词"""
        prompt = f"""
请基于以下信息，生成一份详细的市场分析报告：

1. 大盘走势：
{json.dumps(market_analysis['market_trend'], indent=2, ensure_ascii=False)}

2. 资金流向：
{json.dumps(market_analysis['capital_flow'], indent=2, ensure_ascii=False)}

3. 行业表现：
{json.dumps(market_analysis['sector_performance'], indent=2, ensure_ascii=False)}

4. 选股结果：
{selected_stocks.to_json(orient='records', force_ascii=False)}

请从以下几个方面进行分析：
1. 大盘走势分析和未来趋势判断
2. 行业机会分析
3. 个股投资建议
4. 风险提示

要求：
1. 分析要客观、专业
2. 建议要具体、可操作
3. 风险要充分提示
4. 结合当前市场环境
"""
        return prompt
        
    def _call_deepseek_api(self, prompt):
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            payload = {
                "model": "deepseek-chat",
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7
            }
            
            response = requests.post(
                DEEPSEEK_API_ENDPOINT,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            # 检查响应状态
            if response.status_code != 200:
                print(f"API请求失败，状态码: {response.status_code}")
                print(f"响应内容: {response.text}")
                return None
                
            # 尝试解析JSON
            try:
                return response.json()
            except json.JSONDecodeError:
                print("API返回无效的JSON格式")
                print(f"原始响应: {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"API请求异常: {e}")
            return None
            
    def _format_report(self, response):
        """格式化分析报告"""
        if not response:
            return "无法生成分析报告"
            
        # 添加报告头
        report = f"""
====================================
     市场分析报告
     生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
====================================

{response}

====================================
     风险提示：
     本报告基于历史数据和AI分析生成，仅供参考。
     投资有风险，入市需谨慎。
====================================
"""
        return report

    def analyze_market(self):
        """分析市场整体状况"""
        try:
            # 获取市场指标
            indicators = self.get_market_indicators()
            if not indicators:
                return None
                
            # 获取市场情绪
            sentiment = self.get_market_sentiment()
            if not sentiment:
                sentiment = {'sentiment': 'neutral', 'score': 50}
                
            # 获取市场阶段
            stage = self.get_market_stage()
            if not stage:
                stage = {'stage': 'unknown', 'score': 50}
                
            return {
                'indicators': indicators,
                'sentiment': sentiment,
                'stage': stage
            }
            
        except Exception as e:
            print(f"市场分析失败: {str(e)}")
            return None
            
    def get_market_indicators(self):
        """获取市场指标"""
        try:
            # 获取上证指数数据
            sh_index = ak.stock_zh_index_daily(symbol="sh000001")
            # 获取深证成指数据
            sz_index = ak.stock_zh_index_daily(symbol="sz399001")
            # 获取创业板指数据
            cyb_index = ak.stock_zh_index_daily(symbol="sz399006")
            
            indices_analysis = {
                '上证指数': self._analyze_index(sh_index),
                '深证成指': self._analyze_index(sz_index),
                '创业板指': self._analyze_index(cyb_index)
            }
            
            # 获取资金流向数据
            fund_flow = self._get_fund_flow()
            
            return {
                'indices_analysis': indices_analysis,
                'fund_flow': fund_flow
            }
            
        except Exception as e:
            print(f"获取市场指标失败: {str(e)}")
            return None

    def _analyze_index(self, df):
        """分析指数数据"""
        try:
            if df.empty or len(df) < 20:
                return None
                
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
            # MACD
            exp1 = df['close'].ewm(span=12, adjust=False).mean()
            exp2 = df['close'].ewm(span=26, adjust=False).mean()
            macd = exp1 - exp2
            signal = macd.ewm(span=9, adjust=False).mean()
            
            # RSI
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            # 获取最新数据
            latest = df.iloc[-1]
            prev_close = df.iloc[-2]['close']
            
            # 计算涨跌幅
            change_pct = (latest['close'] - prev_close) / prev_close * 100
            
            return {
                'current_price': latest['close'],
                'change_pct': change_pct,
                'technical': {
                    'macd': macd.iloc[-1],
                    'signal': signal.iloc[-1],
                    'rsi': rsi.iloc[-1]
                }
            }
            
        except Exception as e:
            print(f"指数分析失败: {str(e)}")
            return None

    def _get_fund_flow(self):
        """获取资金流向数据"""
        try:
            # 获取北向资金数据
            north_data = ak.stock_hsgt_hist_em()
            if not north_data.empty:
                # 确保数据是字符串类型再处理
                value = str(north_data.iloc[-1]['当日资金流入'])
                if isinstance(value, str):
                    value = value.replace('亿', '').replace(',', '')
                north_fund = {
                    'today_net': float(value)
                }
            else:
                north_fund = {'today_net': 0}
            
            # 获取主力资金数据
            main_data = ak.stock_dzjy_mrtj()
            if not main_data.empty and '成交净买额' in main_data.columns:
                main_force = {
                    'today_net': float(main_data['成交净买额'].sum()) / 100000000  # 转换为亿元
                }
            else:
                main_force = {'today_net': 0}
            
            # 获取融资融券数据
            try:
                margin_data = ak.stock_margin_detail_szt()  # 改用深交所融资融券数据
                if not margin_data.empty and '融资余额' in margin_data.columns:
                    # 确保数据是字符串类型再处理
                    value = str(margin_data.iloc[-1]['融资余额'])
                    if isinstance(value, str):
                        value = value.replace(',', '')
                    margin = {
                        'total': float(value) / 100000000  # 转换为亿元
                    }
                else:
                    margin = {'total': 0}
            except:
                try:
                    # 尝试使用上交所融资融券数据
                    margin_data = ak.stock_margin_detail_szh()
                    if not margin_data.empty and '融资余额' in margin_data.columns:
                        value = str(margin_data.iloc[-1]['融资余额'])
                        if isinstance(value, str):
                            value = value.replace(',', '')
                        margin = {
                            'total': float(value) / 100000000
                        }
                    else:
                        margin = {'total': 0}
                except:
                    margin = {'total': 0}
            
            return {
                'north_fund': north_fund,
                'main_force': main_force,
                'margin': margin
            }
            
        except Exception as e:
            print(f"获取资金流向数据失败: {str(e)}")
            return {
                'north_fund': {'today_net': 0},
                'main_force': {'today_net': 0},
                'margin': {'total': 0}
            }
            
    def get_market_sentiment(self):
        """分析市场情绪"""
        try:
            # 获取市场情绪指标
            sentiment_score = 50  # 基础分
            
            # 分析指数状态
            indices = self.get_market_indicators()
            if indices and 'indices_analysis' in indices:
                for name, data in indices['indices_analysis'].items():
                    if data:
                        # 涨跌幅影响
                        change = data.get('change_pct', 0)
                        if change > 0:
                            sentiment_score += change
                        else:
                            sentiment_score -= abs(change)
                            
                        # 技术指标影响
                        tech = data.get('technical', {})
                        if tech.get('rsi', 50) > 70:
                            sentiment_score += 10
                        elif tech.get('rsi', 50) < 30:
                            sentiment_score -= 10
                            
                        if tech.get('macd', 0) > tech.get('signal', 0):
                            sentiment_score += 5
                        else:
                            sentiment_score -= 5
            
            # 资金流向影响
            fund_flow = self._get_fund_flow()
            if fund_flow:
                north_net = float(fund_flow['north_fund']['today_net'])
                main_net = float(fund_flow['main_force']['today_net'])
                
                if north_net > 0:
                    sentiment_score += north_net
                else:
                    sentiment_score -= abs(north_net)
                    
                if main_net > 0:
                    sentiment_score += main_net
                else:
                    sentiment_score -= abs(main_net)
            
            # 确保分数在0-100之间
            sentiment_score = max(0, min(100, sentiment_score))
            
            # 判断情绪类型
            if sentiment_score >= 70:
                sentiment = 'bullish'
            elif sentiment_score >= 30:
                sentiment = 'neutral'
            else:
                sentiment = 'bearish'
            
            return {
                'sentiment': sentiment,
                'score': sentiment_score
            }
            
        except Exception as e:
            print(f"市场情绪分析失败: {str(e)}")
            return {
                'sentiment': 'neutral',
                'score': 50
            }
            
    def get_market_stage(self):
        """分析市场阶段"""
        try:
            # 获取指数数据
            indices = self.get_market_indicators()
            if not indices or 'indices_analysis' not in indices:
                return 'unknown'
                
            # 分析主要指数
            sh_index = indices['indices_analysis'].get('上证指数', {})
            if not sh_index:
                return 'unknown'
                
            # 获取技术指标
            tech = sh_index.get('technical', {})
            rsi = tech.get('rsi', 50)
            macd = tech.get('macd', 0)
            macd_signal = tech.get('signal', 0)
            
            # 获取趋势数据
            trend_data = ak.stock_zh_index_daily_em(symbol="000001")
            if trend_data is not None and not trend_data.empty:
                # 计算20日和60日均线
                trend_data['MA20'] = trend_data['收盘'].rolling(window=20).mean()
                trend_data['MA60'] = trend_data['收盘'].rolling(window=60).mean()
                
                latest = trend_data.iloc[-1]
                price = latest['收盘']
                ma20 = latest['MA20']
                ma60 = latest['MA60']
                
                # 判断市场阶段
                if price > ma20 and ma20 > ma60 and rsi > 50 and macd > macd_signal:
                    return 'uptrend'  # 上升趋势
                elif price < ma20 and ma20 < ma60 and rsi < 50 and macd < macd_signal:
                    return 'downtrend'  # 下降趋势
                elif price > ma20 and rsi > 60:
                    return 'overbought'  # 超买
                elif price < ma20 and rsi < 40:
                    return 'oversold'  # 超卖
                elif abs(price - ma20) / ma20 < 0.02:  # 价格在均线2%范围内波动
                    return 'consolidation'  # 盘整
                    
            return 'neutral'  # 无明显趋势
            
        except Exception as e:
            print(f"市场阶段分析失败: {str(e)}")
            return 'unknown'