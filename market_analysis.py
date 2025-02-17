import os
import json
import requests
from datetime import datetime
import akshare as ak
import pandas as pd
from config import DEEPSEEK_API_KEY, MARKET_ANALYSIS_CONFIG, DEEPSEEK_API_ENDPOINT

class MarketAnalyzer:
    def __init__(self):
        self.api_key = DEEPSEEK_API_KEY
        self.config = MARKET_ANALYSIS_CONFIG
        
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
