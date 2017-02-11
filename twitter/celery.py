from __future__ import absolute_import
from twitter.settings import BROKER_URL
from celery import Celery

app = Celery('twitter',
             broker=BROKER_URL,
             include=['twitter.tasks'])
app.config_from_object('twitter.celeryconfig')
if __name__ == '__main__':
    app.start()
