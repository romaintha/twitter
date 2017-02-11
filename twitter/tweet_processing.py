import datetime
import logging
from tweepy import Status

from twitter.models import Tweet, User

logger = logging.getLogger(__name__)


class TweetProcessing:

    DATETIME_FORMAT = '%Y-%m-%d_%H:%M'

    def __init__(self, status=None):
        if status:
            if not isinstance(status, Status):
                raise Exception('tweet must be an instance of Status from Tweepy.')
            self.status = status
            self.author = status.author

    def prepare_tweet_attributes(self):
        # the date needs to be formated as a string to be serialized.
        if hasattr(self.status, 'coordinates') and self.status.coordinates and 'coordinates' in self.status.coordinates:
            coordinates = self.status.coordinates['coordinates']
        else:
            coordinates = None
        return {
            'created_at': self.status.created_at.strftime(self.DATETIME_FORMAT),
            'coordinates': coordinates,
            'id_str': self.status.id_str,
            'lang': self.status.lang if hasattr(self.status, 'lang') else None,
            'retweeted': self.status.retweeted if hasattr(self.status, 'retweeted') else None,
            'text': self.status.text.lower(),
        }

    def prepare_user_attributes(self):
        # the date needs to be formated as a string to be serialized.
        return {
            'created_at': self.author.created_at.strftime(self.DATETIME_FORMAT),
            'description': self.author.description if hasattr(self.author, 'description') else None,
            'followers_count': self.author.followers_count,
            'friends_count': self.author.friends_count,
            'modified': datetime.datetime.now().strftime(self.DATETIME_FORMAT),
            'location': self.author.location if hasattr(self.author, 'location') else None,
            'id_str': self.author.id_str,
            'name': self.author.name,
            'screen_name': self.author.screen_name,
            'time_zone': self.author.time_zone if hasattr(self.author, 'time_zone') else None,
            'url': self.author.url if hasattr(self.author, 'url') else None,
            'lang': self.author.lang if hasattr(self.author, 'lang') else None,
        }

    def prepare_entities(self):
        return self.status.entities

    @staticmethod
    def prepare_batch_processing(tweets):
        users_attributes = [TweetProcessing(status=tweet).prepare_user_attributes() for tweet in tweets]
        tweets_attributes = [TweetProcessing(status=tweet).prepare_tweet_attributes() for tweet in tweets]
        return users_attributes, tweets_attributes

    @classmethod
    def batch_processing(cls, users_attributes, tweets_attributes):
        [u_attr.update(
            {'created_at': datetime.datetime.strptime(u_attr['created_at'], cls.DATETIME_FORMAT),
             'modified': datetime.datetime.strptime(u_attr['modified'], cls.DATETIME_FORMAT)}
        ) for u_attr in users_attributes]
        users = User.create_or_update(*users_attributes)
        [t_attr.update(
            {'created_at': datetime.datetime.strptime(t_attr['created_at'], cls.DATETIME_FORMAT),
             "coordinates": t_attr.get("coordinates") if t_attr.get("coordinates") else getattr(users[k], "coordinates", [])}
        ) for k, t_attr in enumerate(tweets_attributes)]

        tweets = Tweet.create_or_update(*tweets_attributes)
        for k, tweet in enumerate(tweets):
            users[k].posts.connect(tweet)
