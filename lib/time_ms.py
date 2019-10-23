from datetime import datetime
import calendar


class TimeMS:
    def now_ms(self):
        now = datetime.utcnow()  # now UTC
        unixTime_ms = calendar.timegm(now.utctimetuple())*1000  # Unix time
        # get unix time and convert to milliseconds
        return unixTime_ms

    def fromtimestamp_ms(self, ms):
        return datetime.fromtimestamp(ms/1000)
