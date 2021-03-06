from datetime import datetime, timedelta

from bot.bottom_trend_follower import BottomTrendFollow

from client.db_client import DBClient
from client.exchange_client import ExchangeClient

bitmex_client = ExchangeClient("bitmex", "config.ini")
influx_client = DBClient("influxdb", "config.ini")

bot_name = "bottom_trend_follow"
version = "v1.0.0"
timeframe = 1
bottom_trend_tick = 5
middle_trend_tick = 3
top_trend_tick = 1
close_position_on_do_nothing = True
inverse_trading = True
random_leverage = False
random_forest_leverage_adjust = False

default_params = {
    "bot_name": bot_name,
    "version": version,
    "timeframe": timeframe,
    "close_position_on_do_nothing": close_position_on_do_nothing,
    "inverse_trading": inverse_trading,
    "random_leverage": random_leverage,
    "random_forest_leverage_adjust": random_forest_leverage_adjust
}

specific_params = {
    "bottom_trend_tick": bottom_trend_tick,
    "middle_trend_tick": middle_trend_tick,
    "top_trend_tick": top_trend_tick
}

bottom_trend_follow = BottomTrendFollow(
    bitmex_client, influx_client, default_params=default_params, specific_params=specific_params, is_backtest=False)
bottom_trend_follow.run(
    ohlcv_start_time=datetime.now() - timedelta(days=6))
