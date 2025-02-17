import tushare as ts
import akshare as ak
import baostock as bs
import pandas as pd
from datetime import datetime
import time
import os
from config import TUSHARE_TOKEN

# 定义缓存目录
CACHE_DIR = "data_cache"

# 统一的列名映射
COLUMN_MAPPING = {
    # Tushare列名映射
    'amount': '成交额',
    'vol': '成交量',
    'pct_chg': '涨跌幅',
    'ts_code': '股票代码',
    'name': '股票名称',
    'industry': '所属行业',
    'close': '收盘价',
    'open': '开盘价',
    'high': '最高价',
    'low': '最低价',
    'pre_close': '昨收价',
    'change': '涨跌额',
    'turnover_rate': '换手率',
    
    # Baostock列名映射
    'code': '股票代码',
    'turn': '换手率',
    'pctChg': '涨跌幅',
    'volume': '成交量',
    
    # AKShare列名映射
    '代码': '股票代码',
    '名称': '股票名称',
    '最新价': '收盘价',
    '今开': '开盘价',
    '最高': '最高价',
    '最低': '最低价',
    '昨收': '昨收价',
    '涨跌额': '涨跌额',
    '涨跌幅': '涨跌幅',
    '成交量': '成交量',
    '换手率': '换手率',
    '所属行业': '所属行业'
}

def standardize_columns(df):
    """统一数据列名"""
    for old_name, new_name in COLUMN_MAPPING.items():
        if old_name in df.columns:
            df = df.rename(columns={old_name: new_name})
    return df

def get_cache_file_path(trade_date):
    """获取缓存文件路径"""
    return os.path.join(CACHE_DIR, f"stock_data_{trade_date}.csv")

def get_fundamental_cache_file_path(trade_date):
    """获取基本面数据缓存文件路径"""
    return os.path.join(CACHE_DIR, f"fundamental_data_{trade_date}.csv")

def save_to_cache(data, trade_date):
    """保存数据到缓存文件"""
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)
    cache_file = get_cache_file_path(trade_date)
    
    # 确保数据类型正确
    data['交易日期'] = pd.to_datetime(data['交易日期'])
    data['股票代码'] = data['股票代码'].astype(str).str.zfill(6)
    numeric_columns = ['开盘价', '收盘价', '最高价', '最低价', '成交量', '成交额', '振幅', '涨跌幅', '涨跌额', '换手率']
    for col in numeric_columns:
        if col in data.columns:
            data[col] = pd.to_numeric(data[col], errors='coerce')
    
    # 保存数据
    data.to_csv(cache_file, index=False, encoding='utf-8')
    print(f"数据已缓存到: {cache_file}")

def load_from_cache(trade_date):
    """从缓存文件加载数据"""
    cache_file = get_cache_file_path(trade_date)
    if os.path.exists(cache_file):
        try:
            # 读取数据
            data = pd.read_csv(cache_file, encoding='utf-8')
            
            # 转换数据类型
            data['交易日期'] = pd.to_datetime(data['交易日期'])
            data['股票代码'] = data['股票代码'].astype(str).str.zfill(6)
            numeric_columns = ['开盘价', '收盘价', '最高价', '最低价', '成交量', '成交额', '振幅', '涨跌幅', '涨跌额', '换手率']
            for col in numeric_columns:
                if col in data.columns:
                    data[col] = pd.to_numeric(data[col], errors='coerce')
            
            print(f"从缓存加载数据: {cache_file}")
            return data
        except Exception as e:
            print(f"读取缓存文件失败: {e}")
    return None

def fetch_stock_data_akshare(trade_date):
    """使用AKShare获取股票数据"""
    try:
        print("正在使用AKShare获取数据...")
        # 获取A股所有股票列表
        stock_list = ak.stock_zh_a_spot_em()
        
        # 获取行业信息
        try:
            print("正在获取行业信息...")
            industry_data = ak.stock_board_industry_name_em()
            # 提取股票代码和所属行业
            industry_dict = {}
            for _, row in industry_data.iterrows():
                try:
                    # 获取行业成分股
                    stocks = ak.stock_board_industry_cons_em(symbol=row['板块名称'])
                    # 更新行业字典
                    for _, stock in stocks.iterrows():
                        industry_dict[stock['代码']] = row['板块名称']
                except:
                    continue
            
            # 添加行业信息到股票列表
            stock_list['所属行业'] = stock_list['代码'].map(industry_dict)
            stock_list['所属行业'].fillna('其他', inplace=True)
            print("行业信息获取完成")
        except Exception as e:
            print(f"获取行业信息失败: {e}")
            stock_list['所属行业'] = '其他'
        
        # 统一数据格式
        stock_list = standardize_columns(stock_list)
        
        # 添加交易日期
        stock_list['交易日期'] = trade_date
        
        # 打印列名用于调试
        print("获取到的数据列名:", stock_list.columns.tolist())
        
        return stock_list
    except Exception as e:
        print(f"AKShare获取数据失败: {e}")
        return None

def fetch_stock_data_baostock(trade_date):
    """使用Baostock获取股票数据"""
    try:
        print("正在使用Baostock获取数据...")
        # 登录系统
        bs.login()
        
        # 获取股票列表
        stock_rs = bs.query_all_stock(trade_date)
        stock_df = stock_rs.get_data()
        
        result_list = []
        
        for _, row in stock_df.iterrows():
            try:
                # 获取当日交易数据
                rs = bs.query_history_k_data_plus(
                    row["code"],
                    "date,code,open,high,low,close,volume,amount,turn,pctChg,industry",
                    start_date=trade_date,
                    end_date=trade_date,
                    frequency="d",
                    adjustflag="3"
                )
                data = rs.get_data()
                if not data.empty:
                    result_list.append(data)
            except:
                continue
        
        if result_list:
            result_df = pd.concat(result_list)
            # 统一数据格式
            result_df = standardize_columns(result_df)
            
            # 补充股票名称
            try:
                stock_names = ak.stock_zh_a_spot_em()[['代码', '名称']]
                stock_names = stock_names.rename(columns={'代码': '股票代码', '名称': '股票名称'})
                result_df = pd.merge(result_df, stock_names, on='股票代码', how='left')
            except:
                result_df['股票名称'] = ''
            
            return result_df
            
        return None
    except Exception as e:
        print(f"Baostock获取数据失败: {e}")
        return None
    finally:
        bs.logout()

def get_start_date(trade_date):
    """计算开始日期，往前推30个交易日"""
    try:
        # 将日期转换为datetime对象
        end_date = pd.to_datetime(trade_date)
        # 往前推45天（考虑到节假日，确保能获取到30个交易日）
        start_date = end_date - pd.Timedelta(days=45)
        return start_date.strftime('%Y%m%d')
    except Exception as e:
        print(f"计算开始日期失败: {e}")
        # 如果计算失败，往前推45天
        return (pd.to_datetime(trade_date) - pd.Timedelta(days=45)).strftime('%Y%m%d')

def fetch_stock_data(trade_date, use_cache=True):
    """获取指定日期的股票数据，包括必要的历史数据"""
    
    # 如果启用缓存，尝试从缓存加载
    if use_cache:
        cached_data = load_from_cache(trade_date)
        if cached_data is not None:
            cached_data['股票代码'] = cached_data['股票代码'].astype(str).str.zfill(6)
            return cached_data
    
    print(f"正在获取股票数据，包括历史数据...")
    try:
        # 计算开始日期
        start_date = get_start_date(trade_date)
        print(f"获取数据区间: {start_date} 至 {trade_date}")
        
        # 使用AKShare获取股票列表
        stock_list = ak.stock_info_a_code_name()
        stock_list = stock_list.rename(columns={'code': '股票代码', 'name': '股票名称'})
        
        # 获取行业信息
        print("正在获取行业信息...")
        try:
            # 获取东方财富行业列表
            industry_list = ak.stock_board_industry_name_em()
            
            # 创建行业映射字典
            industry_dict = {}
            total_industries = len(industry_list)
            
            for idx, (_, industry) in enumerate(industry_list.iterrows(), 1):
                try:
                    # 获取行业成分股
                    stocks = ak.stock_board_industry_cons_em(symbol=industry['板块名称'])
                    # 更新行业字典
                    for _, stock in stocks.iterrows():
                        stock_code = stock['代码'].strip()
                        if stock_code.startswith('6'):  # 上证
                            stock_code = f"sh{stock_code}"
                        else:  # 深证
                            stock_code = f"sz{stock_code}"
                        industry_dict[stock_code] = industry['板块名称']
                    
                    if idx % 5 == 0:
                        print(f"已处理 {idx}/{total_industries} 个行业")
                        
                except Exception as e:
                    print(f"获取行业 {industry['板块名称']} 成分股失败: {e}")
                    continue
            
            # 将行业信息添加到股票列表中
            stock_list['所属行业'] = stock_list['股票代码'].map(industry_dict)
            stock_list['所属行业'] = stock_list['所属行业'].fillna('其他')
            print(f"成功获取行业信息，共 {len(industry_dict)} 只股票")
            
        except Exception as e:
            print(f"获取行业信息失败: {e}")
            stock_list['所属行业'] = '其他'
        
        print("行业信息处理完成")
        
        # 获取历史数据
        print("正在获取历史数据...")
        all_data = []
        total_stocks = len(stock_list)
        for idx, (_, stock_info) in enumerate(stock_list.iterrows(), 1):
            stock_code = stock_info['股票代码']
            try:
                # 获取单个股票的历史数据，使用start_date
                hist_data = ak.stock_zh_a_hist(symbol=stock_code, period="daily", 
                                             start_date=start_date, end_date=trade_date,
                                             adjust="qfq")
                if hist_data is not None and not hist_data.empty:
                    # 添加股票信息
                    hist_data['股票代码'] = stock_code
                    hist_data['股票名称'] = stock_info['股票名称']
                    hist_data['所属行业'] = stock_info['所属行业']
                    all_data.append(hist_data)
                
                # 每处理100只股票显示一次进度
                if idx % 100 == 0:
                    print(f"已处理 {idx}/{total_stocks} 只股票")
                    
            except Exception as e:
                print(f"获取股票 {stock_code} 的历史数据失败: {e}")
                continue
        
        if not all_data:
            print("没有获取到任何数据")
            return None
        
        print(f"成功获取 {len(all_data)} 只股票的历史数据")
        
        # 合并所有数据
        df = pd.concat(all_data, ignore_index=True)
        
        # 重命名列
        df = df.rename(columns={
            '日期': '交易日期',
            '开盘': '开盘价',
            '收盘': '收盘价',
            '最高': '最高价',
            '最低': '最低价',
            '成交量': '成交量',
            '成交额': '成交额',
            '振幅': '振幅',
            '涨跌幅': '涨跌幅',
            '涨跌额': '涨跌额',
            '换手率': '换手率'
        })
        
        # 确保所有必要的列都存在
        required_columns = ['股票代码', '股票名称', '交易日期', '开盘价', '收盘价', '最高价', '最低价', 
                          '成交量', '成交额', '涨跌幅', '换手率', '所属行业']
        for col in required_columns:
            if col not in df.columns:
                print(f"警告: 缺少必要的列 {col}")
                if col == '所属行业':
                    df[col] = '其他'
                else:
                    return None
        
        # 数据清洗和类型转换
        df['交易日期'] = pd.to_datetime(df['交易日期'])
        numeric_columns = ['开盘价', '收盘价', '最高价', '最低价', '成交量', '成交额', '涨跌幅', '换手率']
        for col in numeric_columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # 按日期和股票代码排序
        df = df.sort_values(['股票代码', '交易日期'])
        
        # 保存完整的历史数据到缓存
        if use_cache:
            save_to_cache(df, trade_date)
        
        return df
        
    except Exception as e:
        print(f"获取股票数据失败: {e}")
        return None

def fetch_fundamental_data(trade_date, use_cache=True):
    """获取财务数据"""
    # 如果使用缓存，尝试从缓存加载
    if use_cache:
        cache_file = get_fundamental_cache_file_path(trade_date)
        if os.path.exists(cache_file):
            try:
                # 读取数据
                data = pd.read_csv(cache_file, encoding='utf-8')
                
                # 转换数据类型
                data['股票代码'] = data['股票代码'].astype(str).str.zfill(6)
                numeric_columns = ['市盈率-动态', '归母净利润增长率']
                for col in numeric_columns:
                    if col in data.columns:
                        data[col] = pd.to_numeric(data[col], errors='coerce')
                
                print(f"从缓存加载基本面数据: {cache_file}")
                return data
            except Exception as e:
                print(f"读取基本面数据缓存失败: {e}")
    
    try:
        print("正在获取市盈率数据...")
        # 获取实时市盈率和成长性数据
        df = ak.stock_zh_a_spot_em()  # 获取A股实时行情
        
        # 重命名列
        df = df.rename(columns={
            '代码': '股票代码',
            '名称': '股票名称',
            '市盈率-动态': '市盈率-动态',
            '涨跌幅': '涨跌幅'
        })
        
        # 确保股票代码为字符串类型
        df['股票代码'] = df['股票代码'].astype(str).str.zfill(6)
        
        # 计算成长性指标（使用涨跌幅的20日平均作为趋势增长率）
        df['归母净利润增长率'] = df['涨跌幅'].rolling(window=20).mean()
        
        # 数据清洗和类型转换
        df['市盈率-动态'] = pd.to_numeric(df['市盈率-动态'], errors='coerce')
        df['归母净利润增长率'] = pd.to_numeric(df['归母净利润增长率'], errors='coerce')
        
        # 只保留需要的列
        result = df[['股票代码', '市盈率-动态', '归母净利润增长率']].copy()
        
        # 填充缺失值
        result = result.fillna({
            '市盈率-动态': result['市盈率-动态'].median(),
            '归母净利润增长率': 0
        })
        
        print(f"成功获取 {len(result)} 条基本面数据")
        
        # 保存到缓存
        if use_cache:
            if not os.path.exists(CACHE_DIR):
                os.makedirs(CACHE_DIR)
            cache_file = get_fundamental_cache_file_path(trade_date)
            result.to_csv(cache_file, index=False, encoding='utf-8')
            print(f"基本面数据已缓存到: {cache_file}")
        
        return result
        
    except Exception as e:
        print(f"财务数据获取失败: {e}")
        # 返回空DataFrame但包含必要的列
        return pd.DataFrame(columns=['股票代码', '归母净利润增长率', '市盈率-动态'])