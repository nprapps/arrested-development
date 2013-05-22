#!/usr/bin/env python

import json
from mimetypes import guess_type
import urllib

import envoy
from flask import Flask, Markup, abort, render_template

import app_config
from models import Joke, Episode, EpisodeJoke
from render_utils import flatten_app_config, make_context

app = Flask(app_config.PROJECT_NAME)


def _all_seasons():
    output = []
    SEASONS = [1, 2, 3]
    if app_config.IMPORT_NEW_SEASON is True:
        SEASONS.append(4)
    for season in SEASONS:
        season_dict = {}
        season_dict['season'] = season
        season_dict['episodes'] = []
        for episode in Episode.select().where(Episode.season == season):
            season_dict['episodes'].append({
                'url': 'episode-%s.html' % episode.code,
                'text': '%s: %s' % (episode.episode, episode.title),
                'episode': episode.episode,
                'code': episode.code
            })
        season_dict['episodes'] = sorted(season_dict['episodes'], key=lambda episode: episode['episode'])
        output.append(season_dict)
    return output


@app.route('/episode-<episode_code>.html')
def _episode_detail(episode_code):
    context = make_context()
    context['episode'] = Episode.get(Episode.code == episode_code)
    context['jokes'] = {}
    context['joke_count'] = 0

    for joke in EpisodeJoke.select().where(EpisodeJoke.episode == context['episode']):
        group = joke.joke.primary_character

        if group not in app_config.PRIMARY_CHARACTER_LIST:
            group = 'Miscellaneous'

        if group not in context['jokes']:
            context['jokes'][group] = []

        context['jokes'][group].append(joke)
        context['joke_count'] += 1

    context['seasons'] = _all_seasons()

    context['group_order'] = [g for g in app_config.PRIMARY_CHARACTER_LIST if g in context['jokes']]

    try:
        context['next'] = Episode.get(number=context['episode'].number + 1)
    except Episode.DoesNotExist:
        context['next'] = None
    try:
        context['prev'] = Episode.get(number=context['episode'].number - 1)
    except Episode.DoesNotExist:
        context['prev'] = None

    return render_template('episode_detail.html', **context)


@app.route('/joke-<joke_code>.html')
def _joke_detail(joke_code):
    context = make_context()
    context['joke'] = Joke.get(Joke.code == int(joke_code))
    context['episodejokes'] = EpisodeJoke.select().where(EpisodeJoke.joke == context['joke'])
    context['episodejokes'] = sorted(context['episodejokes'], key=lambda ej: ej.episode.code)
    context['seasons'] = _all_seasons()

    with open('www/live-data/jokes.json') as f:
        data = json.load(f)

    group_order = data['group_order']
    joke_data = data['jokes']
    connections = data['connections']

    connected_joke_codes = [int(joke_code)]

    def filter_connections(c):
        if c['joke1_code'] == int(joke_code) or c['joke2_code'] == int(joke_code):
            connected_joke_codes.append(c['joke1_code'])
            connected_joke_codes.append(c['joke2_code'])

            return True
        return False

    connections = filter(filter_connections, connections)

    def filter_jokes(c):
        return c['code'] in connected_joke_codes

    for group, jokes in joke_data.items():
        joke_data[group] = filter(filter_jokes, jokes)
        if len(joke_data[group]) == 0:
            del joke_data[group]
            group_order.remove(group)

    context['group_order'] = Markup(json.dumps(group_order))
    context['joke_data'] = Markup(json.dumps(joke_data))
    context['connection_data'] = Markup(json.dumps(connections))
    context['episodes'] = Markup(json.dumps(data['episodes']))

    group = context['joke'].primary_character

    if group not in app_config.PRIMARY_CHARACTER_LIST:
        group = 'Miscellaneous'

    context['group'] = group

    return render_template('joke_detail.html', **context)


@app.route('/')
def index():
    context = make_context()
    context['jokes'] = []

    for joke in Joke.select():
        context['jokes'].append(joke)

    context['jokes'] = sorted(context['jokes'], key=lambda joke: joke.code)
    context['seasons'] = _all_seasons()

    with open('www/live-data/jokes.json') as f:
        data = json.load(f)

    context['group_order'] = Markup(json.dumps(data['group_order']))
    context['joke_data'] = Markup(json.dumps(data['jokes']))
    context['connection_data'] = Markup(json.dumps(data['connections']))
    context['episodes'] = Markup(json.dumps(data['episodes']))

    return render_template('viz.html', **context)


@app.route('/admin/episodes/<episode_code>/', methods=['GET', 'PUT'])
def _admin_episodes(episode_code):
    from flask import request
    if request.method == 'GET':
        context = {}
        context['episode'] = Episode.get(code=episode_code)
        context['episodejokes'] = EpisodeJoke.select().join(Episode).where(Episode.code == episode_code)
        context['jokes'] = Joke.select()
        context['seasons'] = _all_seasons()

        try:
            context['next'] = Episode.get(number=context['episode'].number + 1)
        except Episode.DoesNotExist:
            context['next'] = None
        try:
            context['prev'] = Episode.get(number=context['episode'].number - 1)
        except Episode.DoesNotExist:
            context['prev'] = None

        return render_template('admin_episode_detail.html', **context)

    if request.method == 'PUT':
        e = Episode.get(code=episode_code)
        e.blurb = request.form.get('blurb', None)
        e.save()
        return '%s' % e.id


@app.route('/admin/episodes/<episode_code>/episodejoke/<episode_joke_id>/delete/', methods=['DELETE'])
def _admin_episodejokes_delete(episode_code, episode_joke_id):
    from flask import request
    if request.method == 'DELETE':
        EpisodeJoke.delete().where(EpisodeJoke.id == int(episode_joke_id)).execute()
        return episode_joke_id

@app.route('/admin/episodes/<episode_code>/episodejoke/', methods=['PUT', 'POST'])
def _admin_episodejokes(episode_code):
    from flask import request

    details = request.form.get('details', None)

    if request.method == 'POST':
        episode_joke_id = request.form.get('episode_joke_id', None)
        ej = EpisodeJoke.get(id=int(episode_joke_id))
        ej.details = details
        ej.save()
        return '%s' % ej.id

    if request.method == 'PUT':
        joke_code = request.form.get('joke_code', None)
        joke_type = request.form.get('type', None)

        joke = Joke.get(code=int(joke_code))
        episode = Episode.get(code=episode_code)
        code = 's%se%sj%s' % (
            str(episode.season).zfill(2),
            str(episode.episode).zfill(2),
            joke.code
        )

        context = {}
        context['ej'] = EpisodeJoke(joke=joke, episode=episode, joke_type=joke_type, details=details, code=code)
        context['ej'].save()
        return render_template('_episodejoke_form_row.html', **context)


# Render LESS files on-demand
@app.route('/less/<string:filename>')
def _less(filename):
    try:
        with open('less/%s' % filename) as f:
            less = f.read()
    except IOError:
        abort(404)

    r = envoy.run('node_modules/.bin/lessc -', data=less)

    return r.std_out, 200, {'Content-Type': 'text/css'}


# Render JST templates on-demand
@app.route('/js/templates.js')
def _templates_js():
    r = envoy.run('node_modules/.bin/jst --template underscore jst')

    return r.std_out, 200, {'Content-Type': 'application/javascript'}


# Render application configuration
@app.route('/js/app_config.js')
def _app_config_js():
    config = flatten_app_config()
    js = 'window.APP_CONFIG = ' + json.dumps(config)

    return js, 200, {'Content-Type': 'application/javascript'}


# Server arbitrary static files on-demand
@app.route('/<path:path>')
def _static(path):
    try:
        with open('www/%s' % path) as f:
            return f.read(), 200, {'Content-Type': guess_type(path)[0]}
    except IOError:
        abort(404)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=app_config.DEBUG)
