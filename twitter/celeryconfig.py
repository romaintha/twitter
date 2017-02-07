from kombu import Queue, Exchange


CELERY_TASK_SERIALIZER = 'json'

CELERY_QUEUES = (
    Queue('streaming', Exchange('streaming'), routing_key='streaming'),
)

CELERY_ROUTES = {
    'twitter.tasks.process_tweets': {'queue': 'streaming', 'routing_key': 'streaming'},
}