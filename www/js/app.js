var EPISODE_COUNT = 53;

var DOT_RADIUS = 5;
var OFFSET_X = DOT_RADIUS;
var OFFSET_Y = DOT_RADIUS;

var $viz = null;
var viz_div = null;
var paper = null;

var joke_data;
var connection_data;

function render_joke_viz() {
    if (!Raphael.svg) {
        alert('No SVG support');
    } else {
        var width = $viz.width();
        var height = $viz.height();

        var paper = new Raphael(viz_div, width, height);

        var line_interval = (height - (OFFSET_Y * 2)) / joke_data.length;
        var dot_interval = (width - (OFFSET_X * 2)) / EPISODE_COUNT;

        // Render joke lines
        for (var i = 0; i < joke_data.length; i++) {
            var joke = joke_data[i];
            var episodejokes = joke['episodejokes'];
            var first_episode_number = episodejokes[0]['episode_data']['number'];
            var last_episode_number = episodejokes[episodejokes.length - 1]['episode_data']['number'];

            var line_y = (i * line_interval) + OFFSET_Y;

            var path = 'M' + (dot_interval * first_episode_number + OFFSET_X) + "," + line_y + 'L' + (dot_interval * (last_episode_number + 1) - (OFFSET_X * 2)) + ',' + line_y;
            var line = paper.path(path)

            line.node.setAttribute('id', 'joke-' + joke['code']);
            line.node.setAttribute('class', 'joke-line');
        }

        // Render related joke curves
        for (var i = 0; i < connection_data.length; i++) {
            var connection = connection_data[i];
            var joke1_code = connection.joke1_code;
            var joke2_code = connection.joke2_code;
            var episode_number = connection.episode_number;

            var from_joke_id = joke1_code - 1;
            var from_episode_id = episode_number;

            var to_joke_id = joke2_code - 1
            var to_episode_id = episode_number;

            var from_y = from_joke_id * line_interval + OFFSET_Y;
            var from_x = from_episode_id * dot_interval + OFFSET_X;

            var to_y = to_joke_id * line_interval + OFFSET_Y;
            var to_x = to_episode_id * dot_interval + OFFSET_X;

            var control_x1 = from_x - (dot_interval * 0.75);
            var control_y1 = from_y + line_interval;

            var control_x2 = control_x1;
            var control_y2 = to_y - line_interval;

            var path = 'M' + from_x + ',' + from_y + ' C'  + control_x1 + ',' + control_y1 + ' ' + control_x2 + ',' + control_y2 + ' ' + to_x + ',' + to_y;
            var line = paper.path(path);

            line.node.setAttribute('id', 'line-' + joke1_code + '-to-' + joke2_code + '-e' + episode_number);
            line.node.setAttribute('class', 'connection-line');
        }

        // Render episode dots
        for (var i = 0; i < joke_data.length; i++) {
            var joke = joke_data[i];
            var episodejokes = joke['episodejokes'];

            var line_y = i * line_interval + OFFSET_Y;

            for (var j = 0; j < episodejokes.length; j++) {
                var episodejoke = episodejokes[j];
                var episode_number = episodejoke['episode_data']['number'];

                var dot = paper.circle((episode_number * dot_interval) + OFFSET_X, line_y, 5); 

                dot.node.setAttribute('id', 'episodejoke-' + episode_number);

                var dot_class = 'dot ' + 'joke-type-' + episodejoke['joke_type'];  
            
                dot.node.setAttribute('class', dot_class);
            }
        }
    } 
}

$(function() {
    $viz = $('#viz');
    viz_div = $viz[0];

    $.getJSON('live-data/jokes.json', function(data) {
        joke_data = data['jokes'];
        connection_data = data['connections'];

        render_joke_viz();
    });
});

