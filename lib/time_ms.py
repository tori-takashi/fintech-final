from datetime import datetime
import calendar


class TimeMS:
    @classmethod
    def fromtimestamp(self, ms):
        return datetime.fromtimestamp(ms/1000)
