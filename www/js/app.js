var EPISODE_COUNT = 68;

var DOT_RADIUS = 5;
var LABEL_WIDTH = 200;
var GROUP_LABEL_HEIGHT = 16;
var LINE_INTERVAL = 18;
var GROUP_INTERVAL = 33;
var OFFSET_X_RIGHT = DOT_RADIUS;
var OFFSET_X_LEFT = OFFSET_X_RIGHT + LABEL_WIDTH;
var OFFSET_Y = DOT_RADIUS + 3 + GROUP_LABEL_HEIGHT;
var IS_MOBILE = Modernizr.touch; // disable certain features for touch devices
var WINDOW_WIDTH = $('body').width();
var IS_WEBKIT = $.browser.webkit;
var IS_IE8 = ($.browser.msie && parseInt($.browser.version) == 8);
var INITIAL_LOAD = false;

var $body = null;
var $full_viz = null;
var $joke_viz = null;
var paper = null;
var $tooltip = null;

var joke_code_to_line_y_map = {};
var joke_code_to_related_jokes_map = {};
var episode_number_to_jokes_map = {};

/*
 * Loop through data, render the big graphic
 */
function render_viz($viz, group_order, joke_data, connection_data, episodes, joke_code) {
    var width = $viz.width();
    var height = $viz.height();
    var joke_code = joke_code || null;

    if (WINDOW_WIDTH < 768) {
        IS_MOBILE = true;
        height = 5000;
        $viz.height(height + 'px');
        LABEL_WIDTH = Math.round(width * .4);
        DOT_RADIUS = 2;
        LINE_INTERVAL = 30;
        OFFSET_X_RIGHT = DOT_RADIUS;
        OFFSET_X_LEFT = OFFSET_X_RIGHT + LABEL_WIDTH;
    } else {
        IS_MOBILE = false;
        DOT_RADIUS = 5;
        LABEL_WIDTH = 200;
        LINE_INTERVAL = 18;
        OFFSET_X_RIGHT = DOT_RADIUS;
        OFFSET_X_LEFT = OFFSET_X_RIGHT + LABEL_WIDTH;
    }

    if (!IS_IE8) {
        paper = new Raphael($viz[0], '100%', '100%');
    }

    var line_y = OFFSET_Y;
    var dot_interval = (width - (OFFSET_X_LEFT + OFFSET_X_RIGHT)) / (EPISODE_COUNT + 1);

    var joke_headers = '';
    var joke_labels = '<ul id="viz-labels" style="width: ' + LABEL_WIDTH + 'px;">';
    var season_labels = '';
    var season_labeled = false;

    // Render joke lines
    for (var g in group_order) {
        var group = group_order[g];
        var jokes = joke_data[group];

        for (var i = 0; i < jokes.length; i++) {
            var joke = jokes[i];
            joke_code_to_line_y_map[joke['code']] = line_y;
            joke_code_to_related_jokes_map[joke['code']] = [joke['code']];

            var episodejokes = joke['episodejokes'];
            var first_episode_number = episodejokes[0]['episode_number'];
            var last_episode_number = episodejokes[episodejokes.length-1]['episode_number'] + 1; // +1 to make sure it goes off the side

            var path = 'M' + (dot_interval * first_episode_number + OFFSET_X_LEFT) + "," + line_y + 'L' + (dot_interval * last_episode_number + OFFSET_X_LEFT - OFFSET_X_RIGHT - DOT_RADIUS) + ',' + line_y;

            if (!IS_IE8) {
                var line = paper.path(path)

                line.node.setAttribute('id', 'joke-' + joke['code']);
                if (joke_code == joke['code']) {
                    line.node.setAttribute('class', 'joke-line joke-' + joke['code'] + ' joke-line-detail');
                } else {
                    line.node.setAttribute('class', 'joke-line joke-' + joke['code']);
                }
                line.node.setAttribute('data-joke', joke['code']);
            }

            // add label
            joke_labels += '<li id="label-' + joke['code'] + '" style="top: ' + line_y + 'px;" data-joke="' + joke['code'] + '"';
            if (joke_code == joke['code']) {
                joke_labels += ' class="joke-label-detail joke-label"';
            } else {
                joke_labels += ' class="joke-label"';
            }
            joke_labels += '>';
            joke_labels += '<a href="' + project_root + 'joke/' + joke['code'] + '/">';
            joke_labels += joke['text'];
            joke_labels += '</a></li>';

            // add header if applicable
            if (i == 0 || (joke['primary_character'] != jokes[i-1]['primary_character'])) {
                joke_headers += '<h4 id="' + group.replace(' ', '-').replace(/\./g, '') + '"class="joke-group-header" style="width: ' + LABEL_WIDTH + 'px; top: ' + line_y + 'px">' + joke['primary_character'] + '</h4>';
            }

            line_y += LINE_INTERVAL;
        }

        line_y += GROUP_INTERVAL;
    }

    joke_labels += '</ul>';
    $viz.append(joke_labels);
    $viz.append(joke_headers);

    height = line_y + OFFSET_Y - GROUP_INTERVAL;
    $viz.height(height);
    $viz.find('#viz-labels').height(height);

    // render season labels
    // loop through episodes and create labels (appended to page when various joke groupings are rendered)
    if (!IS_IE8) {
        for (var e in episodes) {
            var episode = episodes[e];
            var episode_number = episode['number'];
            var episode_episode = episode['episode'];

            if (e == 1 || (episodes[e-1] != undefined && episode['season'] != episodes[e-1]['season'])) {
                var label_x = dot_interval * (episode_number - 1) + DOT_RADIUS;

                season_labels += '<li class="episode-season-number" style="left: ' + label_x + 'px;">';
                season_labels += 'Season ' + episode['season'];
                season_labels += '</li>';

                if (e != 1) { // a dividing line before all seasons after the first
                    var line_x = dot_interval * (episode_number - 1) + OFFSET_X_LEFT + (dot_interval / 2);
                    var path = 'M' + line_x + ',' + 0 + 'L' + line_x + ',' + height;
                    var line = paper.path(path);
                    line.node.setAttribute('class', 'season-line');
                }
            }
        }

        // Render related joke curves
        for (var i = 0; i < connection_data.length; i++) {
            var connection = connection_data[i];
            var joke1_code = connection.joke1_code;
            var joke2_code = connection.joke2_code;
            var episode_number = connection.episode_number;

            joke_code_to_related_jokes_map[joke1_code].push(joke2_code);
            joke_code_to_related_jokes_map[joke2_code].push(joke1_code);

            var from_episode_id = episode_number;
            var to_episode_id = episode_number;

            var from_y = joke_code_to_line_y_map[joke1_code];;
            var from_x = from_episode_id * dot_interval + OFFSET_X_LEFT;

            var to_y = joke_code_to_line_y_map[joke2_code];;
            var to_x = to_episode_id * dot_interval + OFFSET_X_LEFT;

            // Ensure connections are drawn north->south
            if (to_y < from_y) {
                var tmp = from_y;
                from_y = to_y;
                to_y = tmp;
            }

            var control_x1 = from_x + dot_interval;
            var control_x2 = control_x1;

            var control_y1 = from_y + LINE_INTERVAL;
            var control_y2 = to_y - LINE_INTERVAL;

            // Special case for connections that are adjacent
            // Spread out the control points so they don't appear as triangles
            if (control_y2 - control_y1 < LINE_INTERVAL) {
                control_y1 -= LINE_INTERVAL;
                control_y2 += LINE_INTERVAL;
            }

            var path = 'M' + from_x + ',' + from_y + ' C'  + control_x1 + ',' + control_y1 + ' ' + control_x2 + ',' + control_y2 + ' ' + to_x + ',' + to_y;
            var line = paper.path(path);

            line.node.setAttribute('id', 'line-' + joke1_code + '-to-' + joke2_code + '-e' + episode_number);
            line.node.setAttribute('class', 'connection-line joke-' + joke1_code + ' joke-' + joke2_code + ' episode-' + episode_number);
        }

        line_y = OFFSET_Y;

        // Render episode dots
        for (var g in group_order) {
            var group = group_order[g];
            var jokes = joke_data[group];

            // append a set of season labels atop each grouping
            if ($viz.selector == '#viz' || season_labeled == false) {
                $viz.append('<ul class="episode-labels" style="left: ' + (OFFSET_X_LEFT + DOT_RADIUS + 3) + 'px; top: ' + line_y + 'px;">' + season_labels + '</ul>');
                season_labeled = true;
            }

            for (var i = 0; i < jokes.length; i++) {
                var joke = jokes[i];
                var joke_code = joke['code']
                var episodejokes = joke['episodejokes'];
                var joke_primary_character = joke['primary_character'];
                var joke_text = joke['text'];

                for (var j = 0; j < episodejokes.length; j++) {
                    var episodejoke = episodejokes[j];
                    var episode = episodes[episodejoke['episode_number']];
                    var episode_number = episode['number'];
                    var episode_code = episode['code'];
                    var episode_title = episode['title'];
                    var episode_connection = episodejoke['connection'];
                    var episode_details = episodejoke['details'];

                    if (!(episode_number in episode_number_to_jokes_map)) {
                        episode_number_to_jokes_map[episode_number] = [];
                    }

                    episode_number_to_jokes_map[episode_number].push(joke_code);

                    var dot = paper.rect((episode_number * dot_interval) + OFFSET_X_LEFT - DOT_RADIUS / 2, line_y - 8, DOT_RADIUS, 16);
                    var dot_class = 'dot ' + 'joke-type-' + episodejoke['joke_type'];

                    dot.node.setAttribute('class', dot_class);
                    dot.node.setAttribute('data-primary-character', joke_primary_character);
                    dot.node.setAttribute('data-joke', joke_code);
                    dot.node.setAttribute('data-text', joke_text);
                    dot.node.setAttribute('data-episode', episode_code);
                    dot.node.setAttribute('data-episode-number', episode_number);
                    dot.node.setAttribute('data-episode-title', episode_title);
                    if (episode_connection) {
                        dot.node.setAttribute('data-connection', episode_connection);
                    }
                    if (episode_details) {
                        dot.node.setAttribute('data-details', episode_details);
                    }
                }

                line_y += LINE_INTERVAL;
            }

            line_y += GROUP_INTERVAL;
        }
    }

    if (!IS_MOBILE && !IS_IE8) {
        $('.dot').hover(
            function() {
                var $dot = $(this);
                var dot_position = $dot.position();
                var tt_height;

                $tooltip.empty();
                if (svgHasClass($dot,'joke-type-b')) {
                    $tooltip.append('<span class="joke-type">Joke In The Background</span>');
                } else if (svgHasClass($dot,'joke-type-f')) {
                    $tooltip.append('<span class="joke-type">Foreshadowed Joke</span>');
                } else {
                    $tooltip.append('<span class="joke-type">Joke</span>');
                }
                $tooltip.append('<span class="joke-info">' + $dot.data('primary-character') + ': ' + $dot.data('text') + '</span>');
                if ($dot.data('connection')) {
                    $tooltip.append('<span class="related-joke"><strong>Related joke:</strong> ' + $dot.data('connection') + '</span>');
                }
                if ($dot.data('details')) {
                    $tooltip.append('<span class="joke-details"><strong>Details:</strong> ' + $dot.data('details') + '</span>');
                }
                $tooltip.append('<span class="episode-info"><strong>Episode:</strong> &ldquo;' + $dot.data('episode-title') + '&rdquo; (' + $dot.data('episode') + ')</span>');

                tt_height = $tooltip.height();
                tt_width = $tooltip.outerWidth();
                tt_top = dot_position.top - (tt_height / 2);
                tt_left = dot_position.left + (DOT_RADIUS * 2) + DOT_RADIUS;

                if ((tt_left + tt_width) > width) {
                    tt_left = dot_position.left - tt_width - DOT_RADIUS;
                }

                if (!IS_WEBKIT) {
                    tt_left -= $viz.offset().left;
                    tt_top -= $viz.offset().top;
                }

                $tooltip.css('left', tt_left + 'px' );
                $tooltip.css('top', tt_top + 'px' );

                $tooltip.fadeIn('fast');

                highlight_joke_network($dot.data('joke'), $dot.data('episode-number'));
            },
            function() {
                var $dot = $(this);

                $tooltip.fadeOut('fast');

                dehighlight_joke_network($dot.data('joke'), $dot.data('episode-number'));
            }
        ).click(function() {
            window.open( project_root + 'episode/' + $(this).data('episode') + '/#joke-' + $(this).data('joke'),'_self');
        });

        $('.joke-line, .joke-label').hover(
            function(e) {
                var joke_code = $(this).data('joke');
                highlight_joke_network(joke_code);
            },
            function(e) {
                var joke_code = $(this).data('joke');
                dehighlight_joke_network(joke_code);
            }
        );
    }
    $('.joke-line, .joke-label').click(function() {
        window.open( project_root + 'joke/' + $(this).data('joke') + '/','_self');
    });
}

function highlight_joke_network(joke_code, episode_number) {
    var selector = '.connection-line.joke-' + joke_code;

    if (episode_number) {
        selector += '.episode-' + episode_number;
    }

    var connections = $(selector);
    var related_jokes = joke_code_to_related_jokes_map[joke_code];

    for (var c = 0; c < connections.length; c++) {
        var el = connections[c];
        var attr = el.getAttribute('class') + ' highlight';
        el.setAttribute('class', attr);
    }

    for (var j = 0; j < related_jokes.length; j++) {
        var joke_code2 = related_jokes[j];

        if (episode_number) {
            // When we have an episode number, only highlight directly connected joke lines
            if (!_.indexOf(episode_number_to_jokes_map[episode_number], joke_code)) {
                continue;
            }
        }

        var klass = joke_code2 == joke_code ? 'highlight-primary' : 'highlight';
        var el = $('.joke-line.joke-' + joke_code2)[0];
        var attr = el.getAttribute('class') + ' ' + klass;
        el.setAttribute('class', attr);

        $('#label-' + joke_code2).addClass('highlight');
    }

    $('#label-' + joke_code).addClass('highlight');
}

function dehighlight_joke_network(joke_code, episode_number) {
    var selector = '.connection-line.joke-' + joke_code;

    if (episode_number) {
        selector += '.episode-' + episode_number;
    }

    var connections = $(selector);
    var related_jokes = joke_code_to_related_jokes_map[joke_code];

    for (var c = 0; c < connections.length; c++) {
        var el = connections[c];
        var attr = el.getAttribute('class').replace(' highlight', '');
        el.setAttribute('class', attr);
    }

    for (var j = 0; j < related_jokes.length; j++) {
        var joke_code2 = related_jokes[j];
        var klass = joke_code2 == joke_code ? 'highlight-primary' : 'highlight';
        var el = $('.joke-line.joke-' + joke_code2)[0];
        var attr = el.getAttribute('class').replace(' ' + klass, '');
        el.setAttribute('class', attr);

        $('#label-' + joke_code2).removeClass('highlight');
    }

    $('#label-' + joke_code).removeClass('highlight');
}


/*
 * Check if an SVG object has a particular class,
 * since jQuery .hasClass() doesn't work w/ classes applied to SVGs
 */
function svgHasClass(obj,c) {
    var classes = obj.attr('class').split(' ');
    var hasClass = false;

    for (var i = 0; i < classes.length; i ++) {
        if (classes[i] == c) {
            hasClass = true;
            break;
        }
    }
    return hasClass;
}


function resize_viz() {
    var new_width = $('body').width();
    if (new_width != WINDOW_WIDTH || INITIAL_LOAD == false) {
        var $viz = null;
        var joke_code = null;
        WINDOW_WIDTH = new_width;

        // Joke detail page
        if ($body.hasClass('joke-detail')) {
            $viz = $joke_viz;
            joke_code = parseInt($joke_viz.data('joke-code'));
        // Index / full viz page
        } else if ($body.hasClass('viz-index')) {
            $viz = $full_viz;
        }

        if (paper) {
            paper.remove();
            $viz.empty();
        }

        render_viz($viz, group_order, joke_data, connection_data, episodes, joke_code);
        INITIAL_LOAD = true;
    }
}


$(function() {
    $body = $('body');
    $full_viz = $('#viz');
    $joke_viz = $('#joke-viz');
    $tooltip = $('#viz-tooltip');

    // IE8 likes to throw random resize events and redraw everything
    if (!IS_IE8) {
        $(window).resize(resize_viz);
    } else {
        if ($body.hasClass('viz-index')) {
            $('#click-for-details').remove();
            $full_viz.append('<img src="img/full-vis-ie8.png" style="margin-left: ' + (LABEL_WIDTH + OFFSET_X_RIGHT) + 'px;" />');
        }
    }
    resize_viz();
});

