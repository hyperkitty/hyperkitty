================
News / Changelog
================

0.1.7
=====
(2014-01-30)

Many significant changes, mostly on:
* The caching system
* The user page
* The front page
* The list overview page


0.1.5
=====
(2013-05-18)

Here are the significant changes since 0.1.4:

* Merge and compress static files (CSS and Javascript)
* Django 1.5 compatibility
* Fixed REST API
* Improved RPM packaging
* Auto-subscribe the user to the list when they reply online
* New login providers: generic OpenID and Fedora
* Improved page loading on long threads: the replies are loaded asynchronously
* Replies are dynamically inserted in the thread view


0.1.4
=====
(2013-02-19)

Here are the significant changes:

* Beginning of RPM packaging
* Improved documentation
* Voting and favoriting is more dynamic (no page reload)
* Better emails display (text is wrapped)
* Replies are sorted by thread
* New logo
* DB schema migration with South
* General style update (Boostream, fluid layout)


0.1 (alpha)
===========
(2012-11-22)

Initial release of HyperKitty.

* login using django user account / browserid / google openid / yahoo openid
* use Twitter Bootstrap for stylesheets
* show basic list info and metrics
* show basic user profile
* Add tags to message threads
