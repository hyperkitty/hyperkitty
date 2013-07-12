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

    git clone https://github.com/hyperkitty/hyperkitty_standalone.git

Second, change the database setting in ``hyperkitty_standalone/settings.py`` to
your preferred database. HyperKitty uses two databases, one to store the metadata
and other to store the emails. Edit this file to reflect the correct database
credentials. The configuration variables are ``DATABASES`` (at the top of the
file) and ``KITTYSTORE_URL`` (at the bottom).

Or better yet, instead of changing the ``settings.py`` file itself, copy the
values you want to change to a file called ``settings_local.py`` and change
them there. It will override the values in ``settings.py`` and will make future
upgrades easier.

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
    python hyperkitty_standalone/manage.py assets build --parse-templates

These static files will be collected in the ``hyperkitty_standalone/static``
directory and served by Apache. You should now be all set. Try accessing
HyperKitty in your web browser.


Connecting to Mailman
=====================

To receive incoming emails from Mailman, you must add the follwing lines to
``mailman.cfg``::

    [archiver.hyperkitty]
    class: hyperkitty.archiver.Archiver
    enable: yes
    configuration: /path/to/hyperkitty_standalone/hyperkitty.cfg

The ``hyperkitty.cfg`` file which path is specified by the ``configuration``
key is an additional HyperKitty-specific configuration file for which an
example is provided. See the included ``hyperkitty_standalone/hyperkitty.cfg``
file.

.. warning::
    The user that Mailman runs under (unually "mailman") must be able to read
    both the ``settings.py`` and ``settings_local.py`` files. Remember that
    those files also contain the database passwords, so make sure the
    permissions are correct. We suggest adding the mailman user to the apache
    group, and only giving this group read access to those files.

After having made these changes, you must restart Mailman. Check its log files
to make sure the emails are correctly archived. You should not see "``Broken
archiver: hyperkitty``" messages.


Initial setup
=============

After installing HyperKitty for the first time, you can populate the database
with some data that may be useful, for example a set of thread categories to
assign to your mailing-list threads. This can be done by running the following
command::

    python hyperkitty_standalone/manage.py loaddata first_start

Thread categories can be edited and added from the Django administration
interface (append ``/admin`` to your base URL).


Upgrading
=========

To upgrade an existing installation of HyperKitty, you need to update the code
base and run the commands that will update the database schemas. Before
updating any of those databases, it is recommanded to shut down the webserver
which serves HyperKitty (Apache HTTPd for example).

There are two main databases in HyperKitty. The one from KittyStore and the one
from HyperKitty itself. To update the KittyStore database, just run::

    kittystore-update -s KITTYSTORE_URL

where "``KITTYSTORE_URL``" is the content of the ``KITTYSTORE_URL`` variable in
``settings.py`` (or ``settings_local.py``). This command may take a long time
to complete, donc interrupt it.

Then, to update the HyperKitty database, run::

    python hyperkitty_standalone/manage.py syncdb
    python hyperkitty_standalone/manage.py migrate hyperkitty

After those commands complete, your database will be updated, you can start
your webserver again, and restart Mailman (to take the KittyStore upgrade into
account).


License
=======

HyperKitty is licensed under the `GPL v3.0`_

.. _GPL v3.0: http://www.gnu.org/licenses/gpl-3.0.html
