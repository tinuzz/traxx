#!/usr/bin/python
#
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

import os
import shutil
import hashlib
import tempfile
import argparse                   # apt-get install python-argparse (for < 2.7)
import mutagen                    # apt-get install python-mutagen
from mutagen.mp3 import MP3
from mutagen.id3 import ID3,TXXX

class mp3hash(object):

    fname = ''
    fsum = ''
    storehash = False  # Do not store hash in ID3 by default

    def md5sum(self, filename):
        md5 = hashlib.md5()
        with open(filename,'rb') as f:
            for chunk in iter(lambda: f.read(256*md5.block_size), b''):
                 md5.update(chunk)
        return md5.hexdigest()

    def make_tmpfile(self, fname):
        tmpdir = tempfile.gettempdir()
        tmpfile = os.path.join (tmpdir,os.path.basename(fname))
        shutil.copy (fname, tmpdir)
        return tmpfile

    def mp3hash(self, fname):
        self.fname = fname
        tmpfile = self.make_tmpfile (fname)
        mp3 = MP3 (tmpfile)
        try:
            mp3.delete ()
            mp3.save ()
        except:
            pass
        self.fsum = self.md5sum (tmpfile)
        os.remove(tmpfile)
        return (self.fsum, fname)

    def writemd5(self):
        if self.fname and self.fsum:
            try:
                mp3 = ID3 (self.fname)
                mp3.add(TXXX(encoding=3, desc=u'MD5', text=[self.fsum]))
                mp3.save()
            except mutagen.id3.ID3NoHeaderError:
                print "No Header Error: %s" % self.fname
                pass
            except IOError:
                print "Couldn't write header."
                pass

    def process_options(self):
        parser = argparse.ArgumentParser(description='mp3hash - calculate a hash of an mp3, excluding any ID3 tags, optionally storing the hash in an ID3 tag',
            formatter_class=lambda prog: argparse.ArgumentDefaultsHelpFormatter(prog,max_help_position=36))
        parser.add_argument('-s', '--store', action='store_true', dest='storehash', help='store the calculted hash in the ID3 tag')
        parser.add_argument('filename', help='the file to calculate a hash for')
        args = parser.parse_args()
        self.storehash  = args.storehash
        self.fname = args.filename

if __name__ == "__main__":

    h = mp3hash ()
    h.process_options()

    try:
        hh = h.mp3hash (h.fname)
        print "%s  %s" % (hh[0], hh[1])
    except IOError, e:
        print "Could not open file: %s" % e

    if h.storehash:
        h.writemd5()
