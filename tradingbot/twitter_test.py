from datetime import datetime, timedelta

from client.twitter_client import TwitterClient
from lib.twitter_dataset import TwitterDataset

twitter_client = TwitterClient("config.ini")
twitter_dataset = TwitterDataset(twitter_client)

since = datetime.now() - timedelta(days=14)  # utc
until = datetime.now()  # utc

tweet_data = twitter_dataset.search_tweet(
    "bitcoin btc", since_ymd_datetime=since, until_ymd_datetime=until)

tweet_data.to_csv("test.csv")
