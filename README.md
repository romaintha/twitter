# twitter
Use the twitter streaming API and store tweets, users, ... in a NEO4J database.

Add to your module a local_settings.py file which contains your twitter API credentials :
CONSUMER_TOKEN = ''
CONSUMER_SECRET = ''
ACCESS_TOKEN = ''
ACCESS_SECRET = ''

Add as well a BROKER_URL to your settings like :
BROKER_URL = 'amqp://guest:guest@127.0.0.1:5672/'

Then starting streaming is quite simple:
You need to instantiate the streamer :
streamer = Streaming(pipeline=stream_pipeline, batch_size=10)
where stream_pipeline could be whatever you want where you process the tweets. I include a simple example in the utils.py module,
and batch_size should be the amount of tweets processed at once. I tried with 100, and it works just fine.

Then you need to start streaming:
streamer.start_streaming(to_track=settings.TO_TRACK)

This will generate messages to your broker. To consume them, simply start celery like that :
celery -A twitter worker -l info -Q streaming -n streaming