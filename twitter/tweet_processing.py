import re
import datetime
import logging
from nltk.tokenize import WordPunctTokenizer
from nltk.stem.snowball import FrenchStemmer
from nltk.corpus import stopwords
from sklearn.externals import joblib
from tweepy import Status

from twitter.models import Tweet, User, Hashtag, Link
from twitter.settings import TO_TRACK, CLASSIFIER_PATH

logger = logging.getLogger(__name__)


class TweetProcessing:

    DATETIME_FORMAT = '%Y-%m-%d_%H:%M'

    def __init__(self, status=None, tweet=None, classifier_path=CLASSIFIER_PATH):
        if status:
            if not isinstance(status, Status):
                raise Exception('tweet must be an instance of Status from Tweepy.')
            self.status = status
            self.author = status.author
            self.entities = status.entities

        if tweet and not isinstance(tweet, Tweet):
            raise Exception('tweet must be an instance of Tweet model.')
        else:
            self.tweet = tweet
        self.classifier_path = classifier_path

    def prepare_related_data(self):
        return {
        'tweet_id': self.status.id_str,
        'retweeted_id': self.status.retweeted_status.id_str if hasattr(self.status, 'retweeted_status') else '',
        'mentions_id': [str(mention['id']) for mention in self.status.entities['user_mentions']],
        'replies_id': self.status.in_reply_to_status_id if hasattr(self.status, 'in_reply_to_status_id') else '',
        'quotes_id': self.status.quoted_status_id if hasattr(self.status, 'quoted_status_id') else '',
    }

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

    def assess_tweet(self):
        tweet_keys = ('created_at', 'id_str', 'retweeted', 'text')
        for key in tweet_keys:
            if not hasattr(self.status, key):
                return False
        user_keys = ('created_at', 'id_str', 'name', 'screen_name')
        for key in user_keys:
            if not hasattr(self.status.author, key):
                return False
        return True

    @classmethod
    def parse_tweet(cls, tweet_attributes, user_attributes, related_data, entities, classifier_path=CLASSIFIER_PATH):
        tweet_attributes['created_at'] = datetime.datetime.strptime(tweet_attributes['created_at'], cls.DATETIME_FORMAT)
        user_attributes['created_at'] = datetime.datetime.strptime(user_attributes['created_at'], cls.DATETIME_FORMAT)
        user_attributes['modified'] = datetime.datetime.strptime(user_attributes['modified'], cls.DATETIME_FORMAT)
        # Create or get the unique User instance (get_or_create returns a list -> [0])
        user = User.get_or_create({'id_str': user_attributes['id_str']})[0]
        for key, value in user_attributes.items():
            setattr(user, key, value)
        user.save()
        # Check whether the user has been already geolocated. If yes pass the geolocation to the tweet if needed
        user_is_geolocated = user and hasattr(user, 'coordinates') and user.coordinates
        tweet_not_geolocated = not tweet_attributes['coordinates']
        if user_is_geolocated and tweet_not_geolocated:
            tweet_attributes['coordinates'] = user.coordinates
        # Create or get the unique Tweet instance (get_or_create returns a list -> [0])
        tweet = Tweet.get_or_create({'id_str': tweet_attributes['id_str']})[0]
        for key, value in tweet_attributes.items():
            setattr(tweet, key, value)
        # Save retweet, mentions and quote data
        tweet.retweet_id_str = related_data['retweeted_id']
        tweet.mention_ids_str = related_data['mentions_id']
        tweet.quote_id_str = related_data['quotes_id']
        tweet.reply_id_str = related_data['replies_id']
        # Create tweet feature
        # processor = cls(tweet=tweet, classifier_path=classifier_path)
        # tweet.features = processor.get_tweet_features()
        # Analysis sentiment
        # tweet.sentiment = processor.analyze_sentiment()
        # tweet.is_sentiment_analyzed = True
        #
        tweet.sentiment = 'neg'
        tweet.is_sentiment_analyzed = True
        tweet.save()
        # create the Posts relationship between user and tweet instances
        user.posts.connect(tweet)
        # Create all the necessary Hashtag instances
        # for hashtag_attributes in entities['hashtags']:
        #     hashtag = Hashtag.get_or_create({'text': hashtag_attributes['text'].lower()})[0]
        #     tweet.tags.connect(hashtag)
        # # Create all the necessary Link instances
        # for link_attributes in entities['urls']:
        #     link = Link.get_or_create({'url': link_attributes['url']})[0]
        #     tweet.contains.connect(link)
        return tweet

    @staticmethod
    def prepare_batch_processing(tweets):
        entities = [TweetProcessing(status=tweet).prepare_entities() for tweet in tweets]
        data = [TweetProcessing(status=tweet).prepare_related_data() for tweet in tweets]
        users_attributes = [TweetProcessing(status=tweet).prepare_user_attributes() for tweet in tweets]
        tweets_attributes = [TweetProcessing(status=tweet).prepare_tweet_attributes() for tweet in tweets]
        return users_attributes, tweets_attributes, entities, data

    @classmethod
    def batch_processing(cls, users_attributes, tweets_attributes, entities, data, analysis_to_perform=[]):
        [u_attr.update(
            {'created_at': datetime.datetime.strptime(u_attr['created_at'], cls.DATETIME_FORMAT),
             'modified': datetime.datetime.strptime(u_attr['modified'], cls.DATETIME_FORMAT)}
        ) for u_attr in users_attributes]
        users = User.create_or_update(*users_attributes)
        [t_attr.update(
            {'created_at': datetime.datetime.strptime(t_attr['created_at'], cls.DATETIME_FORMAT),
             "coordinates": t_attr.get("coordinates") if t_attr.get("coordinates") else getattr(users[k], "coordinates", []),
             "sentiment": "neg",
             "is_sentiment_analyzed": True}
        ) for k, t_attr in enumerate(tweets_attributes)]

        tweets = Tweet.create_or_update(*tweets_attributes)
        for k, tweet in enumerate(tweets):
            users[k].posts.connect(tweet)
        for als in analysis_to_perform:
            als(bulk=tweets)


    @classmethod
    def connect_retweet(cls, related_data):
        if related_data['retweeted_id']:
            tweet = Tweet.nodes.get(id_str=related_data['tweet_id'])
            retweeted = Tweet.nodes.get(id_str=related_data['retweeted_id'])
            tweet.retweets.connect(retweeted)

    def get_tweet_features(self):
        return self.tokenize_tweet()

    def tokenize_tweet(self):
        if not isinstance(self.tweet, Tweet):
            raise Exception('tweet must be an instance of Tweet model.')
        tokenizer = WordPunctTokenizer()
        stemmer = FrenchStemmer()
        words = tokenizer.tokenize(self.clean_tweet())
        french_stopwords = stopwords.words('french')
        # add some punctuations to the stopwords set
        french_stopwords = french_stopwords + [",", ".", "?", "!", ";", ":", "(", ")", "[", "]", "{", "}", "'", '"',
                                               "`", "~", "@", "#", "$", "%", "^", "&", "*", "/", "-", "+"] + TO_TRACK
        words = set(words) - set(french_stopwords)
        return {stemmer.stem(word): True for word in words if word.isalnum()}

    def clean_tweet(self):
        """
        simply return the text of the tweet without hashtag or mention
        """
        text = self.tweet.text
        # remove mention
        text = re.sub(r"@(\w+)", '', text)
        # remove hashtag
        text = re.sub(r"#(\w+)", '', text)
        # remove URL
        text = re.sub(r"http\S+", '', text)
        return text

    def analyze_sentiment(self):
        if not isinstance(self.tweet, Tweet):
            raise Exception('tweet must be an instance of Tweet model.')
        classifier = joblib.load(self.classifier_path)
        return classifier.classify(self.tweet.features)

