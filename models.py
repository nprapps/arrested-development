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
            if joke['joke1'] == self.joke.id:
                related = Joke.get(id=int(joke['joke2']))
                output.append({'url': 'joke-%s.html' % related.code, 'text': related.text, 'primary_character': related.primary_character})
            if joke['joke2'] == self.id:
                related = Joke.get(id=int(joke['joke1']))
                output.append({'url': 'joke-%s.html' % related.code, 'text': related.text, 'primary_character': related.primary_character})

        return output


class JokeConnection(Model):
    joke1 = ForeignKeyField(Joke, cascade=False)
    joke2 = ForeignKeyField(Joke, cascade=False)
    episode = ForeignKeyField(Episode, cascade=False)

    class Meta:
        database = db
