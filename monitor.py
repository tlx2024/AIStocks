from datetime import datetime
import signal
import sys
import time
from apscheduler.schedulers.background import BackgroundScheduler
from data_fetcher import fetch_stock_data, fetch_fundamental_data
from strategy import EnhancedQuantStrategy
from market_trend_analyzer import MarketTrendAnalyzer
import pandas as pd

# 全局调度器
scheduler = None
market_analyzer = MarketTrendAnalyzer()

def handle_shutdown(signum, frame):
    """处理退出信号"""
    print("\n正在优雅退出...")
    if scheduler:
        scheduler.shutdown(wait=True)
    sys.exit(0)

def analyze_market_trend():
    """分析市场趋势"""
    print("\n【市场趋势分析】")
    indicators = market_analyzer.get_market_indicators()
    
    # 1. 输出指数状态
    print("\n大盘指数状态：")
    for name, data in indicators['indices_analysis'].items():
        print(f"\n{name}:")
        print(f"  当前价格: {data['current_price']:.2f}")
        print(f"  涨跌幅: {data['change_pct']:.2f}%")
        print(f"  技术指标:")
        print(f"    MACD: {data['technical']['macd']:.2f}")
        print(f"    RSI: {data['technical']['rsi']:.2f}")
    
    # 2. 输出资金流向
    print("\n资金流向：")
    fund_flow = indicators['fund_flow']
    if fund_flow:
        north_net = fund_flow['north_fund']['today_net']
        main_net = fund_flow['main_force']['today_net']
        margin_total = fund_flow['margin']['total']
        
        # 处理可能的无效数值
        try:
            north_net_str = f"{north_net/100000000:.2f}" if north_net != 0 else "0.00"
        except:
            north_net_str = "0.00"
            
        try:
            main_net_str = f"{main_net/100000000:.2f}" if main_net != 0 else "0.00"
        except:
            main_net_str = "0.00"
            
        try:
            margin_str = f"{margin_total/100000000:.2f}" if margin_total != 0 else "0.00"
        except:
            margin_str = "0.00"
        
        print(f"  北向资金: {north_net_str}亿")
        print(f"  主力资金: {main_net_str}亿")
        print(f"  两融余额: {margin_str}亿")
    
    # 3. 输出市场情绪
    print("\n市场情绪：")
    sentiment = indicators['market_sentiment']
    if sentiment:
        print(f"  涨跌停比: {sentiment['up_down_ratio']:.2f}")
        print(f"  情绪水平: {sentiment['sentiment_level']}")
    
    # 4. 输出市场阶段判断
    stage = indicators['market_stage']
    print(f"\n市场阶段判断: {stage['stage']}")
    print(f"综合得分: {stage['score']:.2f}")
    print(f"投资建议: {stage['suggestion']}")

def job():
    """定时任务：执行策略分析"""
    print("\n【幻方策略实时监控】")
    print(f"执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # 分析市场趋势
        analyze_market_trend()
        
        # 获取当日数据
        date_str = datetime.now().strftime("%Y%m%d")
        data = fetch_stock_data(date_str)
        if data is None or data.empty:
            print("获取股票数据失败")
            return
            
        # 获取基本面数据
        print("\n正在获取基本面数据...")
        fund_data = fetch_fundamental_data(date_str)
        if not fund_data.empty:
            data = pd.merge(data, fund_data, on='股票代码', how='left')
        
        # 执行策略分析
        strategy = EnhancedQuantStrategy()
        data = strategy.calculate_advanced_factors(data)
        signals = strategy.generate_enhanced_signals(data)
        
        if signals.empty:
            print("没有发现符合条件的股票")
            return
            
        # 输出结果
        print("\n【策略选股结果】")
        result_df = signals[['股票代码', '股票名称', '收盘价', '涨跌幅', '换手率', 'Composite_Score']].sort_values('Composite_Score', ascending=False)
        print(result_df.head(3).to_string(index=False))
        
        # 保存结果
        output_file = f'monitor_report_{date_str}.xlsx'
        result_df.to_excel(output_file, index=False)
        print(f"\n详细报告已保存至: {output_file}")
        
    except Exception as e:
        print(f"监控任务执行出错: {e}")

def main():
    global scheduler
    print("启动股票策略监控系统...")
    
    # 设置信号处理
    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)
    
    # 使用后台调度器
    scheduler = BackgroundScheduler()
    
    # 添加定时任务：每个交易日9:30、11:30、14:30执行
    scheduler.add_job(job, 'cron', day_of_week='mon-fri', hour='9,11,14', minute=30)
    
    # 启动调度器
    scheduler.start()
    
    # 立即执行一次
    job()
    
    try:
        # 主线程保持运行，但不阻塞
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        handle_shutdown(None, None)

if __name__ == '__main__':
    main()