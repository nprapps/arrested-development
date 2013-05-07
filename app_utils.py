import csv

import peewee
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


def parse_sheet(sheet):
    with open('data/arrested-%s.csv' % sheet) as csv_file:
        if sheet == '0':
            _parse_jokes(csv.DictReader(csv_file))
        if sheet == '1':
            _parse_episodes(csv.DictReader(csv_file))


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


def _parse_jokes(sheet):
    print sheet
