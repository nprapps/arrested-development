import re

from peewee import *

from app_config import PRIMARY_CHARACTER_LIST

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

    def episode_count(self):
        return EpisodeJoke.select().where(EpisodeJoke.joke == self).count()

    def category(self):
        if self.primary_character == u"Lucille 2":
            return u"Miscellaneous"
        elif self.primary_character in PRIMARY_CHARACTER_LIST:
            return self.primary_character
        else:
            return u"Miscellaneous"

    def character_value(self):
        index = 0
        if self.primary_character not in PRIMARY_CHARACTER_LIST:
            self.primary_character = 'Miscellaneous'

        for character in PRIMARY_CHARACTER_LIST:
            if self.primary_character == character:
                return index
            index += 1

    def first_appearance(self):
        ej = EpisodeJoke.select().join(Episode).where(EpisodeJoke.joke == self).order_by(Episode.code)
        return ej[0].episode.code


class Episode(Model):
    season = IntegerField()
    episode = IntegerField()
    code = TextField()
    title = TextField()
    number = IntegerField()

    rating = TextField(null=True)
    production_code = TextField(null=True)
    run_date = DateField(null=True)
    blurb = TextField(null=True)

    tvdb_image = TextField(null=True)

    class Meta:
        database = db

    def joke_count(self):
        return EpisodeJoke.select().where(EpisodeJoke.episode == self).count()


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

    def formatted_type(self, **kwargs):
            if self.joke_type == "f":
                return "foreshadowing"
            elif self.joke_type == "b":
                return "background"
            else:
                return "standard"

    def connections(self):
        results = []
        output = []
        try:
            results.append(JokeConnection.get(joke1=self.joke, episode=self.episode).__dict__['_data'])
        except JokeConnection.DoesNotExist:
            pass
        try:
            results.append(JokeConnection.get(joke2=self.joke, episode=self.episode).__dict__['_data'])
        except JokeConnection.DoesNotExist:
            pass
        for joke in results:
            related = None
            if joke['joke1'] == self.joke.id:
                related = Joke.get(id=int(joke['joke2']))
            if joke['joke2'] == self.id:
                related = Joke.get(id=int(joke['joke1']))
            if related:
                output.append({
                    'url': 'joke-%s.html' % related.code,
                    'text': related.text,
                    'primary_character': related.primary_character,
                    'joke_code': related.code
                })
        return output


class JokeConnection(Model):
    joke1 = ForeignKeyField(Joke, cascade=False)
    joke2 = ForeignKeyField(Joke, cascade=False)
    episode = ForeignKeyField(Episode, cascade=False)

    class Meta:
        database = db
