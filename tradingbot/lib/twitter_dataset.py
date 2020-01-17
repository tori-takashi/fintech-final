import pandas as pd
from datetime import datetime, timedelta
from pytz import timezone

from time import sleep

from alembic import op
import sqlalchemy

from .sentiment_analysis import SentimentAnalysis

from model.twitter_data import TwitterData


class TwitterDataset():
    def __init__(self, twitter_client, db_client):
        self.api = twitter_client.api
        self.db_client = db_client
        self.sentiment_analysis = SentimentAnalysis()
        if not self.db_client.is_table_exist("twitter_data"):
            self.build_twitter_data_table()

    def build_twitter_data_table(self):
        TwitterData.__table__.create(bind=self.db_client.connector)
        self.db_client.connector.execute(sqlalchemy.sql.text(
            'alter table twitter_data default character set utf8mb4'))

    def insert_tweet(self, query, no_rt=True, since=None, until=None):
        search_results = self.tweet_downloader(
            query, no_rt, since, until)
        self.db_client.session.bulk_insert_mappings(
            TwitterData, search_results)
        self.db_client.session.commit()

    def search_tweet(self, query, no_rt=True, since=None, until=None):
        search_results = self.tweet_downloader(
            query, no_rt, since, until)
        return self.convert_to_df(search_results)

    def tweet_downloader(self, query, no_rt, since, until):
        since = since.astimezone(timezone('utc'))
        until = until.astimezone(timezone('utc'))

        keyword = query

        search_results = []
        current_max_id = None
        oldest_data_time = until

        ratelimit_counter = 0
        ratelimit_start_time = datetime.now()

        while since < oldest_data_time:

            # control rate limit
            if ratelimit_counter == 180:
                sleep(datetime.now() - ratelimit_start_time)
                sleep(10)
                ratelimit_counter = 0
                ratelimit_start_time = datetime.now()

            query = ""
            query += keyword
            query += " -rt" if no_rt is True else ""

            search_results_onetime = self.api.search(
                query, count=100, result_type="mixed", tweet_mode='extended', max_id=current_max_id)
            search_results.extend([self.search_result_to_dict(
                search_result) for search_result in search_results_onetime])

            oldest_data_time = pd.to_datetime(
                search_results[-1]["created_at"]).to_pydatetime().astimezone(timezone('utc'))
            current_max_id = search_results[-1]["tweet_id"]

            print("current oldest dowloaded data is " + str(oldest_data_time))

        return search_results

    def convert_to_df(self, search_results):
        # in need colunms
        return pd.DataFrame(search_results)

    def since_until_settings(self, since=None, until=None):
        concat_query = ""

        if since:
            since_year = since.year
            since_month = since.month
            since_day = since.day
            since_hour = since.hour
            since_min = since.minute
            since_second = since.second
            concat_query += " since:" + \
                str(since_year) + "-" + str(since_month) + \
                "-" + str(since_day) + "_UTC_" + str(since_hour) + \
                ":" + str(since_min) + ":" + str(since_second) + " "

        if until:
            until_year = until.year
            until_month = until.month
            until_day = until.day
            until_hour = until.hour
            until_min = until.minute
            until_second = until.second
            concat_query += " until:" + \
                str(until_year) + "-" + str(until_month) + \
                "-" + str(until_day) + "_UTC_" + str(until_hour) + \
                ":" + str(until_min) + ":" + str(until_second) + " "

        return concat_query

    def search_result_to_dict(self, search_result):
        json = search_result._json

        search_result = {}

        search_result["created_at"] = pd.to_datetime(
            json["created_at"]).to_pydatetime().astimezone(timezone('utc'))
        search_result["tweet_id"] = str(json["id"])
        search_result["text"] = json["text"].lower()
        search_result.update(self.parse_entities(json["entities"]))
        search_result["truncated"] = json["truncated"]
        search_result.update(self.parse_metadata(json["metadata"]))
        search_result["source"] = json["source"]
        search_result.update(self.parse_user(json["user"]))
        search_result["retweet_count"] = json["retweet_count"]
        search_result["favorite_count"] = json["favorite_count"]
        search_result["language"] = json["lang"]

        search_result["is_junk"] = self.junk_classifier(
            search_result["text"], search_result["user_description"])

        # sentiment analysis
        search_result.update(self.parse_vader(search_result["text"]))

        return search_result

    def parse_entities(self, entities):
        hash_tag_list = [text_index["text"]
                         for text_index in entities["hashtags"]]
        hash_tags = " ".join(hash_tag_list)

        tweet_url_list = [url_dict["expanded_url"]
                          for url_dict in entities["urls"]]
        tweet_urls = " ".join(tweet_url_list)

        return {"hash_tags": hash_tags, "tweet_urls": tweet_urls}

    def parse_metadata(self, metadata):
        metadata_dict = {}
        metadata_dict["iso_language_code"] = metadata["iso_language_code"]
        return metadata_dict

    def parse_user(self, user):
        user_dict = {}

        user_dict["user_created_at"] = pd.to_datetime(user["created_at"]).to_pydatetime(
        ).astimezone(timezone('utc'))
        user_dict["user_description"] = user["description"].lower()

        try:
            user_dict["user_profile_url"] = user["entities"]["url"]["urls"][0]["expanded_url"]
        except:
            user_dict["user_profile_url"] = None

        user_dict["user_followers_count"] = user["followers_count"]
        user_dict["user_following_count"] = user["friends_count"]
        user_dict["user_id_str"] = user["id"]
        user_dict["user_name"] = user["name"]
        user_dict["user_screen_name"] = user["screen_name"]
        user_dict["user_tweets"] = user["statuses_count"]
        user_dict["user_profile_url"] = user["url"]
        user_dict["user_verified"] = user["verified"]

        return user_dict

    def parse_vader(self, text):
        vader_dict = {}
        vader_result = self.sentiment_analysis.calc_vader_scores(text)
        vader_dict["vader_negative"] = vader_result["neg"]
        vader_dict["vader_neutral"] = vader_result["neu"]
        vader_dict["vader_positive"] = vader_result["pos"]
        vader_dict["vader_compound"] = vader_result["compound"]

        return vader_dict

    def junk_classifier(self, text, user_description):
        if "bit.ly" in text:
            return True

        if "free" in text:
            return True

        return False

    def search_downloaded_tweet(self):
        return self.db_client.exec_sql("SELECT * FROM twitter_data")
