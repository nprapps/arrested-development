var EPISODE_COUNT = 53;

var DOT_RADIUS = 5;
var LABEL_WIDTH = 275;
var OFFSET_X_RIGHT = DOT_RADIUS + 3;
var OFFSET_X_LEFT = OFFSET_X_RIGHT + LABEL_WIDTH;
var OFFSET_Y = DOT_RADIUS + 3;

var $viz = null;
var viz_div = null;
var paper = null;
var $tooltip = null;

var joke_data;
var joke_code_to_index_map = {};
var connection_data;

function render_joke_viz() {
    if (!Raphael.svg) {
        alert('No SVG support');
    } else {
        var width = $viz.width();
        var height = $viz.height();

        var labels = '<ul id="vis-labels" style="width: ' + LABEL_WIDTH + 'px;">';
        var paper = new Raphael(viz_div, width, height);

        var joke_count = joke_data.length;
        var line_interval = (height - (OFFSET_Y * 2)) / joke_count;
        var dot_interval = (width - (OFFSET_X_LEFT + OFFSET_X_RIGHT)) / EPISODE_COUNT;

        // Render joke lines
        for (var i = 0; i < joke_count; i++) {
            var joke = joke_data[i];
            joke_code_to_index_map[joke['code']] = i;

            var episodejokes = joke['episodejokes'];
            var first_episode_number = episodejokes[0]['episode_data']['number'];
            var last_episode_number = episodejokes[episodejokes.length - 1]['episode_data']['number'];

            var line_y = (i * line_interval) + OFFSET_Y;

            var path = 'M' + (dot_interval * first_episode_number + OFFSET_X_LEFT) + "," + line_y + 'L' + (dot_interval * (last_episode_number + 1) + OFFSET_X_LEFT - (OFFSET_X_RIGHT * 2)) + ',' + line_y;
            var line = paper.path(path)

            line.node.setAttribute('id', 'joke-' + joke['code']);
            line.node.setAttribute('class', 'joke-line');
            
            // add label
            labels += '<li id="label-' + joke['code'] + '" class="joke-label" style="top: ' + line_y + 'px;"><strong>' + joke['primary_character'] + '</strong>: ' + joke['text'] + '</li>';
        }

        labels += '</ul>';
        $viz.append(labels);

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

            var from_y = from_joke_id * line_interval + OFFSET_Y;
            var from_x = from_episode_id * dot_interval + OFFSET_X_LEFT;

            var to_y = to_joke_id * line_interval + OFFSET_Y;
            var to_x = to_episode_id * dot_interval + OFFSET_X_LEFT;

            // Ensure connections are drawn north->south
            if (to_y < from_y) {
                var tmp = from_y;
                from_y = to_y;
                to_y = from_y;
            }

            var control_x1 = from_x - dot_interval;
            var control_y1 = from_y + line_interval;

            var control_x2 = control_x1;
            var control_y2 = to_y - line_interval;

            var path = 'M' + from_x + ',' + from_y + ' C'  + control_x1 + ',' + control_y1 + ' ' + control_x2 + ',' + control_y2 + ' ' + to_x + ',' + to_y;
            var line = paper.path(path);

            line.node.setAttribute('id', 'line-' + joke1_code + '-to-' + joke2_code + '-e' + episode_number);
            line.node.setAttribute('class', 'connection-line');
        }

        // Render episode dots
        for (var i = 0; i < joke_count; i++) {
            var joke = joke_data[i];
            var episodejokes = joke['episodejokes'];
            var joke_primary_character = joke['primary_character'];
            var joke_text = joke['text'];

            var line_y = i * line_interval + OFFSET_Y;

            for (var j = 0; j < episodejokes.length; j++) {
                var episodejoke = episodejokes[j];
                var episode_number = episodejoke['episode_data']['number'];
                var episode_code = episodejoke['episode_data']['code'];
                var episode_title = episodejoke['episode_data']['title'];

                var dot = paper.circle((episode_number * dot_interval) + OFFSET_X_LEFT, line_y, 5); 

                dot.node.setAttribute('id', 'episodejoke-' + episode_number);

                var dot_class = 'dot ' + 'joke-type-' + episodejoke['joke_type'];  
            
                dot.node.setAttribute('class', dot_class);
                dot.node.setAttribute('data-primary-character', joke_primary_character);
                dot.node.setAttribute('data-text', joke_text);
                dot.node.setAttribute('data-episode', episode_code);
                dot.node.setAttribute('data-episode-title', episode_title);
            }
        }
        
        $('.dot').hover(
            function() {
                var dot = $(this);
                var dot_position = dot.position();
                var dot_class = dot.attr('class').split(' ');
                $tooltip.empty();
                $tooltip.append('<strong>Episode: ' + dot.data('episode-title') + ' (' + dot.data('episode') + ')</strong><br />');
                $tooltip.append('<strong>' + dot.data('primary-character') + '</strong>: ' + dot.data('text'));
                if (dot_class[1] == 'joke-type-b') {
                    $tooltip.append(' <em>(in background)</em>');
                } else if (dot_class[1] == 'joke-type-f') {
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
    } 
}

$(function() {
    $viz = $('#viz');
    viz_div = $viz[0];
    $tooltip = $('#viz-tooltip');

    $.getJSON('live-data/jokes.json', function(data) {
        joke_data = data['jokes'];
        connection_data = data['connections'];

        render_joke_viz();
    });
});

