# -*- coding: utf-8 -*-
import os
import sys
import urllib
from pprint import pprint,pformat

import traxxjax

from flask import Flask, render_template, request, Response, redirect, url_for, Markup
app = Flask(__name__)

app.debug = True

@app.route('/')
def index_html():

    pp = request.args.get('p')
    si = request.args.get('i')
    if request.headers.get('X-PJAX'):
        if pp is not None:
            return handle_ajax('html_dirlist', request)
        if si is not None:
            return handle_ajax('mpd_add', request)

    # No PJAX
    if si is not None:
        handle_ajax('mpd_add', request)
    if pp is None:
        pp = ''
    os.stat_float_times(False)
    fname = os.path.join(os.path.dirname(__file__), 'static/site.js')
    mtime = os.stat(fname).st_mtime
    return render_template('index.html', js_mtime=mtime, path=pp, pjax=False)

@app.route('/ajax/<fn>/')
def handle_ajax(fn, req=False):
    afn = 'ajax_' + fn
    a = traxxjax.Ajax()
    afn = getattr(a, afn, a.default_response)
    if req != False:
        return afn(req.args)
    else:
        return afn(request.args)

@app.route('/file/<int:fileid>')
def serve_file(fileid):
    a = traxxjax.Ajax()
    return a.serve_file(fileid)

@app.route('/pl/<int:fileid>/playlist.pls')
def playlist_pls(fileid):
    a = traxxjax.Ajax()
    return a.playlist(fileid, 'pls')

@app.route('/pl/<int:fileid>/playlist.m3u')
def playlist_m3u(fileid):
    a = traxxjax.Ajax()
    return a.playlist(fileid, 'm3u')

@app.route('/playlist.pls')
def dir_playlist_pls():
    a = traxxjax.Ajax()
    return a.dir_playlist(request.args, 'pls')

@app.route('/playlist.m3u')
def dir_playlist_m3u():
    a = traxxjax.Ajax()
    return a.dir_playlist(request.args, 'm3u')

@app.route('/folder.jpg')
def folder_jpg():
    a = traxxjax.Ajax()
    return a.folder_jpg(request.args)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.template_filter('urlencode')
def urlencode_filter(s):
    if type(s) == 'Markup':
        s = s.unescape()
    s = s.encode('utf8')
    s = urllib.quote(s, '')
    return Markup(s)

@app.template_filter('humansize')
def humansize_filter(s):
    unit = 'B'
    if s > 1024:
        s = s // 1024
        unit = 'kB'
    if s > 1024:
        s = s / 1024.0
        unit = 'MB'
    return "%.2f %s" % (s, unit)

@app.template_filter('humanlength')
def humanlength_filter(s):
    s = int(s)
    hrs = 0
    mins = s // 60
    secs = s % 60
    if mins >= 60:
        hrs = mins // 60
        mins = mins % 60
    if hrs > 0:
        return "%d:%02d:%02d" % (hrs, mins, secs)
    else:
        return "%d:%02d" % (mins, secs)

@app.template_filter('humanbps')
def humanbps_filter(s):
    s = int(s) // 1000
    return "%d kbps" % s

if __name__ == '__main__':
    app.run(host='0.0.0.0')
