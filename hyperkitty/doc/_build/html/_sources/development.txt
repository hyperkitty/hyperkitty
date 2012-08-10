===========
Development
===========


Contribution
========
Hang out on IRC and ask questions on #mailman or join the mailing list mailman-developers@python.org

Get the development version up and running:
	1. bzr branch bzr://bzr.fedorahosted.org/bzr/hyperkitty/hyperkitty
 	2. cd hyperkitty
 	3. python setup.py develop ( this command may require sudo privileges)
 	4. Clone the stand alone hk-app, bzr branch bzr://bzr.fedorahosted.org/bzr/hyperkitty/hk-app
 	5. cd hk-app
 	6. python manage.py syncdb
 	7. python manage.py runserver
	(you may need to load data in your local machine using kittystore to get it running)
 	
Testing
=======

python manage.py test hyperkitty

All test modules reside in the ``hyperkitty/hyperkitty/tests`` directory
and this is where you should put your own tests, too. To make the django test
runner find your tests, make sure to add them to the folder's ``__init__.py``:
