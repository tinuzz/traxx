// Global variables
var
	// A flag indicating whether the playlist is currently being updated
	updating = false,

	// A flag indicating whether a search request is cuurently in progress
	searching = false,

	// A flag indicating whether an 'idle' request is currently running
	idling = false,

	// A timeout ID used for delayed restarting of the 'idle' process
	timeout,

	// A timeout ID used for delaying the incremental search function
	inputtimer,

	// A gloabl record of the last chosen sort field
	lastsort = 'trackno',

	// A flag indicating whether the playlist should scroll to the current item
	doscroll = false;

// Get a list of subdirectories for a given path with AJAX
function html_dirlist(path) {
	$.get($SCRIPT_ROOT + "/ajax/html_dirlist/?p="+path, function(data) {
		$('#dirlist').html(data);
		show_breadcrumbs(path);
		add_dir_click(path);
	});
}

// Initialize the 'Play all songs' link
function add_dir_click(path) {
	$('a[data-dir]').click(function() {
		mpd_add_dir(path, $(this));
		return false;
	});
}

// Get a list of songs for a given path with AJAX, using the given sort field
function html_songlist(path, sort) {

	var url = $SCRIPT_ROOT + "/ajax/html_songlist/?p="+path;
	if (typeof sort !== 'undefined') {
		url += "&s=" + sort;
		lastsort = sort;
	}

	// Show a spinner while loading the songlist
	$("#songlist").html('&nbsp;  &nbsp; &nbsp;Loading...').spin({ lines: 8, length: 2, width: 2, radius: 3, left: 0 });

	// Get and process the songlist data
	$.get(url, function(data) {
		$('#songlist').html(data);

		// Initialize the song links
		$('a[data-song]').click(function() {
			songid = $(this).attr('data-song');
			i = $(this).find('i[class="icon-play"]');
			if (i.length == 1) {
				// This is the case where the 'play now' icon was clicked
				mpd_add(songid, $(this), true);
			}
			else {
				mpd_add(songid, $(this));
			}
			return false;
		});

		init_songinfo();

	});
	folder_jpg(path);
}

// Load 'folder.jpg' and initialize a click handler for the image
function folder_jpg(path) {
	$('#folderjpg').html('<img id="folderjpgimg" src="' + $SCRIPT_ROOT + '/folder.jpg?p=' + path + '" />');

	// On click, load the image in a modal div, set the size and show the modal
	$('#folderjpgimg').click(function() {
		src=$(this).attr('src');
		$('#imagemodal').css('width', '430px');
		$('#imageinmodal').attr('src', src).on('load', function () {
			$(this).css('height', '400px');
		});
		$('#imagemodal').modal();
	});
}

// Initialize the 'Song info' click handler to show an AJAX-primed clickover
function init_songinfo() {
	$('.icon-info-sign').clickover({beforeShow: function() {
			element = this
			songid = this.options.info;
			$.ajax({
				url: $SCRIPT_ROOT + "/ajax/html_songinfo/?i=" + songid,
				success: function(result) {
					element.options.content = result;
				},
				async: false
			});
		},
		html: true,
		title: 'Song info',
		placement: 'left'
	});
}

// Show the breadcrumbs naviation in the designated div
function show_breadcrumbs(currentdir) {
	comp = decodeURIComponent(currentdir).split('/');
	str = '<i class="icon-chevron-right"></i> <b><a data-pjax href="' + $SCRIPT_ROOT + '/">Start</a> <i class="icon-chevron-right"></i> ';
	link = encodeURIComponent('/');
	$.each(comp, function(k,v) {
		if (v != '') {
			link += encodeURIComponent(v + '/');
			str += '<a data-pjax href="' + $SCRIPT_ROOT + '/?p=' + link + '">' + v + '</a> <i class="icon-chevron-right"></i> ';
		}
	});
	str += '</b>';
	$('#breadcrumbs').html(str);
}

/* not used ?
function infopop (element,data) {
		options = { 'content': data }
		options['placement'] = 'right';
		options['trigger'] = 'manual';
		options['html'] = true;
		options['title'] = 'Song info';
		$(element).clickover(options);
		$(element).clickover('show');
}
*/

// Show a popover near the given element, with given content
function pop( element, data, placement, hide ) {
		var do_hide = 2000;
		var options = { 'content': data }
		if (typeof placement != 'undefined') {
			options['placement'] = placement
		}
		if (typeof hide != 'undefined') {
			do_hide = hide
		}
		$(element).popover(options);
		$(element).popover('show');

		if (do_hide > 0) {
			window.setTimeout(function() { $(element).popover('destroy'); }, do_hide);
		}
}

// Call 'mpd_add_dir' for given dir
function mpd_add_dir(dir, element) {
	$.get($SCRIPT_ROOT + "/ajax/mpd_add_dir/?p=" + dir + '&s=' + lastsort, function(data) {
		pop(element, data);
	});
}

// Call 'mpd_add' for given song ID, optionally telling the server to play it immediately
function mpd_add(id, element, playnow) {
	param = '';
	if (typeof(playnow) != 'undefined') {
		if (playnow) {
			param = '&playnow=true';
		}
	}

	$.get($SCRIPT_ROOT + "/ajax/mpd_add/?i=" + id + param, function(data) {
		pop(element, data);
	});
}

function mpd_cmd(cmd, element, options) {
	url = $SCRIPT_ROOT + "/ajax/mpd_" + cmd + "/";
	if ('i' in options) {
		url += "?i=" + options.i
	}
	$.get(url, function(data) {
		if ('placement' in options) {
			pop(element, data, options.placement);
		}
		else {
			pop(element, data);
		}
		if (!(cmd == 'enableoutput' || cmd == 'disableoutput')) {
			load_playlist_if_not_updating();
		}
	});
}

function load_playlist() {

	updating = true;
	$('#playlistmodal').find('.modal-body').load($SCRIPT_ROOT + "/ajax/html_playlist/", function () {

		if (doscroll) {
			// Scroll down to show the current song near the top of the list
			if (song > 3) {
				// First set the scrollbar at the top, to get the correct position
				$('#mpdplaylist').scrollTop(0);
				var scroll = parseInt($('#pos' + (song - 3)).position().top);
				$('#mpdplaylist').scrollTop(scroll);
			}
			doscroll = false;
		}

		// set css on the cells, because the .error class on the row loses
		// the battle with Bootstrap's .table-striped
		$('.error').children('td').css('background-color', '#f2dede');

		// Click handler for the 'delete' icon
		$('a[data-action="delete"]').click(function() {
			mpd_cmd('delete', $('#mpdplaylist'), {i: $(this).attr('data-ppos'), placement: 'top'})
		});

		// Click handler for the 'move up' icon
		$('a[data-action="moveup"]').click(function() {
			mpd_cmd('moveup', $('#mpdplaylist'), {i: $(this).attr('data-ppos'), placement: 'top'})
		});

		// Click handler for the 'move down' icon
		$('a[data-action="movedown"]').click(function() {
			mpd_cmd('movedown', $('#mpdplaylist'), {i: $(this).attr('data-ppos'), placement: 'top'})
		});

		// Click handler for the 'requeue' icon
		$('a[data-action="requeue"]').click(function() {
			mpd_cmd('requeue', $('#mpdplaylist'), {i: $(this).attr('data-ppos'), placement: 'top'})
		});

		// Click handler for playlist entries
		$('a[data-pos]').click(function() {
			mpd_cmd('skipto', $('#mpdstatus'), {i: $(this).attr('data-pos'), placement: 'top'})
		});

		// Start MPD idle request
		do_idle();
		updating = false;
	});
}

function load_playlist_if_not_updating () {
  if (!updating) {
    load_playlist ();
  }
}

function show_playlist() {
		$('#playlistmodal').modal();
		idle = true;
		doscroll = true;
		load_playlist_if_not_updating();
}

// Send an 'idle' command to the player and handle the result
// If the result indicates the playlist has changed, then
// reload it.
function do_idle () {
	vis = $('#playlistmodal').css('display');
	if (vis == 'block') {
		if (! idling) {
			idling = true

			// This should use $.ajax, also defining an error handler. The error
			// handler should set idling = false, otherwise this function will
			// not recover from a failed request, like a webserver restart.
			$.getJSON($SCRIPT_ROOT + "/ajax/json_mpd_idle/", function (data) {
				//lines = data.split("|");
				$.each(data, function (index, value) {
					if (value == "playlist" || value == "player") {
						load_playlist_if_not_updating ();
					}
				});
				vis = $('#playlistmodal').css('display');
				if (vis == 'block') {
					// delay a little
					timeout = setTimeout('do_idle', 300);
				}
				else {
					clearTimeout(timeout);
				}
				idling = false
			});
		}
	}
}

function handle_search (sort) {
	if (searching) { return; }
	var q = $('#search').val()
	if (q == '') { return; }
	var url = $SCRIPT_ROOT + "/ajax/html_song_search/?q="+encodeURIComponent(q);
	if (typeof sort !== 'undefined') {
		url += "&s=" + sort;
		lastsort = sort;
	}
	// Put an identifiying div in the dirlist, so the sort button can find out which function to call
	$('#dirlist').html('<div id="currentdiv" style="display: none" data-currentdir="SEARCHRESULT"></div>');
	$('#songlist').load(url, function () {
		searching = false;
		$('a[data-song]').click(function() {
			songid = $(this).attr('data-song');
			mpd_add(songid, $(this));
			return false;
		});
		init_songinfo();
	});
}

function init_playlist_button() {
	$('#showplaylistmodal').click(function() {
		show_playlist()
		return false;
	});
	$('#playlistmodal').on('show', function () {
		$(this).css({'margin-left': function () {
				return -($(this).width() / 2);
			}
		});
	});
}

function init_streams_button() {
	$('#showstreams').click(function() {
		$('#streamsmodal').modal();
		$('#streamsmodal').find('.modal-body').load($SCRIPT_ROOT + "/ajax/html_streams/", function () {
			$('.addstream').click(function() {
				streamid = $(this).attr('data-stream');
				mpd_cmd('addstream', $(this), {'i': streamid});
			});
		});
	});
}

function init_outputs_button() {
	$('#showoutputs').click(function() {
		$('#outputsmodal').modal();
		$('#outputsmodal').find('.modal-body').load($SCRIPT_ROOT + "/ajax/html_outputs/", function () {
  		$('.switch')['bootstrapSwitch']();

			$('div[data-outputid]').on('switch-change', function(e, data) {
				id = $(this).attr('data-outputid');
				if (data.value) {
					cmd='enableoutput';
				}
				else {
					cmd='disableoutput';
				}
				mpd_cmd(cmd, $(this), {'i': id, 'placement': 'left'});
			})
		});
	});
}

function init_search() {
	/* Near-real-time search. On input, wait 600ms for more input before doing search */
	$('#search').on('input', function() {
		if (inputtimer) {
			clearTimeout(inputtimer);
		}
		inputtimer = setTimeout(function () { handle_search(); }, 600);
	});

	$('#searchbutton').click(function() {
		handle_search();
	});
}

function init_sort_button_links() {
	$('a[data-sort]').click(function() {
		sortcol = $(this).attr('data-sort');
		if ($('#currentdiv').attr('data-currentdir') == 'SEARCHRESULT') {
			handle_search(sortcol);
		}
		else {
			html_songlist(currentdir, sortcol);
		}
		// Hide the sort menu
		$('#sortbutton').dropdown('toggle');
		return false;
	});
}

function init_player_control_buttons() {
	$.each(['play','stop','pause','prev','next'], function(index,value) {
		$('#mpd_'+ value).click(function(e) {
			mpd_cmd(value, $(this), {'placement': 'top'});
			load_playlist_if_not_updating()
			return false;
		});
	});

	$('#mpd_clear').click(function(e) {
		if (confirm('Clear entire playlist. Are you sure?')) {
			mpd_cmd('clear', $('#mpdplaylist'), {'placement': 'top'});
		}
		return false;
	});

	$('#mpd_cleanup').click(function(e) {
		if (confirm('Clean up old songs from playlist. Are you sure?')) {
			mpd_cmd('cleanup', $('#mpdplaylist'), {'placement': 'top'});
		}
		return false;
	});
}

function init_pjax() {
	// Use PJAX for #dirlist div
	$(document).pjax('a[data-pjax]', '#dirlist');

	// When dirlist is loaded, initialize related elements
	$(document).on('pjax:end', function(e) {
		currentdir = $('#currentdiv').attr('data-currentdir');
		add_dir_click(currentdir);
		show_breadcrumbs(currentdir);
		html_songlist(currentdir);
	})
}

jQuery(document).ready(function($) {

	// Initialize the AJAX containers using the path from the global 'initpath'
	// variable, which is set from the index.html template. It's already
	// urlencoded.
	html_dirlist(initpath);
	html_songlist(initpath);

	// Initilize UI event handlers
	init_playlist_button();
	init_streams_button();
	init_outputs_button();
	init_search();
	init_sort_button_links();
	init_player_control_buttons();
	init_pjax();

});
