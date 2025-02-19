from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.table import Table
from strategy import BasicStrategy, EnhancedQuantStrategy
from market_analysis import MarketAnalyzer
from monitor import analyze_market_trend
from market_trend_analyzer import MarketTrendAnalyzer
import sys
import argparse
import pandas as pd

class MainMenu:
    def __init__(self):
        self.console = Console()
        self.market_analyzer = MarketAnalyzer()

    def display_header(self):
        self.console.print(
            Panel.fit("[bold cyan]AI 股票分析系统[/bold cyan]",
            subtitle="by TLX 2024",
            style="blue")
        )

    def display_menu_options(self):
        table = Table(show_header=False, box=None)
        table.add_column("选项", style="cyan")
        table.add_column("描述", style="white")
        
        options = {
            "1": "个股技术分析",
            "2": "增强策略分析",
            "3": "智能选股",
            "4": "回测结果查看",
            "5": "系统设置",
            "Q": "退出系统"
        }
        
        for key, value in options.items():
            table.add_row(f"[{key}]", value)
            
        self.console.print(table)

    def show_main_menu(self):
        self.display_header()
        self.display_menu_options()
        
        options = ["1", "2", "3", "4", "5", "Q"]
        choice = Prompt.ask(
            "请选择操作",
            choices=options,
            show_choices=False
        )
        return choice

    def handle_choice(self, choice):
        if choice == "1":
            self._show_stock_analysis()
        elif choice == "2":
            self._handle_enhanced_analysis()
        elif choice == "3":
            self._show_stock_selection()
        elif choice == "4":
            self._show_backtest_results()
        elif choice == "5":
            self._show_settings()

    def _show_stock_analysis(self):
        self.console.print("[bold green]个股技术分析[/bold green]")
        stock_code = Prompt.ask("请输入股票代码")
        try:
            analysis_result = self.market_analyzer.analyze_stock(stock_code)
            formatted_result = self.format_analysis_result(analysis_result)
            self.console.print(Panel(formatted_result, title=f"股票分析结果 - {stock_code}"))
        except Exception as e:
            self.console.print(f"[red]分析出错: {str(e)}[/red]")
        
        input("\n按回车键返回主菜单...")

    def _handle_enhanced_analysis(self):
        """处理增强策略分析"""
        self.console.print("\n增强策略分析", style="bold green")
        stock_code = Prompt.ask("请输入股票代码")
        try:
            strategy = EnhancedQuantStrategy()
            analysis_result = strategy.analyze_stock(stock_code)  # Changed from analyze to analyze_stock
            self.console.print(analysis_result)
        except Exception as e:
            self.console.print(f"[red]分析出错: {str(e)}[/red]")
        
        input("\n按回车键返回主菜单...")

    def _show_stock_selection(self):
        """显示智能选股结果"""
        self.console.print("\n[bold green]智能选股[/bold green]")
        try:
            # 获取市场分析
            market_analysis = self.market_analyzer.analyze_market()
            self.console.print("\n市场分析结果:")
            self._display_market_analysis(market_analysis)
            
            # 获取选股结果
            trend_analyzer = MarketTrendAnalyzer()
            selected_stocks = trend_analyzer.get_selected_stocks(market_analysis)
            
            if selected_stocks:
                # 创建表格显示选股结果
                table = Table(title="推荐股票列表")
                table.add_column("代码", style="cyan")
                table.add_column("名称", style="magenta")
                table.add_column("行业", style="yellow")
                table.add_column("推荐理由", style="green")
                
                for stock in selected_stocks:
                    table.add_row(
                        stock['code'],
                        stock['name'],
                        stock['industry'],
                        stock['reason']
                    )
                
                self.console.print("\n选股结果:")
                self.console.print(table)
            else:
                self.console.print("\n[yellow]未找到符合条件的股票，建议观望[/yellow]")
            
            self.console.print("\n分析完成！")
            
        except Exception as e:
            self.console.print(f"[red]选股过程出错: {str(e)}[/red]")
        
        input("\n按回车键返回主菜单...")

    def _show_backtest_results(self):
        self.console.print("[yellow]回测结果查看功能开发中...[/yellow]")
        input("\n按回车键返回主菜单...")

    def _show_settings(self):
        self.console.print("[yellow]系统设置功能开发中...[/yellow]")
        input("\n按回车键返回主菜单...")

    def format_analysis_result(self, analysis):
        """格式化分析结果为rich表格"""
        from rich.table import Table
        from rich.panel import Panel
        from rich.text import Text
        from rich.console import Console
        
        # 创建表格
        table = Table(title=f"股票分析报告 - {analysis['code']} {analysis['name']}")
        
        # 添加基本信息
        table.add_column("指标", style="cyan")
        table.add_column("数值", style="magenta")
        
        # 添加价格信息
        table.add_row("当前价格", f"{float(analysis['price']):.2f}")
        table.add_row("涨跌幅", f"{float(analysis['change']):.2f}%")
        table.add_row("成交量", f"{int(analysis['volume'])/10000:.2f}万")
        
        # 添加技术指标
        table.add_row("MA5", f"{float(analysis['ma5']):.2f}")
        table.add_row("MA10", f"{float(analysis['ma10']):.2f}")
        table.add_row("MA20", f"{float(analysis['ma20']):.2f}")
        table.add_row("RSI", f"{float(analysis['rsi']):.2f}")
        table.add_row("MACD", f"{float(analysis['macd']):.3f}")
        table.add_row("MACD信号线", f"{float(analysis['macd_signal']):.3f}")
        
        # 创建趋势分析面板
        trend_text = Text("\n".join([f"• {t.strip()}" for t in analysis['trend'].split("|")]))
        trend_panel = Panel(trend_text, title="趋势分析", border_style="green")
        
        # 使用临时控制台将表格和面板渲染为字符串
        console = Console(record=True)
        console.print(table)
        console.print(trend_panel)
        return console.export_text()

    def _display_market_analysis(self, market_analysis):
        """显示市场分析结果"""
        if not market_analysis or 'indicators' not in market_analysis:
            return
            
        indicators = market_analysis['indicators']
        
        # 显示指数状态
        if 'indices_analysis' in indicators:
            indices_table = Table(title="大盘指数状态")
            indices_table.add_column("指数", style="cyan")
            indices_table.add_column("价格", style="white")
            indices_table.add_column("涨跌幅", style="green")
            indices_table.add_column("MACD", style="yellow")
            indices_table.add_column("RSI", style="magenta")
            
            for name, data in indicators['indices_analysis'].items():
                if data and isinstance(data, dict):
                    indices_table.add_row(
                        name,
                        f"{data.get('current_price', 0):.2f}",
                        f"{data.get('change_pct', 0):.2f}%",
                        f"{data.get('technical', {}).get('macd', 0):.2f}",
                        f"{data.get('technical', {}).get('rsi', 0):.2f}"
                    )
            self.console.print(indices_table)
        
        # 显示资金流向
        if 'fund_flow' in indicators:
            fund_flow = indicators['fund_flow']
            flow_table = Table(title="资金流向")
            flow_table.add_column("指标", style="cyan")
            flow_table.add_column("数值", style="white")
            
            # 北向资金
            north_net = fund_flow.get('north_fund', {}).get('today_net', 0)
            if not pd.isna(north_net):
                flow_table.add_row("北向资金净流入", f"{north_net:.2f}亿")
            else:
                flow_table.add_row("北向资金净流入", "暂无数据")
            
            # 主力资金
            main_net = fund_flow.get('main_force', {}).get('today_net', 0)
            if not pd.isna(main_net):
                flow_table.add_row("主力资金净流入", f"{main_net:.2f}亿")
            else:
                flow_table.add_row("主力资金净流入", "暂无数据")
            
            # 融资融券
            margin_total = fund_flow.get('margin', {}).get('total', 0)
            if not pd.isna(margin_total):
                flow_table.add_row("融资融券余额", f"{margin_total:.2f}亿")
            else:
                flow_table.add_row("融资融券余额", "暂无数据")
            
            self.console.print(flow_table)
