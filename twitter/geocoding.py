import datetime
import time

from twitter.models import User
from neomodel import db
from geopy.geocoders import GoogleV3
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable
from twitter.models import Tweet

class Geolocation():

    def __init__(self):
        self.geocoder = GoogleV3()
        self.updated_tweets = []

    def update_user_location(self, user):
        if user.location:
            # hardcoded safetiness against googleMap rate limit
            time.sleep(0.2)
            timeout = True
            try:
                geocode = self.geocoder.geocode(query=user.location, exactly_one=True)
            except:
                geocode = None
            if geocode:
                user.coordinates = [geocode.point[1], geocode.point[0]]
                user.modified = datetime.datetime.now()
                user.save()
                self.update_user_tweets_location(user)
                users = self.update_users_with_same_location(user)
            return self.updated_tweets

    def update_user_tweets_location(self, user):
        results, meta = db.cypher_query('MATCH (u:User)-[:POSTS]->(t:Tweet) WHERE u.id_str="%s" RETURN t'% user.id_str)
        user_tweets = [Tweet.inflate(row[0]) for row in results]
        for tweet in user_tweets:
            if tweet.coordinates == []:
                tweet.coordinates = user.coordinates
                tweet.save()
                self.updated_tweets.append(tweet)

    def update_users_with_same_location(self, user):
        users = User.nodes.filter(location=user.location).exclude(id_str=user.id_str)
        for another_user in users:
            another_user.coordinates = user.coordinates
            another_user.modified = datetime.datetime.now()
            another_user.save()
            self.update_user_tweets_location(another_user)