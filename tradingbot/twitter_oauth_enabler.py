from requests_oauthlib import OAuth1Session, OAuth1
from urllib.parse import parse_qsl
import tweepy
import requests
import six
from six.moves.urllib.parse import parse_qs


def oauth_enabler(consumer_key, consumer_secret, callback=None):
    oauth_callback = callback
    request_token_url = "https://api.twitter.com/oauth/request_token"

    twitter = OAuth1Session(consumer_key, consumer_secret)

    response = twitter.post(
        request_token_url,
        params={'oauth_callback': oauth_callback}
    )

    request_token = dict(parse_qsl(response.content.decode("utf-8")))
    print(response)

    authenticate_url = "https://api.twitter.com/oauth/authenticate"
    authenticate_endpoint = '%s?oauth_token=%s' \
        % (authenticate_url, request_token['oauth_token'])

    print(authenticate_endpoint)


def oauth_enabler_v2(consumer_key, consumer_secret):
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    ret = auth.get_xauth_access_token('tori_toutosh1', 'Enn.3.14')
    print(ret)


def oauth_enabler_v3(consumer_key, consumer_secret, username, password):
    url = "https://api.twitter.com/oauth/request_token"
    oauth = OAuth1(consumer_key,
                   client_secret=consumer_secret)

    r = requests.post(url=url,
                      auth=oauth,
                      headers={'x_auth_mode': 'client_auth',
                               'x_auth_username': username,
                               'x_auth_password': password})
    print(r.text)

    credentials = parse_qs(r.content)
    return credentials.get('oauth_token')[0], credentials.get('oauth_token_secret')[0]


twitterdeck_consumer_key = "yT577ApRtZw51q4NPMPPOQ"
twitterdeck_consumer_secret = "3neq3XqN5fO3obqwZoajavGFCUrC42ZfbrLXy5sCv8"
twitterdeck_callback = "http://www.tweetdeck.com/"

iphone_consumer_key = "IQKbtAYlXLripLGPWd0HUA"
iphone_consumer_secret = "GgDYlkSvaPxGxC4X8liwpUoqKwwr3lCADbz8A7ADU"

android_consumer_key = "3nVuSoBZnx6U4vzUxf5w"
android_consumer_secret = "Bcs59EFbbsdF6Sl9Ng71smgStWEGwXXKSjYvPVt7qys"

# oauth_enabler_v3(iphone_consumer_key,
#                 iphone_consumer_secret, "tori_toutosh1", "Enn.3.14")

# oauth_enabler("7E5aBy6hKju70U5nJ2B15mhgh",
#              "lwW0GPM1n3wV4G5wrYlax3mmmDCmVUjhX7tXicL6riuAt9U3Sh")

oauth_enabler(iphone_consumer_key, iphone_consumer_secret,
              "twittersdk://")
