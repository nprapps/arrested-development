#!/usr/bin/env python

import json
from mimetypes import guess_type
import urllib

import envoy
from flask import Flask, Markup, abort, render_template

import app_config
from models import db, Joke, Episode, EpisodeJoke
from render_utils import flatten_app_config, make_context

app = Flask(app_config.PROJECT_NAME)


@app.route('/episodes.html')
def _episode_list():
    context = make_context()
    context['episodes'] = []
    for episode in Episode.select():
        context['episodes'].append(episode)
    context['episodes'] = sorted(context['episodes'], key=lambda episode: episode.code)
    return render_template('episode_list.html', **context)


@app.route('/episode-<episode_code>.html')
def _episode_detail(episode_code):
    context = make_context()
    context['episode'] = Episode.get(Episode.code == episode_code)
    context['episodejokes'] = EpisodeJoke.select().where(EpisodeJoke.episode == context['episode'])
    context['episodejokes'] = sorted(context['episodejokes'], key=lambda ej: ej.joke.code)
    return render_template('episode_detail.html', **context)


@app.route('/jokes.html')
def _joke_list():
    context = make_context()
    context['jokes'] = []
    for joke in Joke.select():
        context['jokes'].append(joke)
    context['jokes'] = sorted(context['jokes'], key=lambda joke: joke.code)
    return render_template('joke_list.html', **context)


@app.route('/joke-<joke_code>.html')
def _joke_detail(joke_code):
    context = make_context()
    context['joke'] = Joke.get(Joke.code == joke_code)
    context['episodejokes'] = EpisodeJoke.select().where(EpisodeJoke.joke == context['joke'])
    context['episodejokes'] = sorted(context['episodejokes'], key=lambda ej: ej.episode.code)
    return render_template('joke_detail.html', **context)


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
