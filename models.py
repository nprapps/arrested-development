from peewee import *

db = SqliteDatabase('data/app.db')


class Joke(Model):
    primary_character = TextField()
    code = IntegerField()
    text = TextField()

    class Meta:
        database = db

    def related_episodes(self):
        return None


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

    def related_jokes(self):
        return None


class EpisodeJoke(Model):
    joke = ForeignKeyField(Joke, cascade=False)
    episode = ForeignKeyField(Episode, cascade=False)
    joke_type = CharField(length=1, help_text="Choices are: f, b or 1")
    code = TextField()

    details = TextField(null=True)
    origin = TextField(null=True)
    connection = TextField(null=True)

    class Meta:
        database = db
