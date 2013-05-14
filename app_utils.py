import csv
import json

from bs4 import BeautifulSoup
import datetime
from dateutil.parser import *
import requests

from models import db, Joke, Episode, EpisodeJoke


def setup_tables():
    """
    Creates the tables for the Arrested Development database.
    """
    db.connect()
    Joke.create_table()
    Episode.create_table()
    EpisodeJoke.create_table()


def build_regression_csv():
    """
    Builds an episode-based CSV for @stiles to do our regression.
    Outputs a list of episodes with joke counts and ratings.
    """
    with open('data/regression.csv', 'wb') as csvfile:
        regressionwriter = csv.DictWriter(csvfile, ['episode_name', 'episode_id', 'jokes', 'rating'])
        regressionwriter.writerow({'episode_name': 'episode_name', 'episode_id': 'episode_id', 'jokes': 'jokes', 'rating': 'rating'})
        for episode in Episode.select():
            episode_dict = {}
            episode_dict['episode_name'] = episode.title.encode('utf-8')
            episode_dict['episode_id'] = episode.number
            episode_dict['rating'] = episode.rating
            episode_dict['jokes'] = EpisodeJoke.select().where(EpisodeJoke.episode == episode).count()
            regressionwriter.writerow(episode_dict)


def build_connections():
    """
    For each joke:
        Get all of the episodejokes for that joke.
        For each of those episodejokes:
            Get the joke attached via the "connection" field.
            Loop back through the episodejokes again:
                Find an episodejoke where the joke == the connected joke.
                Write a connection to that episode joke on both sides.
    """
    for episode in Episode.select():
        joke_list = []
        for joke in EpisodeJoke.select().join(Episode).where(Episode.code == episode.code):
            joke_list.append((joke.code, joke.joke.code))

        for episode_joke_code, joke_code in joke_list:
            joke = Joke.get(Joke.code == joke_code)
            episode_joke = EpisodeJoke.get(EpisodeJoke.code == episode_joke_code)
            if episode_joke.connection:
                connected_joke = Joke.get(Joke.text == episode_joke.connection.strip())
                for second_episode_joke_code, second_joke_code in joke_list:
                    if episode_joke_code == second_episode_joke_code:
                        pass
                    elif second_joke_code == connected_joke.code:
                        first_episode_joke = EpisodeJoke.get(EpisodeJoke.code == episode_joke_code)
                        second_episode_joke = EpisodeJoke.get(EpisodeJoke.code == second_episode_joke_code)

                        first_episode_joke.related_episode_joke = second_episode_joke
                        first_episode_joke.save()

                        second_episode_joke.related_episode_joke = first_episode_joke
                        second_episode_joke.save()


def write_jokes_json():
    """
    Writes the JSON for @onyxfish and @alykat's viz.
    Produces a list of jokes and within that a list of episodejokes
    where the joke appears, sorted by episode index number.
    """
    payload = []
    for joke in Joke.select():
        joke_dict = joke.__dict__['_data']
        joke_dict['episodejokes'] = []
        for ej in EpisodeJoke.select().join(Joke).where(Joke.code == joke.code):
            episode_dict = ej.__dict__['_data']
            episode_dict['episode_data'] = ej.episode.__dict__['_data']
            episode_dict['episode_data']['run_date'] = episode_dict['episode_data']['run_date'].strftime('%Y-%m-%d')
            episode_dict['related_episode_joke__joke'] = ej.joke.code

            del episode_dict['episode_data']['id']
            del episode_dict['episode']
            del episode_dict['joke']
            del episode_dict['id']

            joke_dict['episodejokes'].append(episode_dict)
        joke_dict['episodejokes'] = sorted(joke_dict['episodejokes'], key=lambda ej: ej['episode_data']['code'])

        del joke_dict['id']
        payload.append(joke_dict)

    with open('www/live-data/jokes.json', 'wb') as jokefile:
        jokefile.write(json.dumps(payload))


def update_episode_extras():
    """
    Gets extra episode data from Wikipedia, including directors/writers, run date
    and production code. Also grabs the newest season (4).
    """
    LABELS = ['episode', 'title', 'directed_by', 'written_by', 'run_date', 'production_code']
    r = requests.get('http://en.wikipedia.org/wiki/List_of_Arrested_Development_episodes')
    soup = BeautifulSoup(r.content)
    tables = soup.select('table.wikitable')[1:5]
    season = 1
    episodes = []

    for table in tables:
        counter = 54
        for row in table.select('tr')[1:]:
            episode_dict = {}
            episode_dict['season'] = season
            for index in range(0, 6):
                key = LABELS[index]
                if row.select('td')[index].string:
                    try:
                        value = row.select('td')[index].string.replace(' & ', ', ')
                    except AttributeError:
                        value = row.select('td')[index].string
                else:
                    iterator = 0
                    for string in row.select('td')[index].strings:
                        if key == 'title':
                            if iterator == 0:
                                value = string.replace('"', '')
                        if key == 'run_date':
                            if iterator == 2:
                                value = datetime.date(
                                    parse(string).year,
                                    parse(string).month,
                                    parse(string).day)
                        iterator += 1

                if value:
                    try:
                        episode_dict[key] = int(value)
                    except ValueError:
                        episode_dict[key] = value
                    except TypeError:
                        episode_dict[key] = value

            if episode_dict['season'] == 4 and episode_dict['episode'] == 15:
                pass
            elif episode_dict['season'] == 3 and episode_dict['episode'] == 13:
                episode_dict['written_by'] = "Story by Mitchell Hurwitz and Richard Day. Teleplay by Chuck Tatham and Jim Vallely"
                episodes.append(episode_dict)
            elif episode_dict['season'] == 4:
                episode_dict['number'] = counter
            else:
                episodes.append(episode_dict)

            counter += 1
        season += 1

    for episode in episodes:
        try:
            e = Episode.get(
                Episode.season == episode['season'],
                Episode.episode == episode['episode']
            )
            eq = Episode.update(**episode).where(Episode.code == e.code)
            eq.execute()
            e = Episode.get(
                Episode.season == episode['season'],
                Episode.episode == episode['episode']
            )
            # print '* Episode extra: %s' % e.code

        except Episode.DoesNotExist:
            episode['code'] = 's%se%s' % (str(episode['season']).zfill(2), str(episode['episode']).zfill(2))
            e = Episode.create(**episode)
            e.save()
            # print '+ Episode extra: %s' % e.code


def import_sheet(sheet):
    """
    Writes a CSV file from our Arrested Development Google doc sheets.
    """
    r = requests.get('https://docs.google.com/spreadsheet/pub?key=0Akb_aqtU8lsGdGhIRXhsT24taTlXNGI4YndnS1c4eEE&single=true&gid=%s&output=csv' % sheet)
    with open('data/arrested-%s.csv' % sheet, 'wb') as csv_file:
        csv_file.write(r.content)


def parse_sheet(sheet, model):
    """
    Parses sheets with the appropriate parser.
    """
    with open('data/arrested-%s.csv' % sheet) as csv_file:
        if sheet == '1':
            _parse_episodes(csv.DictReader(csv_file))
        if sheet == '0':
            if model == 'jokes':
                _parse_jokes(csv.DictReader(csv_file))
            if model == 'episodejokes':
                _parse_episodejokes(csv.DictReader(csv_file))
        if sheet in ['3', '4', '5']:
            _parse_episodejoke_details(csv.DictReader(csv_file), sheet)
        if sheet == '7':
            _parse_joke_blurbs(csv.DictReader(csv_file))


def _parse_joke_blurbs(sheet):
    """
    Grab the joke blurbs sheet from Google docs.
    """
    for row in sheet:
        joke = Joke.get(Joke.code == row['Code'])
        joke.blurb = row['Description']
        try:
            joke.related_joke_code = int(row['Related'])
        except ValueError:
            pass

        joke.save()


def _parse_episodes(sheet):
    """
    Parses episode sheet.
    Imports episodes.
    Will not update.
    """
    episodes = []
    seasons = []
    ratings = []
    names = []
    indexes = []

    zip_list = [seasons, episodes, ratings, None, names]

    counter = 0
    for row in sheet:
        if counter != 3:
            zip_list[counter] += row.values()
        counter += 1
        indexes = row.keys()

    output = []

    for episode in zip(episodes, seasons, ratings, names, indexes):
        if episode[0] == 'EPISODE':
            pass
        else:
            episode_dict = {}
            episode_dict['episode'] = int(episode[0])
            episode_dict['season'] = int(episode[1])
            episode_dict['title'] = episode[3].decode('utf-8')
            episode_dict['rating'] = episode[2]
            episode_dict['code'] = 's%se%s' % (episode[1].zfill(2), episode[0].zfill(2))
            episode_dict['number'] = int(episode[4]) + 1
            output.append(episode_dict)

    for row in output:
        try:
            r = Episode.get(Episode.code == row['code'])
            # print '* Episode: %s' % r.title

        except Episode.DoesNotExist:
            r = Episode.create(**row)
            r.save()
            # print '+ Episode: %s' % r.title


def _parse_jokes(sheet):
    """
    Parses joke sheet.
    Imports jokes.
    Will not update.
    """
    for row in sheet:
        joke_dict = {}
        for item in ['code', 'primary_character', 'text']:
            try:
                joke_dict[item] = int(row[item])
            except ValueError:
                joke_dict[item] = row[item].decode('utf-8')
        try:
            j = Joke.get(Joke.code == joke_dict['code'])
            # print '* Joke: %s' % j.text

        except Joke.DoesNotExist:
            j = Joke.create(**joke_dict)
            j.save()
            # print '+ Joke: %s' % j.text


def _parse_episodejoke_details(sheet, sheet_num):
    """
    Parses the details, origin and connection sheets.
    Adds data to existing episodejokes.
    """
    FIELDS = [None, None, None, 'details', 'origin', 'connection']
    field = FIELDS[int(sheet_num)]
    broken = []
    for row in sheet:
        for column in range(3, 55):
            episode_title, value = row.items()[column]
            if value:
                e = Episode.get(Episode.title == episode_title.decode('utf-8'))
                j = Joke.get(Joke.code == row['code'])
                ej_code = '%sj%s' % (e.code, j.code)
                payload = {}
                payload[field] = value

                try:
                    ej = EpisodeJoke.update(**payload).where(EpisodeJoke.code == ej_code)
                    ej.execute()

                except EpisodeJoke.DoesNotExist:
                    broken.append({'episode': e.code, 'joke': j.text.encode('utf-8'), 'context': value, 'sheet': field})

    with open('data/broken.csv', 'a') as brokenfile:
        writer = csv.DictWriter(brokenfile, ['episode', 'joke', 'context', 'sheet'])
        for row in broken:
            writer.writerow(row)


def _parse_episodejokes(sheet):
    """
    Parses joke sheet.
    Imports episodejokes.
    Will not update.
    """

    for row in sheet:
        for column in range(2, len(row.items())):
            box = row.items()[column]
            if box[1].decode('utf-8') in ['1', 'f', 'b']:
                ej_dict = {}
                ej_dict['joke'] = Joke.get(Joke.code == row['code'])
                ej_dict['episode'] = Episode.get(Episode.title == box[0].decode('utf-8'))
                ej_dict['joke_type'] = box[1].decode('utf-8')
                ej_dict['code'] = '%sj%s' % (ej_dict['episode'].code, ej_dict['joke'].code)

                try:
                    ej = EpisodeJoke.get(EpisodeJoke.code == ej_dict['code'])
                    # print '* EpisodeJoke: %s' % ej.code

                except EpisodeJoke.DoesNotExist:
                    ej = EpisodeJoke.create(**ej_dict)
                    ej.save()
                    # print '+ EpisodeJoke: %s' % ej.code
