import csv

import requests

from models import db, Joke, Episode, EpisodeJoke


def setup_tables():
    db.connect()
    Joke.create_table()
    Episode.create_table()
    EpisodeJoke.create_table()


def import_sheet(sheet):
    r = requests.get('https://docs.google.com/spreadsheet/pub?key=0Akb_aqtU8lsGdGhIRXhsT24taTlXNGI4YndnS1c4eEE&single=true&gid=%s&output=csv' % sheet)
    with open('data/arrested-%s.csv' % sheet, 'wb') as csv_file:
        csv_file.write(r.content)


def parse_sheet(sheet, model):
    with open('data/arrested-%s.csv' % sheet) as csv_file:
        if sheet == '1':
            _parse_episodes(csv.DictReader(csv_file))
        if sheet == '0':
            if model == 'jokes':
                _parse_jokes(csv.DictReader(csv_file))
            if model == 'episodejokes':
                _parse_episodejokes(csv.DictReader(csv_file), 3)
        if sheet in ['3', '4', '5']:
            _parse_episodejokes(csv.DictReader(csv_file), 0)
    return


def _parse_episodes(sheet):
    episodes = []
    seasons = []
    ratings = []
    names = []

    zip_list = [seasons, episodes, ratings, None, names]

    counter = 0
    for row in sheet:
        if counter != 3:
            zip_list[counter] += row.values()
        counter += 1

    output = []

    for episode in zip(episodes, seasons, ratings, names):
        if episode[0] == 'EPISODE':
            pass
        else:
            episode_dict = {}
            episode_dict['episode'] = int(episode[0])
            episode_dict['season'] = int(episode[1])
            episode_dict['title'] = episode[3].decode('utf-8')
            episode_dict['rating'] = episode[2]
            episode_dict['code'] = 's%se%s' % (episode[1], episode[0].zfill(2))
            output.append(episode_dict)

    for row in output:
        try:
            r = Episode.get(Episode.code == row['code'])
            print '* %s' % r.title

        except Episode.DoesNotExist:
            r = Episode.create(**row)
            r.save()
            print '+ %s' % r.title
    return


def _parse_jokes(sheet):
    for row in sheet:
        joke_dict = {}
        for item in ['code', 'primary_character', 'text']:
            try:
                joke_dict[item] = int(row[item])
            except ValueError:
                joke_dict[item] = row[item].decode('utf-8')
        try:
            j = Joke.get(Joke.code == joke_dict['code'])
            print '* %s' % j.text

        except Joke.DoesNotExist:
            j = Joke.create(**joke_dict)
            j.save()
            print '+ %s' % j.text
    return


def _parse_episodejokes(sheet, offset):
    start_column = 0 + offset
    end_column = 53 + offset

    for row in sheet:
        for column in range(start_column, end_column):
            box = row.items()[column]
            if box[1].decode('utf-8') in ['1', 'f', 'b']:
                ej_dict = {}
                ej_dict['joke'] = Joke.get(Joke.code == row['code'])
                ej_dict['episode'] = Episode.get(Episode.title == box[0].decode('utf-8'))
                ej_dict['joke_type'] = box[1].decode('utf-8')
                ej_dict['code'] = '%sj%s' % (ej_dict['episode'].code, ej_dict['joke'].code)

                try:
                    ej = EpisodeJoke.get(EpisodeJoke.code == ej_dict['code'])
                    print '* %s' % ej.code

                except EpisodeJoke.DoesNotExist:
                    ej = EpisodeJoke.create(**ej_dict)
                    ej.save()
                    print '+ %s' % ej.code
    return
