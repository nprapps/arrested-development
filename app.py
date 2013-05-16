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


@app.route('/episodes.html')
def episode_list():
    context = make_context()
    context['episodes'] = []
    for episode in Episode.select():
        context['episodes'].append(episode)
    context['episodes'] = sorted(context['episodes'], key=lambda episode: episode.code)
    context['seasons'] = _all_seasons()
    return render_template('episode_list.html', **context)


@app.route('/jokes.html')
def joke_list():
    context = make_context()
    context['jokes'] = []
    for joke in Joke.select():
        context['jokes'].append(joke)
    context['jokes'] = sorted(context['jokes'], key=lambda joke: joke.code)
    context['seasons'] = _all_seasons()
    return render_template('joke_list.html', **context)


@app.route('/episode-<episode_code>.html')
def _episode_detail(episode_code):
    context = make_context()
    context['episode'] = Episode.get(Episode.code == episode_code)
    context['episodejokes'] = []
    for character in app_config.PRIMARY_CHARACTER_LIST:
        character_dict = {}
        character_dict['name'] = character
        character_dict['jokes'] = []
        for joke in EpisodeJoke.select().where(EpisodeJoke.episode == context['episode']):
            if joke.joke.primary_character == character:
                character_dict['jokes'].append(joke)
        if len(character_dict['jokes']) > 0:
            character_dict['jokes'] = sorted(character_dict['jokes'], key=lambda ej: ej.episode.number)
            context['episodejokes'].append(character_dict)
    context['seasons'] = _all_seasons()
    return render_template('episode_detail.html', **context)


@app.route('/joke-<joke_code>.html')
def _joke_detail(joke_code):
    context = make_context()
    context['joke'] = Joke.get(Joke.code == joke_code)
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

    return render_template('joke_detail.html', **context)


@app.route('/')
@app.route('/viz.html')
def _viz():
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


# Render LESS files on-demand
@app.route('/less/<string:filename>')
def _less(filename):
    try:
        with open('less/%s' % filename) as f:
            less = f.read()
    except IOError:
        abort(404)

    r = envoy.run('node_modules/.bin/lessc -', data=less)

    return r.std_out, 200, { 'Content-Type': 'text/css' }

# Render JST templates on-demand
@app.route('/js/templates.js')
def _templates_js():
    r = envoy.run('node_modules/.bin/jst --template underscore jst')

    return r.std_out, 200, { 'Content-Type': 'application/javascript' }

# Render application configuration
@app.route('/js/app_config.js')
def _app_config_js():
    config = flatten_app_config()
    js = 'window.APP_CONFIG = ' + json.dumps(config)

    return js, 200, { 'Content-Type': 'application/javascript' }

# Server arbitrary static files on-demand
@app.route('/<path:path>')
def _static(path):
    try:
        with open('www/%s' % path) as f:
            return f.read(), 200, { 'Content-Type': guess_type(path)[0] }
    except IOError:
        abort(404)

@app.template_filter('urlencode')
def urlencode_filter(s):
    """
    Filter to urlencode strings.
    """
    if type(s) == 'Markup':
        s = s.unescape()

    s = s.encode('utf8')
    s = urllib.quote_plus(s)

    return Markup(s)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=app_config.DEBUG)
