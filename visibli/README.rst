Visibli
=======

Scripts to grab visibli/sharedby URL shortcodes.

Requires

* Python 3
* HTTP proxy listening to 8123 proxied to Tor SOCKS proxy. 
  * Polipo proxy http://www.pps.univ-paris-diderot.fr/~jch/software/polipo/tor.html
* A text file ``user-agents.txt`` of web browser user agents

See http://archiveteam.org/index.php?title=URLTeam for details.


Visibli Hex
+++++++++++

Visibli's old share shortener

It uses urls like links.visibli.com/links/fbc5fa

charset: 0123456789abcdef


Visibli
+++++++

Visibli's (now SharedBy) new shortener

It uses urls like:

* links.visibli.com/share/AHbpFG
* vsb.li/AHbpFG
* links.sharedby.co/share/AHbpFG
* sharedby.co/AHbpFG
* archive_team_and_urlteam_is_the_best.sharedby.co/AHbpFG
* shrd.by/AHbpFG

charset: 0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ
