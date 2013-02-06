musiclib
========

Some programs for maintaining a database of mp3s:

mp3hash.py
----------

A small Python program / module for calculating a MD5 hash of an mp3 file.
This hash can be used to identify a file by its musical content, i.e. any
present ID3 tags will not influence the hash. This way, the hash can be
used to detect duplicate songs, even when their tags are different.
The calculated hash can optionally be stored inside the mp3 as a TXXX tag.

	usage: mp3hash.py [-h] [-s] filename

	mp3hash - calculate a hash of an mp3, excluding any ID3 tags, optionally
	storing the hash in an ID3 tag

	positional arguments:
		filename     the file to calculate a hash for

	optional arguments:
		-h, --help   show this help message and exit
		-s, --store  store the calculted hash in the ID3 tag (default: False)

It can also be used as a module from another python program:

	import mp3hash
	h = mp3hash.mp3hash ()
	md5 = h.mp3hash (filename)[0]

Known limitation: it cannot create a new ID3 tag, so saving the MD5 hash
to a file that doesn't already have a tag will fail.

mp3hash_all
-----------

Mp3hash_all uses mp3hash.py to recursively tag all mp3s in a directory tree.

	usage: mp3hash_all [-h] directory

	mp3hash_all - recursively traverse a directory, hashing all found mp3s and
	store the hash in the ID3 tag of the file

	positional arguments:
		directory   the directory to scan for mp3s

	optional arguments:
		-h, --help  show this help message and exit

mindexd
-------

Mindexd is a daemon for keeping a music database up to date. It basically
does two things:

- do an initial full scan of the root directory, adding all the mp3 files it
  finds to the database
- after the full scan, it monitors the root directory for changes and updates
  the database accordingly

It has only been tested with MySQL, but since it utilizes SQLAlchemy for all
atabase operations, it should be easy to port to PostgreSQL, for example.

It uses several external Python modules:
- sqlalchemy for database access
- mutagen    for reading ID3 tags and other music properties
- daemon     for daemonizing itself into the background
- pyinotify  for monitoring the music library
- argparse   for parsing command line arguments (external to Python < 2.7)
- mp3hash    (see above) for creating ID3-independent hashes of mp3 files

Here's how it's used:

	usage: mindexd [-h] [-D] [-f] [-m] [-H <hostname>] [-u <username>]
				 [-p <password>] [-n <database>] [-l <file>]
				 [--loglevel <level>] rootdir

	Music Indexing Daemon

	positional arguments:
		rootdir                             the directory to index and monitor

	optional arguments:
		-h, --help                          show this help message and exit
		-D, --daemonize                     run mindexd in the background (default: False)
		-f, --full                          do a full directory scan at startup (default: False)
		-m, --md5                           write MD5 checksum to ID3 (default: False)
		-H <hostname>, --dbhost <hostname>  database server (default: localhost)
		-u <username>, --dbuser <username>  database user (default: musiclib)
		-p <password>, --dbpass <password>  database password (default: None)
		-n <database>, --dbname <database>  database name (default: musiclib)
		-l <file>, --logfile <file>         logfile (default: /tmp/mindexd.log)
		--loglevel <level>                  loglevel, valid levels are
													<debug|info|warning|error|critical> (default: info)

Getting started
---------------

* Create a MySQL database. The default name is 'musiclib', but you can name it
  anything you want.
* Add the songtable to the database, from the provided SQL file.

	mysql -u <user> musiclib < musiclib-mysql.sql

* If your mp3 collection is large, perform an initial scan in the foreground.
  This may take a while. Add '-n <dbname>' if your database is not called
  'musiclib'.

	mindexd -u <user> </path/to/musicdir>

* Now start mindexd in the background to monitor you music collection and keep
  the database up to date.

	mindexd -D -u <user> </path/to/musicdir>

Try adding files to your collection, moving files around or editing ID3 tags,
and see your changes updated in your database within seconds.


License
-------

All software in this project is licensed under the Apache License, version 2.0.
A copy of the license can be found in the 'COPYING' file and on the web [1].

* [6] <http://www.apache.org/licenses/LICENSE-2.0>

