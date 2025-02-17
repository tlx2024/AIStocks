import pandas as pd
import numpy as np
from config import STRATEGY_CONFIG
from data_fetcher import fetch_fundamental_data

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

class EnhancedQuantStrategy(BasicStrategy):
    def __init__(self):
        super().__init__()  # 确保调用父类的初始化方法
        # 因子权重
        self.factor_weights = {
            'momentum': 0.3,    # 动量因子权重
            'value': 0.3,      # 估值因子权重
            'quality': 0.2,    # 质量因子权重
            'sentiment': 0.2   # 情绪因子权重
        }
        
        # 使用从config.py导入的STRATEGY_CONFIG
        self.conditions = self.config
    
    def calculate_advanced_factors(self, data):
        """计算高级因子"""
        try:
            print("\n开始计算多因子...")
            
            # 确保数据按日期和股票代码排序
            data = data.sort_values(['交易日期', '股票代码'])
            
            # 创建因子列
            data['20D_Return'] = np.nan
            data['Volume_5D'] = np.nan
            data['Turnover_5D'] = np.nan
            data['Volatility_20D'] = np.nan
            data['MA5'] = np.nan
            data['MA20'] = np.nan
            data['Trend'] = np.nan
            
            # 按股票分组计算
            grouped = data.groupby('股票代码')
            
            # 1. 动量因子 - 20日收益率
            data['20D_Return'] = grouped['收盘价'].transform(lambda x: x.pct_change(20))
            
            # 2. 成交量因子
            data['Volume_5D'] = grouped['成交量'].transform(lambda x: x.rolling(5).mean())
            data['Turnover_5D'] = grouped['换手率'].transform(lambda x: x.rolling(5).mean())
            
            # 3. 波动率因子
            data['Volatility_20D'] = grouped['涨跌幅'].transform(lambda x: x.rolling(20).std())
            
            # 4. 趋势因子
            data['MA5'] = grouped['收盘价'].transform(lambda x: x.rolling(5).mean())
            data['MA20'] = grouped['收盘价'].transform(lambda x: x.rolling(20).mean())
            data['Trend'] = data['MA5'] / data['MA20'] - 1
            
            # 获取最新日期的数据
            latest_date = data['交易日期'].max()
            latest_data = data[data['交易日期'] == latest_date]
            
            # 打印因子范围
            print(f"动量因子计算完成，20日收益率范围: {latest_data['20D_Return'].min():.2f}% 到 {latest_data['20D_Return'].max():.2f}%")
            print(f"5日平均成交量范围: {latest_data['Volume_5D'].min():.2e} 到 {latest_data['Volume_5D'].max():.2e}")
            print(f"5日平均换手率范围: {latest_data['Turnover_5D'].min():.2f}% 到 {latest_data['Turnover_5D'].max():.2f}%")
            print(f"20日波动率范围: {latest_data['Volatility_20D'].min():.2f}% 到 {latest_data['Volatility_20D'].max():.2f}%")
            print(f"趋势因子范围: {latest_data['Trend'].min():.2f} 到 {latest_data['Trend'].max():.2f}")
            
            # 数据质量检查
            print("\n数据质量检查:")
            for col in ['20D_Return', 'Volume_5D', 'Turnover_5D', 'Volatility_20D', 'Trend']:
                missing = latest_data[col].isna().sum()
                if missing > 0:
                    print(f"警告: {col} 有 {missing} 个缺失值")
            
            return data
            
        except Exception as e:
            print(f"因子计算出错: {e}")
            import traceback
            traceback.print_exc()
            return data
    
    def generate_enhanced_signals(self, data):
        """生成增强版交易信号"""
        print("\n开始生成交易信号...")
        try:
            # 填充缺失值
            factor_cols = ['20D_Return', 'Turnover_5D', 'Volatility_20D', 'Trend']
            for col in factor_cols:
                if col in data.columns:
                    median_val = data[col].median()
                    data[col] = data[col].fillna(median_val)
            
            # 处理极端值
            for col in factor_cols:
                if col in data.columns:
                    # 计算上下四分位数
                    Q1 = data[col].quantile(0.25)
                    Q3 = data[col].quantile(0.75)
                    IQR = Q3 - Q1
                    
                    # 定义极端值边界
                    lower_bound = Q1 - 1.5 * IQR
                    upper_bound = Q3 + 1.5 * IQR
                    
                    # 处理极端值
                    data[col] = data[col].clip(lower_bound, upper_bound)
            
            # 数据标准化
            weights = {
                '20D_Return': self.factor_weights['momentum'],
                'Turnover_5D': self.factor_weights['value'],
                'Volatility_20D': -self.factor_weights['quality'],  # 波动率越小越好
                'Trend': self.factor_weights['sentiment']
            }
            
            # 标准化并计算综合得分
            composite_score = 0
            for col in factor_cols:
                if col in data.columns:
                    # 标准化
                    mean = data[col].mean()
                    std = data[col].std()
                    if std != 0:
                        data[f'{col}_Z'] = (data[col] - mean) / std
                        # 累加到综合得分
                        composite_score += data[f'{col}_Z'] * weights[col]
                        print(f"{col} Z-score范围: {data[f'{col}_Z'].min():.2f} 到 {data[f'{col}_Z'].max():.2f}")
                    else:
                        data[f'{col}_Z'] = 0
                        print(f"{col} Z-score范围: 0 到 0 (标准差为0)")
            
            # 保存综合得分
            data['Composite_Score'] = composite_score
            
            print(f"\n综合得分范围: {data['Composite_Score'].min():.2f} 到 {data['Composite_Score'].max():.2f}")
            
            # 初次筛选 - 使用相对宽松的条件
            signals = data[
                (data['收盘价'] >= 5.0) &  # 最低价格限制
                (data['成交量'] >= 1e6) &  # 最低成交量100万
                (data['换手率'] >= 0.5) &  # 最低换手率0.5%
                (data['Volatility_20D'] <= 0.2)  # 波动率限制20%
            ].copy()
            
            print(f"\n初次筛选后剩余股票数: {len(signals)}")
            
            if len(signals) < 10:
                print("股票数量不足，使用更宽松的条件...")
                # 使用非常宽松的条件
                signals = data[
                    (data['收盘价'] >= 3.0) &  # 降低最低价格限制
                    (data['成交量'] >= 5e5) &  # 降低最低成交量到50万
                    (data['换手率'] >= 0.3)  # 降低最低换手率到0.3%
                ].copy()
                print(f"最终筛选后剩余股票数: {len(signals)}")
            
            if len(signals) > 0:
                # 按综合得分排序
                signals = signals.sort_values('Composite_Score', ascending=False)
                # 只保留前30只股票
                signals = signals.head(30)
                
                # 打印选股结果
                print("\n选股结果:")
                result_cols = ['股票代码', '股票名称', '收盘价', '涨跌幅', '换手率', 'Composite_Score']
                print(signals[result_cols].to_string())
                
                return signals
            else:
                print("没有找到符合条件的股票")
                return pd.DataFrame()
                
        except Exception as e:
            print(f"信号生成出错: {e}")
            import traceback
            traceback.print_exc()
            return pd.DataFrame()