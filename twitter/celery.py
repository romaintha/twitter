from __future__ import absolute_import

from celery import Celery

app = Celery('twitter',
             broker='guest:guest@127.0.0.1:5672//',
             include=['twitter.tasks'])
app.config_from_object('twitter.celeryconfig')
if __name__ == '__main__':
    app.start()
