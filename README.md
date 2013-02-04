musiclib
========

Some programs for maintaining a database of mp3s:

* mp3hash.py

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

* mp3hash_all

Mp3hash_all uses mp3hash.py to recursively tag all mp3s in a directory tree.

	usage: mp3hash_all [-h] directory

	mp3hash_all - recursively traverse a directory, hashing all found mp3s and
	store the hash in the ID3 tag of the file

	positional arguments:
		directory   the directory to scan for mp3s

	optional arguments:
		-h, --help  show this help message and exit

