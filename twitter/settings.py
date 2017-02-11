import os

DIR_PATH = os.path.dirname(os.path.realpath(__file__))

# Twitter Apps authentication
CONSUMER_TOKEN = ''
CONSUMER_SECRET = ''
ACCESS_TOKEN = ''
ACCESS_SECRET = ''

# Things to track
TO_TRACK = [
    'arthaud',
    'mélenchon',
    'jadot',
    'hamon', 'montebourg', 'valls','peillon',
    'macron',
    'bayrou', 'lassale',
    'fillon',
    'dupont-aignan',
    'le pen',
    'cheminade',]

# DateTime format
DATETIME_FORMAT = '%Y-%m-%d_%H:%M'

# Used to get twitter API credential
from twitter.local_settings import *