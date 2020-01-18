from realtime_datafeeder.bitmex_realtime_datafeeder import BitmexRealtimeDatafeeder

bitmex_realtime_feeder = BitmexRealtimeDatafeeder("config.ini", True)
bitmex_realtime_feeder.run()
