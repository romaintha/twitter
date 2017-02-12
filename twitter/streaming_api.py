import logging
import time

import tweepy

from twitter import settings


class Streaming:

    def __init__(self,
                 pipeline,
                 batch_size=1000,
                 consumer_key=settings.CONSUMER_TOKEN,
                 consumer_secret=settings.CONSUMER_SECRET,
                 acces_token=settings.ACCESS_TOKEN,
                 access_secret=settings.ACCESS_SECRET,):
        self.auth = tweepy.OAuthHandler(consumer_key=consumer_key, consumer_secret=consumer_secret)
        self.auth.set_access_token(acces_token, access_secret)
        self.stream = tweepy.Stream(auth=self.auth, listener=Listener(pipeline, batch_size=batch_size))
        logging.basicConfig(filename='log_twitter.txt', level=logging.DEBUG)

    def start_streaming(self,to_track=settings.TO_TRACK):
        while True:
            try:
                self.stream.filter(track=to_track)
            except Exception as e:
                logging.exception('stream filter')
                time.sleep(3)


class Listener(tweepy.StreamListener):

    def __init__(self, pipeline, batch_size):
        super(Listener, self).__init__()
        self.pipeline = pipeline
        self.tweets = list()
        self.batch_size = batch_size

    def on_status(self, status):
        if not self.tweet_filter(status):
            return
        self.tweets.append(status)
        if len(self.tweets) >= self.batch_size:
            data = self.pipeline(self.tweets)
            self.tweets = list()

    def on_error(self, status_code):
        logging.debug('error: %s', status_code)
        if status_code == 420:
            time.time(61*15)

    def on_timeout(self):
        logging.debug('timeout')

    def on_limit(self, track):
        logging.debug('limit: %s', track)

    @staticmethod
    def tweet_filter(status):
        if getattr(status, 'lang') != 'fr':
            return False
        return True
