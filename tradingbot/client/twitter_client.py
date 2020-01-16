import pandas as pd
from pprint import pprint

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

    def show_public_tweets(self):
        public_tweets = self.api.home_timeline()
        for tweet in public_tweets:
            print(tweet.text)

    def search_tweet(self, query, no_rt=True, since_ymd_datetime=None, until_ymd_datetime=None):
        query += self.since_until_settings(since_ymd_datetime,
                                           until_ymd_datetime)
        query += " -rt" if no_rt is True else ""

        print(query)

        search_results = self.api.search(query, count=100, result_type="mixed")
        return self.convert_to_df(search_results)

    def since_until_settings(self, since, until):
        concat_query = ""

        if since:
            since_year = since.year
            since_month = since.month
            since_day = since.day
            concat_query += " since:" + \
                str(since_year) + "-" + str(since_month) + \
                "-" + str(since_day) + " "

        if until:
            until_year = until.year
            until_month = until.month
            until_day = until.day
            concat_query += "until:" + \
                str(until_year) + "-" + str(until_month) + \
                "-" + str(until_day) + " "

        return concat_query

    def convert_to_df(self, search_results):
        # in need colunms
        search_results_list = [self.search_result_to_dict(
            search_result) for search_result in search_results]
        return pd.DataFrame(search_results_list)

    def search_result_to_dict(self, search_result):
        json = search_result._json

        search_result = {}

        search_result["created_at"] = json["created_at"]
        search_result["tweet_id"] = json["id"]
        search_result["text"] = json["text"]
        search_result.update(self.parse_entities(json["entities"]))
        search_result["truncated"] = json["truncated"]
        search_result.update(self.parse_metadata(json["metadata"]))
        search_result["source"] = json["source"]
        search_result.update(self.parse_user(json["user"]))
        search_result["retweet_count"] = json["retweet_count"]
        search_result["favorite_count"] = json["favorite_count"]
        search_result["language"] = json["lang"]

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

        user_dict["user_created_at"] = user["created_at"]
        user_dict["user_description"] = user["description"]

        try:
            user_dict["user_profile_url"] = user["entities"]["url"]["urls"][0]["expanded_url"]
        except:
            user_dict["user_profile_url"] = None

        user_dict["user_followers_count"] = user["followers_count"]
        user_dict["user_following_count"] = user["friends_count"]
        user_dict["user_id"] = user["id"]
        user_dict["user_location"] = user["location"]
        user_dict["user_name"] = user["name"]
        user_dict["user_screen_name"] = user["screen_name"]
        user_dict["user_tweets"] = user["statuses_count"]
        user_dict["user_profile_url"] = user["url"]
        user_dict["user_verified"] = user["verified"]

        return user_dict
