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
top_trend_tick = 2
close_position_on_do_nothing = True
inverse_trading = False

default_params = {
    "bot_name": bot_name,
    "version": version,
    "timeframe": timeframe,
    "close_position_on_do_nothing": close_position_on_do_nothing,
    "inverse_trading": inverse_trading
}

specific_params = {
    "bottom_trend_tick": bottom_trend_tick,
    "middle_trend_tick": middle_trend_tick,
    "top_trend_tick": top_trend_tick
}

bottom_trend_follow = BottomTrendFollow(
    bitmex_client, influx_client, default_params=default_params, specific_params=specific_params, is_backtest=False)
bottom_trend_follow.set_bot_identity_for_real(
    "bottom_trend_follow_ver1_1_5_3_1_1_0")
bottom_trend_follow.run(
    ohlcv_start_time=datetime.now() - timedelta(minutes=4))