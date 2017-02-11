from twitter.tweet_processing import TweetProcessing
from twitter.tasks import bulk_parsing

def stream_pipeline(statuses):
    users_attributes, tweets_attributes = TweetProcessing.prepare_batch_processing(statuses)
    bulk_parsing.delay(users_attributes, tweets_attributes)