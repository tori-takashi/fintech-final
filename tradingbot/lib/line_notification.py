import requests
from client.config import Config


class LineNotification:
    def __init__(self, config_path):
        self.config = Config(config_path).config
        self.token = self.config["line_notification"]["token"]

        self.url = "https://notify-api.line.me/api/notify"
        self.headers = {"Authorization": "Bearer " + self.token}

    def notify(self, text, print_console=True):
        if print_console:
            print(text)
        data = {"message": text}
        requests.post(self.url, data=data, headers=self.headers)
