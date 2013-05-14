var EPISODE_COUNT = 53;
var JOKE_COUNT = 10;

var DOT_RADIUS = 5;
var OFFSET_X = DOT_RADIUS;
var OFFSET_Y = DOT_RADIUS;

var $viz = null;
var viz_div = null;
var paper = null;

$(function() {
    $viz = $('#viz');
    viz_div = $viz[0];

    if (!Raphael.svg) {
        alert('No SVG support');
    } else {
        var width = $viz.width();
        var height = $viz.height();

        var paper = new Raphael(viz_div, width, height);

        var line_interval = (height - (OFFSET_Y * 2)) / JOKE_COUNT;
        var dot_interval = (width - (OFFSET_X * 2)) / EPISODE_COUNT;

        // Render joke lines
        for (var i = 0; i < JOKE_COUNT; i++) {
            var line_y = (i * line_interval) + OFFSET_Y;

            var path = 'M' + (0 + OFFSET_X) + "," + line_y + 'L' + (width - (OFFSET_X * 2)) + ',' + line_y;
            var line = paper.path(path)

            line.node.setAttribute('id', 'joke-' + i);
            line.node.setAttribute('class', 'joke-line');
        }

        // Render related joke curves
        var from_joke = 3;
        var from_episode = 2;

        var to_joke = 9;
        var to_episode = 2;

        var from_x = from_episode * dot_interval + OFFSET_X;
        var from_y = from_joke * line_interval + OFFSET_Y;

        var to_x = to_episode * dot_interval + OFFSET_X;
        var to_y = to_joke * line_interval + OFFSET_Y;

        var control_x1 = from_x - (dot_interval * 0.75);
        var control_y1 = from_y + line_interval;

        var control_x2 = control_x1;
        var control_y2 = to_y - line_interval;

        var path = 'M' + from_x + ',' + from_y + ' C'  + control_x1 + ',' + control_y1 + ' ' + control_x2 + ',' + control_y2 + ' ' + to_x + ',' + to_y;
        var line = paper.path(path);

        line.node.setAttribute('id', 'connection-j' + from_joke + 'e' + from_episode + '-j' + to_joke + 'e' + to_episode);
        line.node.setAttribute('class', 'connection-line');


        // Render episode dots
        for (var i = 0; i < JOKE_COUNT; i++) {
            var line_y = i * line_interval + OFFSET_Y;

            for (var j = 0; j < EPISODE_COUNT; j++) {
                var dot = paper.circle((j * dot_interval) + OFFSET_X, line_y, 5); 

                dot.node.setAttribute('id', 'joke-' + i + '-episode-' + j);
                dot.node.setAttribute('class', 'dot episode-dot');
            }
        }
    }
});

