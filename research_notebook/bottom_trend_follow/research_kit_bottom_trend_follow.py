import sys
from pathlib import Path

# fix to adjust your directory
tradingbot_dir = "../../tradingbot"
config_ini = tradingbot_dir + "/config.ini"

sys.path.append(tradingbot_dir)

from datetime import datetime, timedelta
from pprint import pprint

from sklearn import linear_model
from scipy import stats

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from client.exchange_client import ExchangeClient
from client.db_client import DBClient
from client.exchange_ws_client import WSClient

from lib.pandamex import PandaMex
from lib.time_ms import TimeMS
from lib.dataset import Dataset

from bot.bottom_trend_follower import BottomTrendFollow

from model.backtest_management import BacktestManagement
from model.backtest_transaction_log import BacktestTransactionLog
from model.backtest_summary import BacktestSummary

from technical_analysis.ad import TechnicalAnalysisAD
from technical_analysis.atr import TechnicalAnalysisATR
from technical_analysis.bollinger_band import TechnicalAnalysisBB
from technical_analysis.MACD import TechnicalAnalysisMACD
from technical_analysis.SAR import TechnicalAnalysisSAR
from technical_analysis.obv import TechnicalAnalysisOBV
from technical_analysis.roc import TechnicalAnalysisROC
from technical_analysis.rsi import TechnicalAnalysisRSI
from technical_analysis.so import TechnicalAnalysisSTOCH
from technical_analysis.williamsr import TechnicalAnalysisWilliamsR
from technical_analysis.wma import TechnicalAnalysisWMA

# option settings
pd.set_option("display.max_columns", 250)
pd.set_option("display.max_rows", 250)
import warnings
warnings.filterwarnings('ignore')
plt.rcParams['figure.figsize'] = (10.0, 20.0)

bitmex_exchange_client = ExchangeClient(
    "bitmex", Path(config_ini))
mysql_client = DBClient("mysql", Path(config_ini))
dataset_manager = Dataset(mysql_client, bitmex_exchange_client, True)
dataset_manager.update_ohlcv("bitmex",start_time=datetime.now() - timedelta(days=365), with_ta=True)

# manually added
def get_joined_params_and_summary():
    bot = BottomTrendFollow(db_client=mysql_client, exchange_client=bitmex_exchange_client, is_backtest=True)
    backtest_management = bot.trading_bot_backtest.trading_bot_backtest_db.backtest_management_table()
    backtest_summary = BacktestSummary()
    
    query_management = "SELECT * FROM " + bot.trading_bot_backtest.trading_bot_backtest_db.backtest_management_table_name + ";"
    query_summary = "SELECT * FROM backtest_summary;"
    
    backtest_management_df = mysql_client.exec_sql(query_management)
    backtest_summary_df = mysql_client.exec_sql(query_summary)
    
    merged_backtest_results_df = pd.merge(backtest_management_df, backtest_summary_df, left_on="backtest_summary_id", right_on="id")
    print("data loaded")
    return merged_backtest_results_df

def f_and_t_test(column_1, column_2):
    print("=====================================")
    # Kormogorov Smirnov tst
    print("Kormogorov Smirnov test")
    ks_statistic, ks_pvalue = stats.ks_2samp(column_1, column_2)
    print("KS     :" + str(ks_statistic))
    print("p-value:" + str(ks_pvalue))
    
    if ks_pvalue > 0.05:
        print("p > 0.05, These distribution have no difference.")
    else:
        print("p <= 0.05, These distribution have a difference")
    
    # F-test
    print("F-test")
    column_1_var = np.var(column_1, ddof=1)
    column_2_var = np.var(column_2, ddof=1)
    column_1_df = len(column_1) - 1
    column_2_df = len(column_2) - 1
    f = column_1_var / column_2_var
    one_sided_pval1 = stats.f.cdf(f, column_1_df, column_2_df)
    one_sided_pval2 = stats.f.sf(f, column_1_df, column_2_df)
    two_sided_pval = min(one_sided_pval1, one_sided_pval2) * 2
    print('F:       ', round(f, 3))
    print('p-value: ', round(two_sided_pval, 3))
    
    # F-test result and t-test
    if two_sided_pval > 0.05:
        print("p > 0.05, Equal variance")
        print("t-test for equal veriance")
        t_stat, t_stat_pval = stats.ttest_ind(column_1, column_2)
        
    else:
        print("p <= 0.05, Unqual variance")
        print("t-test for unequal variance")
        t_stat, t_stat_pval = stats.ttest_ind(column_1, column_2, equal_var=False)
              
    print("t:       ", round(t_stat, 3))
    print("p-value: ", round(t_stat_pval, 3))
              
    if t_stat_pval < 0.05:
        print("p < 0.05, The averages are different.")
    else:
        print("p > 0.05, The averages are not different.")
        
 # get data functions
def get_params_summary_log_df_by_summary_id(summary_id):
    #{FIXME} Don't use, the result is incorrect
    summary_model_obj = mysql_client.session.query(BacktestSummary).filter(BacktestSummary.id==summary_id).all()[-1]
    
    summary_df = mysql_client.model_to_dataframe([summary_model_obj]).iloc[0,:]
    params_df = mysql_client.get_row_by_backtest_summary_id("bottom_trend_follow_backtest_management", summary_id).iloc[0,:]
    transaction_log_df = mysql_client.model_to_dataframe(summary_model_obj.backtest_transaction_log)
    
    return params_df, summary_df, transaction_log_df

def generate_summary_by_summary_id(summary_id):
    params_df, summary_df, transaction_log_df = get_params_summary_log_df_by_summary_id(summary_id)
    print(params_df)
    print(summary_df)
    
def get_summary_id_by_params_set(timeframe, bottom, middle, top, close_position_on_do_nothing=True, inverse_trading=False,
                                 random_forest_leverage_adjust=False):
    c = int(close_position_on_do_nothing)
    i = int(inverse_trading)
    query = "SELECT * FROM bottom_trend_follow_backtest_management WHERE timeframe=" + str(timeframe) +\
        " and bottom_trend_tick=" + str(bottom) + " and middle_trend_tick=" + str(middle) + " and top_trend_tick=" +\
        str(top) + " and close_position_on_do_nothing=" + str(c) + " and inverse_trading=" + str(i) + ";"
    row_df = mysql_client.exec_sql(query)
    summary_id = list(row_df.backtest_summary_id)[0]
    return summary_id
    
def generate_asset_curve_by_summary_id(summary_id):
    plt.rcParams['figure.figsize'] = (20.0, 20.0)
    params_df, summary_df, transaction_log_df = get_params_summary_log_df_by_summary_id(summary_id)
    
    asset_figure = plt.figure()
    graph = asset_figure.add_subplot(111)
    graph.set_title("cumulative asset curve id:" + str(summary_df.index.values[0]) +\
                    " (bottom:" + str(params_df.bottom_trend_tick) + ", middle:" +\
        str(params_df.middle_trend_tick) + ", top:" + str(params_df.top_trend_tick) + ", timeframe:" +\
        str(params_df.timeframe))
    graph.set_xlabel("time")
    graph.set_ylabel("asset USD")
    graph.plot(transaction_log_df.close_time, transaction_log_df.current_balance)
    
def generate_asset_curve_by_summary_ids(summary_ids):
    plt.rcParams['figure.figsize'] = (20.0, 20.0)
    id_params_logs = {}
    
    for id in summary_ids:
        print("transaction log loading from summary_id:" + str(id))
        params_df, summary_df, transaction_log_df = get_params_summary_log_df_by_summary_id(id)
        id_params_logs[id] = [params_df,transaction_log_df]
        
    asset_figure = plt.figure()
    
    for id, log in id_params_logs.items():
        graph = asset_figure.add_subplot(111)
        label = "id:" + str(id) +" timeframe:" + str(log[0].timeframe) + " bottom:" + str(log[0].bottom_trend_tick) + " middle:" +\
            str(log[0].middle_trend_tick) + " top:" + str(log[0].top_trend_tick)
        graph.set_title("cumulative asset curve")
        graph.set_xlabel("time")
        graph.set_ylabel("asset USD")
        graph.plot(log[1].close_time, log[1].current_balance, label=label)
        graph.legend()

def generate_transaction_snapshot_by_summary_id(summary_id, start_time, end_time):
    picked_ohlcv_df = dataset_manager.get_ohlcv(start_time=start_time, end_time=end_time, round=False)
    ta_ema = TechnicalAnalysisMACD(picked_ohlcv_df)
    
    params_df, summary_df , transaction_log_df = get_params_summary_log_df_by_summary_id(summary_id)

    picked_transaction_log_df = transaction_log_df[(transaction_log_df.entry_time > start_time) &\
                                                  (transaction_log_df.entry_time < end_time)]
    
    win_picked = picked_transaction_log_df[transaction_log_df.profit_status == "win"]
    lose_picked = picked_transaction_log_df[transaction_log_df.profit_status == "lose"]

    entry_times = list(picked_transaction_log_df.entry_time)
    win_close_times = list(win_picked.close_time)
    lose_close_times = list(lose_picked.close_time)

    plt.rcParams['figure.figsize'] = (30.0, 10.0)
    plt.plot(picked_ohlcv_df.index, picked_ohlcv_df.close)
    plt.plot(picked_ohlcv_df.index, ta_ema.append_ema_close(int(params_df.bottom_trend_tick)*int(params_df.timeframe)))
    plt.plot(picked_ohlcv_df.index, ta_ema.append_ema_close(int(params_df.middle_trend_tick)*int(params_df.timeframe)))
    plt.plot(picked_ohlcv_df.index, ta_ema.append_ema_close(int(params_df.top_trend_tick)*int(params_df.timeframe)))
    plt.ylim(picked_ohlcv_df.close.min()-(picked_ohlcv_df.close.max() - picked_ohlcv_df.close.min())*0.05,
             picked_ohlcv_df.close.max()+(picked_ohlcv_df.close.max() - picked_ohlcv_df.close.min())*0.05)
    plt.vlines(entry_times, ymin=0, ymax=150000, color="black")
    plt.vlines(win_close_times, ymin=0, ymax=150000, color="red")
    plt.vlines(lose_close_times, ymin=0, ymax=150000, color="blue")
    plt.plot()
    
def generate_transaction_log_by_params_combination(tradingbot, timeframe_params, backtest_start_time, backtest_end_time, bottom_params, 
                                            middle_params, top_params, inverse_trading, close_position_on_do_nothing, random_forest_leverage_adjust):
    
    ohlcv_df_1min = dataset_manager.get_ohlcv(start_time=backtest_start_time, end_time=backtest_end_time)
    print("dataset size: " + str(len(ohlcv_df_1min)))
    
    calc_start_time = datetime.now()
    
    for timeframe in timeframe_params:
        print("timeframe=>" + str(timeframe))
        for bottom_trend_tick in bottom_params:
            for middle_trend_tick in middle_params:           
                for top_trend_tick in top_params:
                    if bottom_trend_tick <= middle_trend_tick or middle_trend_tick <= top_trend_tick:
                        continue
                    generate_transaction_log_by_param(tradingbot=tradingbot, timeframe_param=timeframe,backtest_start_time=backtest_start_time,
                                                      backtest_end_time=backtest_end_time,
                                                      bottom_trend_tick=bottom_trend_tick, middle_trend_tick=middle_trend_tick,
                                                      top_trend_tick=top_trend_tick,
                                                      inverse_trading=inverse_trading, close_position_on_do_nothing=close_position_on_do_nothing,
                                                      random_forest_leverage_adjust=random_forest_leverage_adjust,auto_bulk_insert=False,
                                                      ohlcv_df_1min=ohlcv_df_1min)
        tradingbot.trading_bot_backtest.bulk_insert()
    print("total processing time:" + str(datetime.now() - calc_start_time))
    
def generate_transaction_log_by_param(tradingbot, timeframe_param, backtest_start_time, backtest_end_time, bottom_trend_tick, 
                                      middle_trend_tick, top_trend_tick, inverse_trading, close_position_on_do_nothing,
                                      random_forest_leverage_adjust, auto_bulk_insert=True, random_leverage=False, ohlcv_df_1min=None):
    
    if ohlcv_df_1min is None:
        ohlcv_df_1min = dataset_manager.get_ohlcv(start_time=backtest_start_time, end_time=backtest_end_time)
        print("dataset size: " + str(len(ohlcv_df_1min)))
    
    default_params = {
        "bot_name": tradingbot.default_params["bot_name"],
        "version": "v1.0.0",
        "close_position_on_do_nothing": close_position_on_do_nothing,
        "inverse_trading": inverse_trading,
        "timeframe": int(timeframe_param),
        "random_forest_leverage_adjust": random_forest_leverage_adjust,
        "random_leverage": random_leverage
    }
    specific_params = {
        "bottom_trend_tick": int(bottom_trend_tick),
        "middle_trend_tick": int(middle_trend_tick),
        "top_trend_tick": int(top_trend_tick)
    }
                    
    tradingbot.set_params(default_params, specific_params)
            
    before_run = datetime.now()
    tradingbot.run(ohlcv_df=ohlcv_df_1min[::timeframe_param], ohlcv_start_time=backtest_start_time,
        ohlcv_end_time=backtest_end_time)
    print("bottom_trend_tick=>" + str(bottom_trend_tick) +\
          " midle_trend_tick=>" + str(middle_trend_tick) +\
          " top_trend_tick=>" + str(top_trend_tick) +\
          " time:" + str(datetime.now() - before_run))
    if auto_bulk_insert:
        tradingbot.trading_bot_backtest.bulk_insert()
    return tradingbot.trading_bot_backtest.summary_id
        
def compare_summary_by_ids(ids):
    [1579,1580]
    
    params_dataframes = []
    summary_dataframes = []
    transaction_logs = []
    
    for id in ids:
        p, s, t = get_params_summary_log_df_by_summary_id(id)
        params_dataframes.append(p)
        summary_dataframes.append(s)
        transaction_logs.append(t)
    
    params_df  = pd.DataFrame(data=params_dataframes,  index=[str(id) for id in ids])
    summary_df = pd.DataFrame(data=summary_dataframes, index=[str(id) for id in ids])
    
    pd.set_option('display.expand_frame_repr', False)
    
    print(params_df.T)
    print(summary_df.T)
    
def profit_factor_analysis(df, figure_title, timeframe_params):
    columns_picked_up = df.sort_values("profit_factor", ascending=False).loc[:,[
        "timeframe",
        "bottom_trend_tick",
        "middle_trend_tick",
        "top_trend_tick",
        "profit_factor"
    ]]
    
    bins=100
    
    fig_profit_factor_histogram = plt.figure()
    fig_profit_factor_histogram.suptitle(figure_title, fontsize=16, y=1.01)
    #fig_profit_factor_histogram.subplots_adjust(wspace=0.4, hspace=0.6)
    profit_factor_histogram_all = fig_profit_factor_histogram.add_subplot(len(timeframe_params)+1,1,1)
    profit_factor_histogram_all.hist(df.profit_factor, bins=100)
    profit_factor_histogram_all.set_title("profit factor distribution for all rows")
    profit_factor_histogram_all.set_xlabel("profit factor")
    profit_factor_histogram_all.set_ylabel("freq")
    
    for i, timeframe in enumerate(timeframe_params):
        profit_factor_histogram = fig_profit_factor_histogram.add_subplot(len(timeframe_params) + 1,1, 2 + i)
        profit_factor_histogram.hist(columns_picked_up.query("timeframe==" + str(timeframe)).profit_factor, bins=bins)
        profit_factor_histogram.set_title("profit factor distribution for timeframe=" + str(timeframe))
        profit_factor_histogram.set_xlabel("profit factor")
        profit_factor_histogram.set_ylabel("freq")
        
    plt.rcParams['figure.figsize'] = (10.0, 10.0)
    fig_profit_factor_histogram.tight_layout()
    
def visualize_timeframe_entry_profit_relation(df, figure_title, timeframe_params):
    plt.rcParams['figure.figsize'] = (10.0, 10.0)
    title = "timeframe entry and profit total profit"
    
    figure_timeframe_entry_profit = plt.figure()
    figure_timeframe_entry_profit.suptitle(figure_title, fontsize=16, y=1.01)
    graph1 = figure_timeframe_entry_profit.add_subplot(1,1,1)
    graph1.set_title(title)
    graph1.set_xlabel("total_entry")
    graph1.set_ylabel("total return")

    for t in timeframe_params:
        graph1.scatter(df[df.timeframe == t].total_entry,
                       df[df.timeframe == t].total_return,
                   alpha=0.5,linewidths="1", label="timeframe:" + str(t))
        graph1.legend()
    
    figure_timeframe_entry_profit.tight_layout()
    
def find_best_ranking_parameter(sorted_df_in_need_with_timeframe, tick_params,
                                bottom_trend_tick=None, middle_trend_tick=None, verbose=False):
    optimal_tick = 0
    max_tick_ranking = 0
    
    # tick optimize detection
    if bottom_trend_tick is None and middle_trend_tick is None:
        base_query = "bottom_trend_tick == "        
                
    elif bottom_trend_tick is not None and middle_trend_tick is None:
        base_query = "bottom_trend_tick == " + str(bottom_trend_tick) + " and middle_trend_tick == "
            
    elif bottom_trend_tick is not None and middle_trend_tick is not None:
        base_query = "bottom_trend_tick == " + str(bottom_trend_tick) + " and middle_trend_tick ==" +\
                    str(middle_trend_tick) + " and top_trend_tick == "
        
    return get_max_ranking_tick(sorted_df_in_need_with_timeframe, base_query, tick_params, verbose=verbose)

def get_max_ranking_tick(sorted_df_in_need_with_timeframe, base_query, tick_params, verbose=False):
    max_tick_ranking = 0
    optimal_tick = 0
    
    for tick in tick_params:
        df = sorted_df_in_need_with_timeframe.query(base_query + str(tick))
                    
        denominator = len(df)
        numerator = df.index.values.sum()
            
        average_ranking = numerator/denominator
        if verbose is True:
            print("denominator => " + str(denominator) + " numerator => " + str(numerator) + " tick => " + str(tick) +\
              " average ranking => " + str(average_ranking))
            
        if average_ranking < max_tick_ranking or max_tick_ranking == 0:
            max_tick_ranking = average_ranking
            optimal_tick = tick
            
    return optimal_tick

def find_optimal_parameters_by_ranking(df,timeframe_params, bottom_trend_tick_params, middle_trend_tick_params, top_trend_tick_params, verbose=False):
    sorted_df_in_need = df[[
        "timeframe",
        "bottom_trend_tick",
        "middle_trend_tick",
        "top_trend_tick",
        "profit_factor"]
    ].sort_values("profit_factor", ascending=False)
    
    for timeframe in timeframe_params:
        print("calc optimal parameters for timeframe:" + str(timeframe))
        sorted_df_in_need_with_timeframe = sorted_df_in_need.query("timeframe ==" + str(timeframe))
        if verbose:
            print("bottom")
        optimal_bottom = find_best_ranking_parameter(sorted_df_in_need_with_timeframe,
            bottom_trend_tick_params, verbose=verbose)
        if verbose:
            print("middle with bottom => " + str(optimal_bottom) )
        optimal_middle = find_best_ranking_parameter(sorted_df_in_need_with_timeframe,
            middle_trend_tick_params, bottom_trend_tick=optimal_bottom, verbose=verbose)
        if verbose:
            print("top with bottom => " + str(optimal_bottom) + " middle => " + str(optimal_middle))
        optimal_top = find_best_ranking_parameter(sorted_df_in_need_with_timeframe,
            top_trend_tick_params, bottom_trend_tick=optimal_bottom, middle_trend_tick=optimal_middle, verbose=verbose)
        
        print("optimal bottom => " + str(optimal_bottom) + " middle => " +\
              str(optimal_middle) + "top => " + str(optimal_top))