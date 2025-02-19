import pandas as pd
import numpy as np
from config import STRATEGY_CONFIG
from data_fetcher import fetch_fundamental_data
from datetime import datetime, timedelta
import akshare as ak

class BasicStrategy:
    def __init__(self):
        self.config = STRATEGY_CONFIG

    def calculate_technical_indicators(self, df):
        """计算技术指标"""
        # 计算5日、10日、20日均线
        df['MA5'] = df['收盘价'].rolling(window=5).mean()
        df['MA10'] = df['收盘价'].rolling(window=10).mean()
        df['MA20'] = df['收盘价'].rolling(window=20).mean()
        
        # 计算MACD
        exp12 = df['收盘价'].ewm(span=12, adjust=False).mean()
        exp26 = df['收盘价'].ewm(span=26, adjust=False).mean()
        df['MACD'] = exp12 - exp26
        df['SIGNAL'] = df['MACD'].ewm(span=9, adjust=False).mean()
        
        # 计算RSI
        delta = df['收盘价'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        return df

    def analyze(self, data):
        if data is None:
            return pd.DataFrame()  # 返回空DataFrame如果数据获取失败
            
        # 数据预处理
        data = data[
            (data['成交额'] >= self.config['min_turnover'])
        ].copy()
        
        # 计算技术指标
        data = self.calculate_technical_indicators(data)
        
        # 生成买入信号
        data['buy_signal'] = np.where(
            (data['MACD'] > data['SIGNAL']) &  # MACD金叉
            (data['RSI'] < 70) &               # RSI未超买
            (data['涨跌幅'] > -3) &            # 当日跌幅不大
            (data['换手率'] > 1),              # 换手率大于1%
            1, 0)
        
        # 生成卖出信号
        data['sell_signal'] = np.where(
            (data['MACD'] < data['SIGNAL']) |  # MACD死叉
            (data['RSI'] > 80) |               # RSI超买
            (data['涨跌幅'] < -5),             # 当日跌幅过大
            1, 0)
        
        return data

    def generate_signals(self, analyzed_data):
        if analyzed_data.empty:
            return pd.DataFrame()
            
        # 确保所属行业列存在
        if '所属行业' not in analyzed_data.columns:
            analyzed_data['所属行业'] = '其他'
            
        signals = analyzed_data[
            (analyzed_data['buy_signal'] == 1) | 
            (analyzed_data['sell_signal'] == 1)
        ][['股票代码', '股票名称', '收盘价', 'buy_signal', 'sell_signal', 
           '所属行业', '涨跌幅', '换手率', 'MACD', 'SIGNAL', 'RSI']]
        
        signals['操作建议'] = np.where(
            signals['buy_signal'] == 1, '买入', '卖出')
        signals['目标价格'] = np.where(
            signals['buy_signal'] == 1,
            signals['收盘价'] * self.config['take_profit'],
            signals['收盘价'] * self.config['stop_loss']
        )
        
        # 添加建议理由
        def get_reason(row):
            if row['buy_signal'] == 1:
                reasons = []
                if row['换手率'] > 3:
                    reasons.append('换手活跃')
                if row['涨跌幅'] > 0:
                    reasons.append('势头向上')
                if row['MACD'] > row['SIGNAL']:
                    reasons.append('MACD金叉')
                return '、'.join(reasons) if reasons else '技术面改善'
            else:
                if row['涨跌幅'] < -5:
                    return '跌幅过大'
                if row['RSI'] > 80:
                    return 'RSI超买'
                return '技术面转弱'
                
        signals['建议理由'] = signals.apply(get_reason, axis=1)
        
        return signals

class EnhancedQuantStrategy:
    def __init__(self):
        self.config = STRATEGY_CONFIG
        
    def analyze_stock(self, symbol):
        try:
            # 确保股票代码格式正确
            if not symbol.startswith(('600', '601', '602', '603', '605', '688', '000', '002', '300')):
                raise ValueError("无效的股票代码格式")
            
            # 获取更长时间范围的历史数据
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=180)).strftime('%Y%m%d')
            
            # 获取股票数据
            df = ak.stock_zh_a_hist(symbol=symbol, period="daily",
                                  start_date=start_date, end_date=end_date,
                                  adjust="qfq")
            
            if df.empty or len(df) < 30:
                raise ValueError("获取不到足够的历史数据")
            
            # 重命名列
            df = df.rename(columns={
                '日期': 'date',
                '开盘': 'open',
                '收盘': 'close',
                '最高': 'high',
                '最低': 'low',
                '成交量': 'volume'
            })
            
            # 确保按日期排序
            df = df.sort_values('date')
            
            # 计算技术指标
            analysis = self._calculate_indicators(df)
            
            # 生成分析报告
            report = self._generate_analysis_report(analysis, symbol)
            return report
            
        except Exception as e:
            raise Exception(f"增强策略分析失败: {str(e)}")
    
    def _calculate_indicators(self, df):
        """计算各种技术指标"""
        # 计算移动平均线
        df['MA5'] = df['close'].rolling(window=5).mean()
        df['MA10'] = df['close'].rolling(window=10).mean()
        df['MA20'] = df['close'].rolling(window=20).mean()
        df['MA60'] = df['close'].rolling(window=60).mean()
        
        # 计算MACD
        exp1 = df['close'].ewm(span=12, adjust=False).mean()
        exp2 = df['close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = exp1 - exp2
        df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        df['MACD_Hist'] = df['MACD'] - df['Signal']
        
        # 计算RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # 计算布林带
        df['BB_middle'] = df['close'].rolling(window=20).mean()
        df['BB_upper'] = df['BB_middle'] + 2 * df['close'].rolling(window=20).std()
        df['BB_lower'] = df['BB_middle'] - 2 * df['close'].rolling(window=20).std()
        
        # 获取最新数据
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        
        return {
            'latest_price': latest['close'],
            'prev_price': prev['close'],
            'change_pct': ((latest['close'] - prev['close']) / prev['close'] * 100),
            'volume': latest['volume'],
            'ma5': latest['MA5'],
            'ma10': latest['MA10'],
            'ma20': latest['MA20'],
            'ma60': latest['MA60'],
            'rsi': latest['RSI'],
            'macd': latest['MACD'],
            'macd_signal': latest['Signal'],
            'macd_hist': latest['MACD_Hist'],
            'bb_upper': latest['BB_upper'],
            'bb_middle': latest['BB_middle'],
            'bb_lower': latest['BB_lower'],
            'date': latest['date']
        }
    
    def _generate_analysis_report(self, analysis, symbol):
        """生成详细的分析报告"""
        report = []
        report.append(f"=== {symbol} 增强量化分析报告 ===\n")
        
        # 价格信息
        report.append(f"当前价格: {analysis['latest_price']:.2f}")
        report.append(f"涨跌幅: {analysis['change_pct']:.2f}%")
        report.append(f"成交量: {analysis['volume']/10000:.2f}万")
        
        # 趋势分析
        report.append("\n=== 趋势分析 ===")
        if analysis['latest_price'] > analysis['ma60']:
            report.append("- 长期趋势：上升")
        else:
            report.append("- 长期趋势：下降")
            
        if analysis['latest_price'] > analysis['ma20']:
            report.append("- 中期趋势：上升")
        else:
            report.append("- 中期趋势：下降")
            
        if analysis['latest_price'] > analysis['ma5']:
            report.append("- 短期趋势：上升")
        else:
            report.append("- 短期趋势：下降")
        
        # MACD分析
        report.append("\n=== MACD分析 ===")
        if analysis['macd'] > analysis['macd_signal']:
            report.append("- MACD金叉形成，买入信号")
        else:
            report.append("- MACD死叉形成，卖出信号")
        
        # RSI分析
        report.append("\n=== RSI分析 ===")
        rsi = analysis['rsi']
        if rsi > 70:
            report.append("- RSI超买（%.2f），注意回调风险" % rsi)
        elif rsi < 30:
            report.append("- RSI超卖（%.2f），可能存在反弹机会" % rsi)
        else:
            report.append("- RSI处于中性区间（%.2f）" % rsi)
        
        # 布林带分析
        report.append("\n=== 布林带分析 ===")
        if analysis['latest_price'] > analysis['bb_upper']:
            report.append("- 股价突破布林带上轨，超买状态")
        elif analysis['latest_price'] < analysis['bb_lower']:
            report.append("- 股价突破布林带下轨，超卖状态")
        else:
            report.append("- 股价在布林带中轨附近波动")
        
        # 投资建议
        report.append("\n=== 投资建议 ===")
        if (analysis['latest_price'] > analysis['ma20'] and 
            analysis['macd'] > analysis['macd_signal'] and 
            30 < analysis['rsi'] < 70):
            report.append("1. 多头行情，可以考虑持有或逢低买入")
            report.append("2. 建议止损位设置在MA20下方")
        elif (analysis['latest_price'] < analysis['ma20'] and 
              analysis['macd'] < analysis['macd_signal'] and 
              analysis['rsi'] > 70):
            report.append("1. 空头行情，建议减持或观望")
            report.append("2. 等待企稳信号后再考虑入场")
        else:
            report.append("1. 目前处于震荡整理阶段")
            report.append("2. 建议观望，等待明确的趋势信号")
        
        return "\n".join(report)