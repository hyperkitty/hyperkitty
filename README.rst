===================================
HyperKitty - Archiver for for GNU Mailman v3
===================================

HyperKitty is an open source Django application under development. It aims to provide web interface to access GNU Mailman archives.


Installation
============

1. git clone https://github.com/syst3mw0rm/hyperkitty
2. cd hyperkitty
3. python setup.py develop
4. Clone KittyStore and Load archive data into postgresql using kittystore (https://github.com/pypingou/kittystore)
5. Create symlink kittystore using **ln -s {path-to-kittystore}/kittystore/ kittystore**
6. Install hk-app (https://github.com/syst3mw0rm/hk-app)

Dependencies
============

Hyperkitty dependencies
-----------------------
* Django==1.4 
* URLObject==2.0.2 
* django-gravatar==0.1.0
* django-social-auth==0.7.0
* djangorestframework==0.3.3
* httplib2==0.7.4
* oauth2==1.5.211
* psycopg2==2.4.5
* python-openid==2.2.5
* wsgiref==0.1.2
* yolk==0.4.3


kittystore dependencies
-----------------------
* SQLAlchemy==0.7.8



License 
========

.. _GPL v3.0: http://www.gnu.org/licenses/gpl-3.0.html

HyperKitty is licensed under the `GPL v3.0`_
