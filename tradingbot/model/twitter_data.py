from sqlalchemy import Column, Integer, Float, DateTime, String, Boolean
from sqlalchemy.ext.declarative import declarative_base


class TwitterData(declarative_base()):
    __tablename__ = "twitter_data"

    id = Column(Integer, primary_key=True)

    created_at = Column(DateTime)
    tweet_id = Column(String(40))
    text = Column(String(500))
    truncated = Column(Boolean)
    source = Column(String(200))
    retweet_count = Column(Integer)
    favorite_count = Column(Integer)
    language = Column(String(20))

    # entities
    hash_tags = Column(String(200))
    tweet_urls = Column(String(300))

    # metadata
    iso_language_code = Column(String(20))

    # user
    user_created_at = Column(DateTime)
    user_description = Column(String(300))

    user_profile_url = Column(String(300))
    user_followers_count = Column(Integer)
    user_following_count = Column(Integer)
    user_id = Column(String(40))
    user_name = Column(String(140))
    user_screen_name = Column(String(30))
    user_tweets = Column(Integer)
    user_profile_url = Column(String(300))
    user_verified = Column(Boolean)

    is_junk = Column(Boolean)

    vader_negative = Column(Float)
    vader_neutral = Column(Float)
    vader_positive = Column(Float)
    vader_compound = Column(Float)

    def __init__(self):
        self.id = TwitterData.id

        self.created_at = TwitterData.created_at
        self.tweet_id = TwitterData.tweet_id
        self.text = TwitterData.text
        self.truncated = TwitterData.truncated
        self.source = TwitterData.source
        self.retweet_count = TwitterData.retweet_count
        self.favorite_count = TwitterData.favorite_count
        self.language = TwitterData.language

        self.is_junk = TwitterData.is_junk

        # entities
        self.hash_tags = TwitterData.hash_tags
        self.tweet_urls = TwitterData.tweet_urls

        # metadata
        self.iso_language_code = TwitterData.iso_language_code

        # user
        self.user_created_at = TwitterData.user_created_at
        self.user_description = TwitterData.user_description

        self.user_profile_url = TwitterData.user_profile_url
        self.user_followers_count = TwitterData.user_followers_count
        self.user_following_count = TwitterData.user_following_count
        self.user_id = TwitterData.user_id
        self.user_name = TwitterData.user_name
        self.user_screen_name = TwitterData.user_screen_name
        self.user_tweets = TwitterData.user_tweets
        self.user_profile_url = TwitterData.user_profile_url
        self.user_verified = TwitterData.user_verified

        self.vader_negative = TwitterData.vader_negative
        self.vader_neutral = TwitterData.vader_neutral
        self.vader_positive = TwitterData.vader_positive
        self.vader_compound = TwitterData.vader_compound
