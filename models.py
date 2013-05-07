from peewee import *

db = SqliteDatabase('app.db')


class Joke(Model):
    primary_character = TextField()
    code = IntegerField()
    text = TextField()

    class Meta:
        database = db


class Episode(Model):
    season = IntegerField()
    episode = IntegerField()
    code = TextField()
    title = TextField()
    rating = TextField()

    run_date = DateField(null=True)
    netflix_link = TextField(null=True)

    class Meta:
        database = db


class EpisodeJoke(Model):
    joke = ForeignKeyField(Joke, related_name='jokes', cascade=False)
    episode = ForeignKeyField(Episode, related_name='episodes', cascade=False)
    character = TextField()
    text = TextField()

    class Meta:
        database = db
