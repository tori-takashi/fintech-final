import pandas as pd
from datetime import datetime
from pytz import timezone


class TwitterDataset:
    def __init__(self, twitter_client):
        self.api = twitter_client.api

    def search_tweet(self, query, no_rt=True, since_ymd_datetime=None, until_ymd_datetime=None):
        search_results = self.tweet_downloader(
            query, no_rt, since_ymd_datetime, until_ymd_datetime)
        return self.convert_to_df(search_results)

    def tweet_downloader(self, query, no_rt, since_ymd_datetime, until_ymd_datetime):
        since_ymd_datetime = since_ymd_datetime.astimezone(timezone('utc'))
        until_ymd_datetime = until_ymd_datetime.astimezone(timezone('utc'))

        keyword = query

        print(since_ymd_datetime)

        search_results = []
        oldest_data_time = until_ymd_datetime

        while since_ymd_datetime < oldest_data_time:
            query = ""
            query += keyword
            query += self.since_until_settings(None, oldest_data_time)
            query += " -rt" if no_rt is True else ""
            print(query)

            search_results_onetime = self.api.search(
                query, count=100, result_type="mixed")
            search_results.extend([self.search_result_to_dict(
                search_result) for search_result in search_results_onetime])

            oldest_data_time = pd.to_datetime(
                search_results[-1]["created_at"]).to_pydatetime().astimezone(timezone('utc'))

        return search_results

    def convert_to_df(self, search_results):
        # in need colunms
        return pd.DataFrame(search_results)

    def since_until_settings(self, since_ymd_datetime=None, until_ymd_datetime=None):
        concat_query = ""

        if since_ymd_datetime:
            since_year = since_ymd_datetime.year
            since_month = since_ymd_datetime.month
            since_day = since_ymd_datetime.day
            since_hour = since_ymd_datetime.hour
            since_min = since_ymd_datetime.minute
            since_second = since_ymd_datetime.second
            concat_query += " since:" + \
                str(since_year) + "-" + str(since_month) + \
                "-" + str(since_day) + "_UTC_" + str(since_hour) + \
                ":" + str(since_min) + ":" + str(since_second) + " "

        if until_ymd_datetime:
            until_year = until_ymd_datetime.year
            until_month = until_ymd_datetime.month
            until_day = until_ymd_datetime.day
            until_hour = until_ymd_datetime.hour
            until_min = until_ymd_datetime.minute
            until_second = until_ymd_datetime.second
            concat_query += " until:" + \
                str(until_year) + "-" + str(until_month) + \
                "-" + str(until_day) + "_UTC_" + str(until_hour) + \
                ":" + str(until_min) + ":" + str(until_second) + " "

        return concat_query

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
        user_dict["user_name"] = user["name"]
        user_dict["user_screen_name"] = user["screen_name"]
        user_dict["user_tweets"] = user["statuses_count"]
        user_dict["user_profile_url"] = user["url"]
        user_dict["user_verified"] = user["verified"]

        return user_dict
