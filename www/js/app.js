var EPISODE_COUNT = 53;

var DOT_RADIUS = 5;
var LABEL_WIDTH = 200;
var GROUP_LABEL_HEIGHT = 16;
var LINE_INTERVAL = 15;
var GROUP_INTERVAL = 33;
var OFFSET_X_RIGHT = DOT_RADIUS + 3;
var OFFSET_X_LEFT = OFFSET_X_RIGHT + LABEL_WIDTH;
var OFFSET_Y = DOT_RADIUS + 3 + GROUP_LABEL_HEIGHT;

var $viz = null;
var viz_div = null;
var paper = null;
var $tooltip = null;

var group_order;
var joke_data;
var connection_data;
var episodes;

var joke_code_to_index_map = {};
var joke_code_to_line_y_map = {};

/*
 * Loop through data, render the big graphic
 */
function render_joke_viz() {
    if (!Raphael.svg) {
        alert('No SVG support');
    } else {
        var width = $viz.width();
        var height = $viz.height();

        var episode_labels = '';
        var joke_labels = '<ul id="vis-labels" style="width: ' + LABEL_WIDTH + 'px;">';
        var headers = '';
        var paper = new Raphael(viz_div, width, height);

        var line_y = OFFSET_Y;
        var dot_interval = (width - (OFFSET_X_LEFT + OFFSET_X_RIGHT)) / EPISODE_COUNT;

        // Render joke lines
        for (var g in group_order) {
            var group = group_order[g];
            var jokes = joke_data[group];

            for (var i = 0; i < jokes.length; i++) {
                var joke = jokes[i];
                joke_code_to_index_map[joke['code']] = i;
                joke_code_to_line_y_map[joke['code']] = line_y;

                var episodejokes = joke['episodejokes'];
                var first_episode_number = episodejokes[0]['episode_number'];
                var last_episode_number = EPISODE_COUNT + 1; // +1 to make sure it goes off the side

                var path = 'M' + (dot_interval * first_episode_number + OFFSET_X_LEFT) + "," + line_y + 'L' + (dot_interval * (last_episode_number + 1) + OFFSET_X_LEFT - (OFFSET_X_RIGHT * 2)) + ',' + line_y;
                var line = paper.path(path)

                line.node.setAttribute('id', 'joke-' + joke['code']);
                line.node.setAttribute('class', 'joke-line');
                line.node.setAttribute('data-joke', joke['code']);
                
                // add label
                joke_labels += '<li id="label-' + joke['code'] + '" class="joke-label" style="top: ' + line_y + 'px;">';
                joke_labels += '<a href="joke-' + joke['code'] + '.html">';
                joke_labels += joke['text'];
                joke_labels += '</a></li>';
                
                // add header if applicable
                if (i == 0 || (joke['primary_character'] != jokes[i-1]['primary_character'])) {
                    headers += '<h4 class="joke-group-header" style="width: ' + LABEL_WIDTH + 'px; top: ' + line_y + 'px">' + joke['primary_character'] + '</h4>';
                }

                line_y += LINE_INTERVAL;
            }
        
            line_y += GROUP_INTERVAL;
        }
        joke_labels += '</ul>';
        $viz.append(joke_labels);
        $viz.append(headers);
        
        // render episode labels
        episode_labels += '<ul class="episode-labels" style="left: ' + (OFFSET_X_LEFT + DOT_RADIUS + 3) + 'px;">';
        for (var e in episodes) {
            var episode = episodes[e];
            var episode_number = episode['number'];
            var episode_episode = episode['episode'];
            console.log(episode);

            if (e == 1 || (episodes[e-1] != undefined && episode['season'] != episodes[e-1]['season'])) {
                episode_labels += '<li class="episode-season-number">Season ' + episode['season'];
                
                if (e != 1) { // a dividing line before all seasons after the first
                    var line_x = dot_interval * (episode_number - 1) + OFFSET_X_LEFT + (dot_interval / 2);
                    var path = 'M' + line_x + ',' + 0 + 'L' + line_x + ',' + height;
                    var line = paper.path(path);
                    line.node.setAttribute('class', 'season-line');
                }
            }
            episode_labels += '<li class="episode-number" style="width: ' + dot_interval + 'px;" id="' + episode['code'] + '" data-episode="' + episode['episode'] + '" data-id="' + episode['id'] + '" data-season="' + episode['season'] + '" + data-episode-title="' + episode['title'] + '">';
            episode_labels += episode['episode'];
            episode_labels += '</li>';
        }
        episode_labels += '</ul>';
        $viz.append(episode_labels);
        
        // Render related joke curves
        for (var i = 0; i < connection_data.length; i++) {
            var connection = connection_data[i];
            var joke1_code = connection.joke1_code;
            var joke2_code = connection.joke2_code;
            var episode_number = connection.episode_number;

            var from_joke_id = joke_code_to_index_map[joke1_code];
            var from_episode_id = episode_number;

            var to_joke_id = joke_code_to_index_map[joke2_code];
            var to_episode_id = episode_number;

            var from_y = joke_code_to_line_y_map[joke1_code];;
            var from_x = from_episode_id * dot_interval + OFFSET_X_LEFT;

            var to_y = joke_code_to_line_y_map[joke2_code];;
            var to_x = to_episode_id * dot_interval + OFFSET_X_LEFT;

            // Ensure connections are drawn north->south
            if (to_y < from_y) {
                var tmp = from_y;
                from_y = to_y;
                to_y = from_y;
            }

            var control_x1 = from_x + dot_interval;
            var control_y1 = from_y + LINE_INTERVAL;

            var control_x2 = control_x1;
            var control_y2 = to_y - LINE_INTERVAL;

            var path = 'M' + from_x + ',' + from_y + ' C'  + control_x1 + ',' + control_y1 + ' ' + control_x2 + ',' + control_y2 + ' ' + to_x + ',' + to_y;
            var line = paper.path(path);

            line.node.setAttribute('id', 'line-' + joke1_code + '-to-' + joke2_code + '-e' + episode_number);
            line.node.setAttribute('class', 'connection-line');
        }

        line_y = OFFSET_Y;

        // Render episode dots
        for (var g in group_order) {
            var group = group_order[g];
            var jokes = joke_data[group];

            for (var i = 0; i < jokes.length; i++) {
                var joke = jokes[i];
                var episodejokes = joke['episodejokes'];
                var joke_primary_character = joke['primary_character'];
                var joke_text = joke['text'];

                for (var j = 0; j < episodejokes.length; j++) {
                    var episodejoke = episodejokes[j];
                    var episode = episodes[episodejoke['episode_number']];
                    var episode_number = episode['number'];
                    var episode_code = episode['code'];
                    var episode_title = episode['title'];

                    var dot = paper.circle((episode_number * dot_interval) + OFFSET_X_LEFT, line_y, 5); 

                    dot.node.setAttribute('id', 'episodejoke-' + episode_number);

                    var dot_class = 'dot ' + 'joke-type-' + episodejoke['joke_type'];  
                
                    dot.node.setAttribute('class', dot_class);
                    dot.node.setAttribute('data-primary-character', joke_primary_character);
                    dot.node.setAttribute('data-text', joke_text);
                    dot.node.setAttribute('data-episode', episode_code);
                    dot.node.setAttribute('data-episode-title', episode_title);
                }

                line_y += LINE_INTERVAL;
            }

            line_y += GROUP_INTERVAL;
        }
        
        $('.dot').hover(
            function() {
                var dot = $(this);
                var dot_position = dot.position();
                
                $tooltip.empty();
                $tooltip.append('<strong>Episode: ' + dot.data('episode-title') + ' (' + dot.data('episode') + ')</strong><br />');
                $tooltip.append('<strong>' + dot.data('primary-character') + '</strong>: ' + dot.data('text'));
                
                if (svgHasClass(dot,'joke-type-b')) {
                    $tooltip.append(' <em>(in background)</em>');
                } else if (svgHasClass(dot,'joke-type-f')) {
                    $tooltip.append(' <em>(foreshadowed)</em>');
                }
                $tooltip.css('left', (dot_position.left + (DOT_RADIUS * 2) + 3) + 'px' );
                $tooltip.css('top', (dot_position.top + (DOT_RADIUS * 2) + 3) + 'px' );
                $tooltip.fadeIn('fast');
            },
            function() {
                $tooltip.fadeOut('fast');
            }
        ).click(function() {
            window.open('episode-' + $(this).data('episode') + '.html');
        });
        
        $('.joke-line').hover(
            function() {
                // make all jokes on the line also highlight
            },
            function() {
                // remove highlight from all jokes on the line
            }
        ).click(function() {
            window.open('joke-' + $(this).data('joke') + '.html');
        });
    } 
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


$(function() {
    $viz = $('#viz');
    viz_div = $viz[0];
    $tooltip = $('#viz-tooltip');

    $.getJSON('live-data/jokes.json', function(data) {
        group_order = data['group_order'];
        joke_data = data['jokes'];
        connection_data = data['connections'];
        episodes = data['episodes'];

        render_joke_viz();
    });
});

