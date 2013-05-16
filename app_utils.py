import csv
import json

from bs4 import BeautifulSoup
import datetime
from dateutil.parser import *
import requests

from models import db, Joke, Episode, EpisodeJoke, JokeConnection


def setup_tables():
    """
    Creates the tables for the Arrested Development database.
    """
    db.connect()
    Joke.create_table()
    Episode.create_table()
    EpisodeJoke.create_table()
    JokeConnection.create_table()


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
    for episode_joke in EpisodeJoke.select():
        if episode_joke.connection:
            joke1 = episode_joke.joke
            joke2 = Joke.get(Joke.text == episode_joke.connection.strip())
            episode = episode_joke.episode

            if joke2.code < joke1.code:
                tmp = joke2
                joke2 = joke1
                joke1 = tmp

            JokeConnection(joke1=joke1, joke2=joke2, episode=episode).save()


def write_jokes_json():
    """
    Writes the JSON for @onyxfish and @alykat's viz.
    Produces a list of jokes and within that a list of episodejokes
    where the joke appears, sorted by episode index number.
    """
    payload = {
        'group_order': [
            'The Bluths',
            'Michael',
            'G.O.B.',
            'Tobias',
            'Lindsay',
            'Buster',
            'Oscar',
            'George Sr.',
            'Lucille',
            'Maeby',
            'George Michael',
            'Miscellaneous'
        ],
        'jokes': {},
        'connections': [],
        'episodes': {}
    }

    for joke in Joke.select().order_by(Joke.primary_character):
        if joke.primary_character not in payload['group_order']:
            joke.primary_character = 'Miscellaneous'

        if joke.primary_character not in payload['jokes']:
            payload['jokes'][joke.primary_character] = []

        joke_dict = joke.__dict__['_data']

        del joke_dict['id']

        joke_dict['episodejokes'] = []

        for ej in EpisodeJoke.select().join(Joke).where(Joke.code == joke.code):
            episode_dict = ej.__dict__['_data']
            episode_dict['episode_number'] = ej.episode.number

            del episode_dict['episode']
            del episode_dict['joke']
            del episode_dict['id']

            joke_dict['episodejokes'].append(episode_dict)

        joke_dict['episodejokes'] = sorted(joke_dict['episodejokes'], key=lambda ej: ej['episode_number'])

        payload['jokes'][joke.primary_character].append(joke_dict)

    for episode in Episode().select().order_by(Episode.number):
        episode_dict = episode.__dict__['_data']
        episode_dict['run_date'] = episode_dict['run_date'].strftime('%Y-%m-%d')

        payload['episodes'][episode.number] = episode_dict

    for primary_character, jokes in payload['jokes'].items():
        payload['jokes'][primary_character] = sorted(jokes, key=lambda j: j['episodejokes'][0]['episode_number'])

    for connection in JokeConnection.select():
        payload['connections'].append({
            'joke1_code': connection.joke1.code,
            'joke2_code': connection.joke2.code,
            'episode_number': connection.episode.number
        })

    payload['connections'] = sorted(payload['connections'], key=lambda c: c['joke1_code'])

    with open('www/live-data/jokes.json', 'wb') as jokefile:
        jokefile.write(json.dumps(payload))


def parse_tvdb_xml(xmlfile):
    FIELDS_LIST = [
        ('blurb', 'Overview', 'str'),
        ('run_date', 'FirstAired', 'date'),
        ('season', 'Combined_season', 'int'),
        ('production_code', 'ProductionCode', 'str'),
        ('episode', 'EpisodeNumber', 'int'),
        ('season', 'Season', 'int')
    ]
    soup = BeautifulSoup(xmlfile, "xml")
    for episode in soup.findAll('Episode'):
        season = int(episode.find('Combined_season').text)
        if season > 0:
            episode_dict = {}
            for model_field, xml_field, data_type in FIELDS_LIST:
                try:
                    if episode.find(xml_field).text:
                        episode_dict[model_field] = episode.find(xml_field).text
                        if data_type == 'int':
                            episode_dict[model_field] = int(episode_dict[model_field])
                        if data_type == 'date':
                            d = parse(episode_dict[model_field])
                            episode_dict[model_field] = datetime.date(d.year, d.month, d.day)
                except AttributeError:
                    pass
            if episode.find('filename').text:
                episode_dict['tvdb_image'] = 'http://thetvdb.com/banners/_cache/%s' % episode.find('filename').text
            episode_dict['code'] = 's%se%s' % (
                str(episode_dict['season']).zfill(2),
                str(episode_dict['episode']).zfill(2))
            try:
                Episode.get(code=episode_dict['code'])
                Episode.update(**episode_dict).where(Episode.code == episode_dict['code']).execute()
            except Episode.DoesNotExist:
                if episode_dict['season'] == 4:
                    episode_dict['number'] = episode_dict['episode'] + 53
                    episode_dict['code'] = 's%se%s' % (
                        str(episode_dict['season']).zfill(2),
                        str(episode_dict['episode']).zfill(2))
                    episode_dict['title'] = episode.find('EpisodeName').text
                Episode(**episode_dict).save()


def update_episode_extras():
    try:
        with open('data/extras.xml', 'rb') as xmlfile:
            parse_tvdb_xml(xmlfile)
    except IOError:
        r = requests.get('http://thetvdb.com/api/983EF67DBCBB1A2D/series/72173/all/en.xml')
        with open('data/extras.xml', 'wb') as xmlfile:
            xmlfile.write(r.content)
        update_episode_extras()


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
        for column in range(2, 55):
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
