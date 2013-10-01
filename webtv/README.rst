WebTV / MSN TV
==============

Script to grab http://www.webtv.net . See http://archiveteam.org/index.php?title=MSN_TV for more details.

Requires Python 2 and Wget 1.14.

* Create the ``warc`` and ``log`` directories.
* Place your ``urls.txt`` the same directory.
* ``touch STOP`` to gracefully stop.

Bugs
====

If the supplied URL is too long to be included as part of the filename, it may error depending on the filesystem.
