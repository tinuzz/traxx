musiclib
========

Some programs for maintaining a database of mp3s:

mindexd
-------

Mindexd is a daemon for keeping a music database up to date. It basically
does two things:

- do an initial full recursive scan of the root directory, adding all the mp3 files it
  finds to the database
- after the full scan, it monitors the root directory for changes and updates
  the database accordingly

It has only been tested with MySQL, but since it utilizes SQLAlchemy for all
database operations, it should be easy to port to PostgreSQL, for example.

It uses several external Python modules:
- sqlalchemy for database access
- mutagen    for reading ID3 tags and other music properties
- daemon     for daemonizing itself into the background
- pyinotify  for monitoring the music library
- argparse   for parsing command line arguments (external to Python < 2.7)
- mp3hash    (see below) for creating ID3-independent hashes of mp3 files

Here's how it's used:

	usage: mindexd [-h] [-D] [-f] [-c] [-m] [-H <hostname>] [-u <username>]
	               [-p <password>] [-n <database>] [-l <file>] [--loglevel <level>]
	               rootdir
	
	Music Indexing Daemon
	
	positional arguments:
	  rootdir                             the directory to index and monitor
	
	optional arguments:
	  -h, --help                          show this help message and exit
	  -D, --daemonize                     run mindexd in the background (default: False)
	  -f, --full                          do a full directory scan at startup (default: False)
	  -c, --clean                         after full scan, clean up unseen files from database (slow). This option does not
	                                      do anything if -f is not specified. (default: False)
	  -m, --md5                           write MD5 checksum to ID3 (default: False)
	  -H <hostname>, --dbhost <hostname>  database server (default: localhost)
	  -u <username>, --dbuser <username>  database user (default: musiclib)
	  -p <password>, --dbpass <password>  database password (default: None)
	  -n <database>, --dbname <database>  database name (default: musiclib)
	  -l <file>, --logfile <file>         logfile (default: /tmp/mindexd.log)
	  --loglevel <level>                  loglevel, valid levels are <debug|info|warning|error|critical> (default: info)
	
	For security, the database password can also be given by setting it in the DBPASS environment variable. The --dbpass
	option takes precendence over the environment variable.

See 'getting started' below for more information.

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

Getting started
---------------

* Create a MySQL database. The default name is 'musiclib', but you can name it
  anything you want.
* Add the songtable to the database, from the provided SQL file.

	mysql -u &lt;user&gt; musiclib &lt; musiclib-mysql.sql

* If your mp3 collection is large, perform an initial scan in the foreground.
  This may take a while. Add '-n &lt;dbname&gt;' if your database is not called
  'musiclib'.

	DBPASS=&lt;yourpassword&gt; mindexd --full -u &lt;user&gt; &lt;/path/to/musicdir&gt;

* Now start mindexd in the background to monitor you music collection and keep
  the database up to date.

	DBPASS=&lt;yourpassword&gt; mindexd --daemonize -u &lt;user&gt; &lt;/path/to/musicdir&gt;

Try adding files to your collection, moving files around or editing ID3 tags,
and see your changes updated in your database within seconds.

If somehow, after some time, changes to your music library have not been processed
by mindexd, you may want to re-run the full scan.

* To do a quick rescan, only adding newly found files and updating changed
  files before going back to monitoring your collection, combine the options
  above:

	DBPASS=&lt;yourpassword&gt; mindexd --full --daemonize -u &lt;user&gt; &lt;/path/to/musicdir&gt;

* To do a full scan + cleanup, which removes files from the database that are
  no longer found in your collection, run mindexd with the '--clean' option:

	DBPASS=&lt;yourpassword&gt; mindexd --full --clean --daemonize -u &lt;user&gt; &lt;/path/to/musicdir&gt;


Database support
----------------

Mindexd has only been developed and tested with MySQL. However, since
SQLAlchemy is used for all database access, it should be easy to port to other
databases, like PostgreSQL. To my knowledge, mindexd does not use any
database-specific statements, except perhaps for 'func.now()'.

License
-------

All software in this project is licensed under the Apache License, version 2.0.
A copy of the license can be found in the 'COPYING' file and on the web [1].

* [1] <http://www.apache.org/licenses/LICENSE-2.0>

