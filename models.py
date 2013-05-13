import re

from peewee import *

db = SqliteDatabase('data/app.db', autocommit=True)


def slugify(text):
    value = re.sub('[^\w\s-]', '', text).strip().lower()
    return re.sub('[^\w\s-]', '', value).strip().lower()


class Joke(Model):
    primary_character = TextField()
    code = IntegerField()
    text = TextField()

    blurb = TextField(null=True)
    related_joke_code = IntegerField(null=True)

    class Meta:
        database = db

    @classmethod
    def slug():
        return slugify(self.text)

    def episode_count(self):
        return EpisodeJoke.select().where(EpisodeJoke.joke == self).count()


class Episode(Model):
    season = IntegerField()
    episode = IntegerField()
    code = TextField()
    title = TextField()
    number = IntegerField()

    rating = TextField(null=True)
    directed_by = TextField(null=True)
    written_by = TextField(null=True)
    production_code = CharField(max_length=255, null=True)
    run_date = DateField(null=True)

    wikipedia_link = TextField(null=True)
    netflix_link = TextField(null=True)

    class Meta:
        database = db

    @classmethod
    def slug():
        return slugify(self.code)

    def joke_count(self):
        return EpisodeJoke.select().where(EpisodeJoke.episode == self).count()


class EpisodeJoke(Model):
    joke = ForeignKeyField(Joke, cascade=False)
    related_episode_joke = ForeignKeyField('self', cascade=False, null=True)
    episode = ForeignKeyField(Episode, cascade=False)
    joke_type = CharField(length=1, help_text="Choices are: f, b or 1")
    code = TextField()

    details = TextField(null=True)
    origin = TextField(null=True)
    connection = TextField(null=True)

    class Meta:
        database = db

    @classmethod
    def slug():
        return slugify(self.code)
