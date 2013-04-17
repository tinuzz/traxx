# -*- coding: utf-8 -*-

from pprint import pprint, pformat
import os
import json
import re
from math import ceil
from sqlalchemy import *     # apt-get install python-sqlalchemy
from sqlalchemy.sql import func, or_
from flask import Response, render_template, abort, send_file
import traxx.mpdplay as mpdplay
from socket import error as SocketError
from mpd import (MPDClient, CommandError)
import collections
import urllib
from datetime import datetime

class Ajax (object):

    def __init__(self):
        self.read_config()
        self.db_connect()
        if not hasattr(self.config, 'numsongs'):
            self.config['numsongs'] = 150
        if not hasattr(self.config, 'plformat'):
            self.config['plformat'] = 'm3u'
            #self.config['plformat'] = 'pls'

    def read_config(self):
        cfgfile =  os.path.join(os.path.dirname(__file__), 'traxx.conf')
        fp = open(cfgfile)
        strconfig = fp.read()
        fp.close()
        self.config = json.loads(strconfig, object_pairs_hook=collections.OrderedDict)
        self.con_id = {'host': self.config['mpdhost'], 'port': self.config['mpdport'] }

    def db_connect(self):
        self.db_engine = create_engine(self.config['dbengine'] + '://' + self.config['dbuser'] + ':' + \
            self.config['dbpass'] + '@' + self.config['dbhost'] + '/' + self.config['db'] + '?charset=utf8')
        self.db_metadata = MetaData(self.db_engine)
        self.db_songtable = Table(self.config['dbtable'], self.db_metadata, autoload=True)
        self.dbc = self.db_engine.connect()

    def mpd_connect(self):
        self.client = MPDClient()
        self.client.connect(host=self.config['mpdhost'], port=self.config['mpdport'])

    def get_order(self, sort):
        cols = ['artist', 'title', 'filename', 'length', 'size']
        if sort in cols:
            cols.remove(sort)
            order = [sort] + cols
        else:
            order = [cast(self.db_songtable.c.trackno, Integer)]
            order += cols
        return order

    def get_songs(self, args, path):
        # Sanitize physical dir
        pdir = os.path.realpath(re.sub (r"/+", "/", self.config['rootdir'] + '/' + path)).rstrip('/')
        sort = args.get('s', 'trackno')
        order = self.get_order(sort);
        sql = select([self.db_songtable], self.db_songtable.c.path == pdir, order_by=order)
        return self.dbc.execute(sql).fetchall()

    def get_state(self):
        status = self.client.status()
        action = 'unknown'
        if status['state'] == 'play':
            action = 'started'
        elif status['state'] == 'stop':
            action = 'is stopped'
        elif status['state'] == 'pause':
            action = 'is paused'
        return action

    def fix_pl(self, item):
        item['col1'] = ''
        item['col2'] = ''
        if 'artist' in item:
            item['col1'] = unicode(item['artist'], 'utf-8')
        elif 'name' in item:
            item['col1'] = unicode(item['name'], 'utf-8')
        else:
            item['col1'] = unicode(item['file'], 'utf-8')

        if 'title' in item:
            item['col2'] = unicode(item['title'], 'utf-8')

        if 'time' not in item:
            item['time'] = '0'
        return item

    def ajax_html_dirlist(self, args):

        p = args.get('p', '')
        p = urllib.unquote_plus(p)

        # Sanitize path
        path = re.sub(r"/+", "/", p.rstrip('/')).rstrip('#')

        # Sanitize physical dir
        pdir = os.path.realpath(re.sub (r"/+", "/", self.config['rootdir'] + '/' + path)) + '/'
        # The result has to start with the configured rootdir
        if pdir[0:len(self.config['rootdir'])] != self.config['rootdir']:
            pdir = os.path.realpath(self.config['rootdir']) + '/'

        sql = select([func.substring_index(func.replace(self.db_songtable.c.path, pdir, '' ), '/', 1).label('npath')]).\
            where(func.substring_index(func.replace(self.db_songtable.c.path, pdir, '' ), '/', 1) != '').distinct().order_by('npath')
        rows = self.dbc.execute(sql).fetchall()

        plroute = 'dir_playlist_%s' % self.config['plformat']
        if len(rows) == 0:
            return render_template('playdir.html', path=path, plroute=plroute)
        else:
            numpercol = ceil (len(rows) / 2.0)
            return render_template('dirlist.html', rows=rows, numpercol=numpercol, path=path)

    def ajax_html_songlist(self, args):
        p = args.get('p', '')
        p = urllib.unquote_plus(p)
        path = re.sub(r"/+", "/", p.rstrip('/')).rstrip('#')
        rows = self.get_songs(args, path)

        if len(rows):
            plroute = 'playlist_%s' % self.config['plformat']
            return render_template('songlist.html', rows=rows, path=path, plroute=plroute)
        else:
            return "No songs<br /><br />"

    def ajax_html_song_search(self, args):
        q = args.get('q', '')
        if q == '':
            return 'No result'
        sort = args.get('s', 'artist')
        order = self.get_order(sort);
        qq = '%%%s%%' % q
        sql = select([self.db_songtable], or_(self.db_songtable.c.artist.like(qq), self.db_songtable.c.title.like(qq)), order_by=order).limit(self.config['numsongs'])
        rows = self.dbc.execute(sql).fetchall()
        plroute = 'playlist_%s' % self.config['plformat']
        return render_template('songlist.html', rows=rows, path='/', plroute=plroute)

    def ajax_html_songinfo(self, args):
        try:
            id = int(args.get('i'))
        except ValueError:
            return "Error"

        sql = select([self.db_songtable],  self.db_songtable.c.id == id)
        row = self.dbc.execute(sql).fetchall()[0]
        humanmtime = datetime.fromtimestamp(row['mtime'])
        return render_template('songinfo.html', row=row, humanmtime=humanmtime, rowtxt=pformat(row), sql=str(sql))

    def ajax_mpd_add(self, args):
        try:
            id = int(args.get('i'))
        except ValueError:
            return

        playnow = args.get('playnow', 'false')

        sql = select([self.db_songtable], self.db_songtable.c.id == id)
        row = self.dbc.execute(sql).fetchall()[0]
        fname = os.path.join(row['path'], row['filename']).encode('utf-8')
        try:
            pos,num  = mpdplay.main([fname], self.con_id)
        except SocketError:
            return "Error: cannot connect to MPD"

        if playnow == 'true':
            self.mpd_connect()
            self.client.play(int(pos)-1)

        txt = "Song"
        if num > 1:
            txt = "%d songs" % num
        return "%s added at position %d" % (txt, int(pos))

    def ajax_mpd_add_dir(self, args):
        try:
            path = args.get('p')
        except ValueError:
            return
        path = re.sub(ur"/+", "/", path.rstrip('/'))
        rows = self.get_songs(args, path)
        files = [ os.path.join(r['path'], r['filename']) for r in rows ]

        try:
            pos,num  = mpdplay.main(files, self.con_id)
        except SocketError:
            return "Error: cannot connect to MPD"

        return "%d songs added at position %d" % (int(num), int(pos))

    def ajax_mpd_addstream(self, args):
        try:
            i = args.get('i')
        except ValueError:
            return "Missing parameter"
        try:
            url=self.config['streams'][i]['url'];
        except KeyError:
            return "Unknown stream"
        self.mpd_connect()
        self.client.add(url)
        status = self.client.status()
        if status['state'] == 'stop':
            self.client.play(int(status['playlistlength'])-1)
        return "Stream added at position %s" % status['playlistlength']

    def ajax_mpd_delete(self, args):
        try:
            i = int(args.get('i'))
        except ValueError:
            return "Unknown song"
        self.mpd_connect()
        self.client.delete(i)
        return "Song deleted"

    def ajax_mpd_skipto(self, args):
        try:
            i = int(args.get('i'))
        except ValueError:
            return "Unknown song"
        self.mpd_connect()
        self.client.play(i)
        st = self.get_state()
        return "Playback %s" % st

    def ajax_mpd_play(self, args):
        self.mpd_connect()
        self.client.play()
        st = self.get_state()
        return "Playback %s" % st

    def ajax_mpd_stop(self, args):
        self.mpd_connect()
        self.client.stop()
        st = self.get_state()
        return "Playback %s" % st

    def ajax_mpd_pause(self, args):
        self.mpd_connect()
        self.client.pause()
        st = self.get_state()
        return "Playback %s" % st

    def ajax_mpd_prev(self, args):
        self.mpd_connect()
        self.client.previous()
        return "Skipping back"

    def ajax_mpd_next(self, args):
        self.mpd_connect()
        self.client.next()
        return "Skipping forward"

    def ajax_mpd_clear(self, args):
        self.mpd_connect()
        status = self.client.status()
        self.client.clear()
        return "Playlist cleared"

    def ajax_mpd_cleanup(self, args):
        self.mpd_connect()
        status = self.client.status()
        if 'song' in status:
            n = int(status['song'])
            for _ in range(n):
                self.client.delete(0)
        else:
            self.client.clear()
        return "Playlist cleaned up"

    def ajax_mpd_moveup(self, args):
        try:
            i = int(args.get('i'))
        except ValueError:
            return "Unknown song"
        if i <= 0:
            return "Can't move first song up"
        self.mpd_connect()
        status = self.client.status()
        last = int(status['playlistlength']) - 1
        if i > last:
            return "Unknown song"
        self.client.move(i, i-1)
        return "Move up"

    def ajax_mpd_movedown(self, args):
        try:
            i = int(args.get('i'))
        except ValueError:
            return "Unknown song"
        if i < 0:
            return "Unknown song"
        self.mpd_connect()
        status = self.client.status()
        last = int(status['playlistlength']) - 1
        if i >= last:
            return "Can't move last song down"
        self.client.move(i, i+1)
        return "Move down"

    def ajax_mpd_requeue(self, args):
        try:
            i = int(args.get('i'))
        except ValueError:
            return "Unknown song"
        if i < 0:
            return "Unknown song"
        self.mpd_connect()
        status = self.client.status()
        last = int(status['playlistlength']) - 1
        self.client.move(i, last)
        return "Requeued"

    def ajax_mpd_enableoutput(self, args):
        try:
            i = int(args.get('i'))
        except ValueError:
            return "Unknown output"
        if i < 0:
            return "Unknown output"
        self.mpd_connect()
        self.client.enableoutput(i)
        return "Output enabled"

    def ajax_mpd_disableoutput(self, args):
        try:
            i = int(args.get('i'))
        except ValueError:
            return "Unknown output"
        if i < 0:
            return "Unknown output"
        self.mpd_connect()
        self.client.disableoutput(i)
        return "Output disabled"

    def ajax_html_playlist(self, args):
        self.mpd_connect()
        pl = self.client.playlistinfo()
        map(self.fix_pl, pl)

        status = self.client.status()
        if 'song' not in status:
            status['song'] = -1
        mpd_status = 'unknown'
        if status['state'] == 'play':
            mpd_status = 'playing song %d' % (int(status['song']) + 1)
        if status['state'] == 'stop':
            mpd_status = 'stopped'
        if status['state'] == 'pause':
            mpd_status = 'paused'
        return render_template('playlist.html', pl=pl, mpd_status=mpd_status, song=status['song'])

    def ajax_html_streams(self, args):
        return render_template('streams.html', streams=self.config['streams'])

    def ajax_html_outputs(self, args):
        self.mpd_connect()
        outputs = self.client.outputs()
        return render_template('outputs.html', outputs=outputs)

    def ajax_json_mpd_idle(self, args):
        self.mpd_connect()
        #idle = self.client.idle('playlist')
        idle = self.client.idle()
        return json.dumps(idle)

    def serve_file(self, fileid):
        sql = select([self.db_songtable], self.db_songtable.c.id == fileid)
        rows = self.dbc.execute(sql).fetchall()
        if len(rows):
            row=rows[0]
            fname = os.path.join(row['path'], row['filename']).encode('utf-8')
            if os.path.exists(fname):
                return send_file(fname, as_attachment=True)
        abort(404)

    def playlist(self, fileid, fmt):
        sql = select([self.db_songtable], self.db_songtable.c.id == fileid)
        rows = self.dbc.execute(sql).fetchall()
        if fmt == 'm3u':
            return Response(render_template('playlist.m3u', rows=rows), mimetype='audio/x-mpegurl')
        if fmt == 'pls':
            return Response(render_template('playlist.pls', rows=rows, num=len(rows)), mimetype='audio/x-scpls')
        abort(404)

    def dir_playlist(self, args, fmt):
        try:
            path = args.get('p')
        except ValueError:
            return
        path = re.sub(r"/+", "/", path.rstrip('/'))
        rows = self.get_songs(args, path)
        if fmt == 'm3u':
            return Response(render_template('playlist.m3u', rows=rows), mimetype='audio/x-mpegurl')
        if fmt == 'pls':
            return Response(render_template('playlist.pls', rows=rows, num=len(rows)), mimetype='audio/x-scpls')
        abort(404)

    def folder_jpg(self, args):
        try:
            path = args.get('p')
        except ValueError:
            return
        path = re.sub(r"/+", "/", path.rstrip('/')).rstrip('#')
        pdir = os.path.realpath(re.sub (r"/+", "/", self.config['rootdir'] + '/' + path))
        # The result has to start with the configured rootdir
        if pdir[0:len(self.config['rootdir'])] != self.config['rootdir']:
            abort(404)

        fname = os.path.join(pdir, 'folder.jpg').encode('utf-8')
        if os.path.exists(fname):
            return send_file(fname)
        return send_file(os.path.join(os.path.dirname(__file__), 'static', 'no_image.jpg'))
        abort(404)

    # This method gets called if the requested AJAX function
    # does not exist as a method on this class
    def default_response(self, args):
        abort(404)
