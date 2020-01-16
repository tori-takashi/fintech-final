from datetime import datetime, timedelta

from client.twitter_client import TwitterClient
from client.db_client import DBClient
from lib.twitter_dataset import TwitterDataset

twitter_client = TwitterClient("config.ini")
db_client = DBClient("mysql", "config.ini")
twitter_dataset = TwitterDataset(twitter_client, db_client)

since = datetime.now() - timedelta(days=7)  # utc
until = datetime.now()  # utc

twitter_dataset.insert_tweet("btc", since=since, until=until)
all_tweet = twitter_dataset.search_downloaded_tweet()
print(all_tweet[all_tweet.is_junk == 1].text)
