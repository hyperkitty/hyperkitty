===================================
HyperKitty - Archiver for for GNU Mailman v3
===================================

HyperKitty is an open source Django application under development. It aims to provide web interface to access GNU Mailman archives.


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




Installation
============
1. Clone the repository
2. Install all the dependencies using pip install -r requirements.txt
3. Load data into postgresql using kittystore (https://github.com/pypingou/kittystore)
4. python manage.py syncdb
5. python manage.py runserver


License 
========

Copyright (C) 1998-2012 by the Free Software Foundation, Inc.

HyperKitty is free software: you can redistribute it and/or
modify it under the terms of the GNU Lesser General Public License as
published by the Free Software Foundation, version 3 of the License.

HyperKitty is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser
General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with mailman.client. If not, see <http://www.gnu.org/licenses/>.
