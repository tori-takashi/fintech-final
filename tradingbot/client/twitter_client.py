import tweepy
from .config import Config


class TwitterClient:
    def __init__(self, config_path):
        self.config_path = config_path
        config = Config(config_path).config

        self.auth = tweepy.OAuthHandler(
            config["twitter"]["consumer_key"], config["twitter"]["consumer_secret"])
        self.auth.set_access_token(config["twitter"]["access_token"], config["twitter"][
                                   "access_token_secret"])
        self.api = tweepy.API(self.auth)
