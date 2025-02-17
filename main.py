import argparse
from datetime import datetime
import pandas as pd
from data_fetcher import fetch_stock_data, fetch_fundamental_data
from strategy import BasicStrategy, EnhancedQuantStrategy
from report_generator import generate_report
from market_analysis import MarketAnalyzer

def parse_args():
    parser = argparse.ArgumentParser(description='股票交易策略系统')
    parser.add_argument('--date', type=str, help='交易日期，格式：YYYYMMDD', default=datetime.now().strftime('%Y%m%d'))
    parser.add_argument('--strategy', type=str, choices=['basic', 'enhanced'], default='basic', help='选择策略类型：basic或enhanced')
    parser.add_argument('--no-cache', action='store_true', help='不使用缓存数据')
    parser.add_argument('--output', type=str, help='输出文件名，默认为report_日期.xlsx')
    return parser.parse_args()

def main():
    # 解析命令行参数
    args = parse_args()
    
    print(f"开始运行策略，日期: {args.date}")
    
    try:
        # 获取股票数据（包括历史数据）
        stock_data = fetch_stock_data(args.date, use_cache=not args.no_cache)
        if stock_data is None or stock_data.empty:
            print("未获取到股票数据")
            return
            
        # 确保股票代码为字符串类型
        stock_data['股票代码'] = stock_data['股票代码'].astype(str).str.zfill(6)
        
        # 获取基本面数据
        fund_data = fetch_fundamental_data(args.date, use_cache=not args.no_cache)
        if fund_data is None:
            print("未获取到基本面数据")
            return
            
        # 确保两边的股票代码都是字符串类型
        fund_data['股票代码'] = fund_data['股票代码'].astype(str).str.zfill(6)
        
        # 只合并目标日期的数据
        target_date = pd.to_datetime(args.date)
        target_data = stock_data[stock_data['交易日期'] == target_date].copy()
        target_data = pd.merge(target_data, fund_data, on='股票代码', how='left')
        
        # 将合并后的数据更新回原始数据框
        stock_data = stock_data[stock_data['交易日期'] != target_date]
        stock_data = pd.concat([stock_data, target_data])
        stock_data = stock_data.sort_values(['股票代码', '交易日期'])
        
        # 选择并运行策略
        if args.strategy == 'enhanced':
            print("使用增强策略分析...")
            strategy = EnhancedQuantStrategy()
            stock_data = strategy.calculate_advanced_factors(stock_data)
            # 只对目标日期的数据生成信号
            target_data = stock_data[stock_data['交易日期'] == target_date].copy()
            signals = strategy.generate_enhanced_signals(target_data)
        else:
            print("使用基础策略分析...")
            strategy = BasicStrategy()
            stock_data = strategy.analyze(stock_data)
            signals = strategy.generate_signals(stock_data)
        
        if signals is not None and not signals.empty:
            print("\n选股结果：")
            result_df = signals[['股票代码', '股票名称', '收盘价', '涨跌幅', '换手率']].copy()
            if 'Composite_Score' in signals.columns:
                result_df['综合得分'] = signals['Composite_Score']
            elif '技术得分' in signals.columns:
                result_df['综合得分'] = signals['技术得分']
            print(result_df.to_string(index=False))
            
            # 集成市场分析功能
            analyzer = MarketAnalyzer()
            market_data = analyzer.fetch_market_data()
            if market_data:
                market_analysis = analyzer.analyze_market_data(market_data)
                report = analyzer.generate_market_report(signals, market_analysis)
                print("\n" + "="*50)
                print(report)
                print("="*50)
            else:
                print("无法获取市场数据，跳过市场分析")
            
            # 生成报告
            output_file = args.output if args.output else f'report_{args.date}.xlsx'
            generate_report(signals, output_file)
            print(f"\n分析报告已生成: {output_file}")
        else:
            print("没有找到符合条件的股票")
    except Exception as e:
        print(f"运行策略出错: {str(e)}")

if __name__ == '__main__':
    main()
