#!/usr/bin/python

#   Copyright 2013 Martijn Grendelman <m@rtijn.net>
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

"""
mpdplay - a command line utility that adds arbitrary files to an MPD playlist

It needs 'python-mpd' [1] to communicate with MPD.

This program basically does the following, given one or more filenames as
command line arguments:
- check if the filename is indeed an existing file
- if the file is a .m3u playlist file, expand its contents
- for each song file (either from the command line or from a m3u file),
  create a symlink in MUSICDIR, which should be set to your MPD's music_directory
- update MPD's database
- add all the processed songs to MPD's playlist
- if MPD is not playing, start playback on the first added song

Some remarks:

- Setting MUSICDIR to a directory below your MPD's music directory, while
  perfectly possible from MPD's point of view, is not yet supported. Adding
  the song to the playlist would fail, because this program doesn't know
  which portion of the MUSCIDIR to prepend to the filename.
- The program is not very chatty, it will only report fatal errors. It will
  silently ignore non-existent files.

[1] http://pypi.python.org/pypi/python-mpd/
"""

import os
import sys
import time

#from pprint import pprint
from mpd import (MPDClient, CommandError)    # apt-get install python-mpd
from socket import error as SocketError

HOST = 'localhost'
PORT = '6600'
PASSWORD = False
MUSICDIR = '/var/lib/mpd/music'   # Your MPD music_directory

CON_ID = {'host':HOST, 'port':PORT}

client = False

def still_updating(client):
    assert client != False
    status=client.status()
    if 'updating_db' in status:
        return True
    else:
        return False

def get_playlist_length(client):
    assert client != False
    status=client.status()
    return int(status['playlistlength'])

def is_playing(client):
    assert client != False
    status=client.status()
    return status['state'] == 'play'

def make_link(filename):
    r = os.path.realpath(filename.strip())
    if os.path.exists(r):
        f = os.path.basename(r)
        l = "%s/%s" % (MUSICDIR, f)
        if os.path.islink(l):
            try:
                os.remove(l)
            except OSError:
                return False
        os.symlink(r, l)
        return f
    else:
        return False

def process_m3u(filename):
    names = []
    if os.path.exists(filename):
        with open(filename) as m3u:
            songs = m3u.readlines()
        for f in songs:
            n = make_link(f)
            if n:
                names.append(n)
    return names

def all_links(files):
    names = []
    for f in files:
        if os.path.splitext(f)[1] == '.m3u':
            names += process_m3u(f)
        else:
            n = make_link(f)
            if n:
                names.append(n)
    return names

def main(files, con_id=None, password=None):

    if len(files) == 0:
        return

    # First, connect to MPD. If that doesn't work, there is no use in
    # creating symlinks or doing anything else

    client = MPDClient()
    client.connect(**(con_id or CON_ID))

    if password or PASSWORD:
        mpdAuth(client, password or PASSWORD)

    # Process the command line arguments and create symlinks
    names = all_links(files)

    # if a DB update is in progress, wait for it to finish
    while still_updating(client):
        pass

    # Update the database
    client.update()

    # Wait for the database update to finish
    while still_updating(client):
        pass

    # Get the position of the first song we're going to add
    # Pos is 0-based, so no need to add 1
    pos = get_playlist_length(client);

    # Add song(s)
    for n in names:
        client.add(n)

    # Start playing if necessary
    if not is_playing(client):
        client.play(pos)

    # Clean up
    client.disconnect()

    return (pos + 1, len(names))

def cli(files):
    try:
        main(files)
    except SocketError:
        print "Cannot connect to MPD."
        sys.exit(1)

# Script starts here
if __name__ == "__main__":
    files = sys.argv[1:]
    cli(files)
