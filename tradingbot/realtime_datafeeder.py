from realtime_datafeeder.bitmex_realtime_datafeeder import BitmexRealtimeDatafeeder
from client.db_client import DBClient

bitmex_client = DBClient("mysql", "config.ini")
bitmex_realtime_feeder = BitmexRealtimeDatafeeder(bitmex_client)
bitmex_realtime_feeder.run()
