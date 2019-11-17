from configparser import SafeConfigParser
from .tuned_bitmex_websocket import BitMEXWebsocket


class WSClient:
    def __init__(self):
        self.config = SafeConfigParser()
        self.config.read("config.ini")

        self.ws = BitMEXWebsocket(
            endpoint="https://www.bitmex.com/api/v1",
            symbol="XBTUSD",
            api_key=self.config['bitmex']['apiKey'],
            api_secret=self.config['bitmex']['secret']
        )
        self.ws.get_instrument()
