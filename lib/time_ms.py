from datetime import datetime
import calendar


class TimeMS:
    @classmethod
    def now(self):
        now = datetime.utcnow()  # now UTC
        unixtime_ms = calendar.timegm(now.utctimetuple())*1000  # Unix time
        # get unix time and convert to milliseconds
        return unixtime_ms

    @classmethod
    def to_unixtime(self, datetime_val):
        unixtime_ms = calendar.timegm(
            datetime_val.utctimetuple()) * 1000  # unix time
        return unixtime_ms

    @classmethod
    def fromtimestamp(self, ms):
        return datetime.fromtimestamp(ms/1000)
