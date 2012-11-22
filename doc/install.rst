============
Installation
============

.. note::
    This installation guide covers HyperKitty, the web user interface to access
    GNU Mailman v3 Archives. To install GNU Mailman follow the instructions in
    the documentation: http://packages.python.org/mailman/


Install the code
================

Install the HyperKitty package and its dependencies with the following
commands::

    sudo pip install -r requirements.txt
    sudo python setup.py install


Setup your django project
=========================

You now have installed the necessary packages but you still need to setup the
Django site (project).

First, get the project directory from the source code management system::

    bzr branch bzr://bzr.fedorahosted.org/bzr/hyperkitty/hyperkitty_standalone

Second, change the database setting in ``hyperkitty_standalone/settings.py`` to
your preferred database. HyperKitty uses two databases, one to store the metadata
and other to store the emails. Edit this file to reflect the correct database
credentials. The configuration variables are ``DATABASES`` (at the top of the
file) and ``KITTYSTORE_URL`` (at the bottom).

.. note::
    Detailed information on how to use different database engines can be found
    in the `Django documentation`_.

.. _Django documentation: https://docs.djangoproject.com/en/1.4/ref/settings/#databases


.. Setting up the databases

.. include:: database.rst


Running HyperKitty on Apache with mod_wsgi
==========================================

.. note::
    This guide assumes that you know how to setup a VirtualHost with Apache.
    If you are using SQLite, the ``.db`` file as well as its folder need to be
    writable by the web server.

Edit ``hyperkitty_standalone/hyperkitty.apache.conf`` to point to your source
code location.

Add following line to your apache/httpd configuration file::

    Include "/{path-to-hyperkitty_standalone}/hyperkitty.apache.conf"

And reload Apache. We're almost ready. But you need to collect the static files
from HyperKitty (which resides somewhere on your pythonpath) to be able to
serve them from the site directory. All you have to do is run::

    python hyperkitty_standalone/manage.py collectstatic

These static files will be collected in the ``hyperkitty_standalone/static``
directory and served by Apache. You should now be all set. Try accessing
HyperKitty in your web browser.


Connecting to Mailman
=====================

To receive incoming emails from Mailman, you must add the follwing lines to
``mailman.cfg``::

    [archiver.hyperkitty]
    class: hyperkitty.lib.archiver.Archiver
    enable: yes
    configuration: /path/to/hyperkitty_standalone/hyperkitty.cfg

The ``hyperkitty.cfg`` file which path is specified by the ``configuration``
key is an additional HyperKitty-specific configuration file for which an
example is provided. See the included ``hyperkitty_standalone/hyperkitty.cfg``
file.

After having made these changes, you must restart Mailman. Check its log files
to make sure the emails are correctly archived. You should not see "``Broken
archiver: hyperkitty``" messages.


License
=======

HyperKitty is licensed under the `GPL v3.0`_

.. _GPL v3.0: http://www.gnu.org/licenses/gpl-3.0.html
