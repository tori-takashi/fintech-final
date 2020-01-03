import requests
from client.config import Config


class LineNotification:
    def __init__(self, config_path):
        self.url = "https://notify-api.line.me/api/notify"
        self.headers = {"Authorization": "Bearer " + self.token}

        self.config = Config(config_path).config
        self.token = self.config["line_notification"]["token"]

    def notify(self, text):
        data = {"message": text}
        requests.post(self.url, data=data, headers=self.headers)
