============
Installation
============

.. note::
    This installation guide covers HyperKitty, the web user interfaceaccess GNU Mailman v3 
    Archives. To install GNU Mailman follow the instructions in the documentation:
    http://packages.python.org/mailman/


Install Dependencies
====================

sudo pip install -r requirements.txt


Install HyperKitty
=================

sudo python manage.py install


Setup your django project
=========================

Since you have now installed the necessary packages to run HyperKitty, it's
time to setup your Django site.

First, get the project directory from launchpad:

::

    $ bzr branch bzr://bzr.fedorahosted.org/bzr/hyperkitty/hk-app

Second, change the database setting in ``postorius_standalone/settings.py`` to
your preferred database. HyperKitty uses two databases, one to store the metadata
and other to store mails. Edit this file to reflect the correct database credential.

.. note::
    Detailed information on how to use different database engines can be found
    in the `Django documentation`_.

.. _Django documentation: https://docs.djangoproject.com/en/1.4/ref/settings/#databases

Third, prepare the database:

::

    $ cd hk-app
    $ python manage.py syncdb
    $ cd ..

This will create the ``.db file`` (if you are using SQLite) and will setup all the
necessary db tables. You will also be prompted to create a superuser which
will act as an admin account for HyperKitty


Running the development server
==============================

The quickest way to run HyperKitty is to just start the development server:

::

    $ cd hk-app
    $ python manage.py runserver


.. warning::
    You should use the development server only locally. While it's possible to
    make your site publicly available using the dev server, you should never
    do that in a production environment.


Running HyperKitty on Apache with mod_wsgi
=========================================

.. note::
    This guide assumes that you know how to setup a VirtualHost with Apache.
    If you are using SQLite, the ``.db`` file as well as its folder need to be
    writable by the web server.

Edit ``apache/apache_django_wsgi.conf`` to point to your source code location.

Add following line to your apache/httpd configuration file

:: 
Include "/{path-to-hk-app}/apache/apache_django_wsgi.conf"


We're almost ready. But you need to collect the static files from HyperKitty
(which resides somewhere on your pythonpath) to be able to serve them from the
site directory. All you have to do is to change into the
``hk-app`` directory and run:

::

    $ python manage.py collectstatic
