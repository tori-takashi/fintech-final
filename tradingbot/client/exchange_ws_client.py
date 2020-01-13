from .tuned_bitmex_websocket import BitMEXWebsocket
from .config import Config


class WSClient:
    def __init__(self, config_path):
        self.config = Config(config_path).config

        self.ws = BitMEXWebsocket(
            endpoint="https://www.bitmex.com/api/v1",
            symbol="XBTUSD",
            api_key=self.config['bitmex']['apiKey'],
            api_secret=self.config['bitmex']['secret']
        )
        self.ws.get_instrument()
