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

    sudo python setup.py install

You will also need to install Node.js and LESS (version >= 1.5) using your package
manager or the project's installation documentation. If you are using Fedora 20, you
can just run ``yum install nodejs-less``. If you are using an earlier version,
you can install the correct version of LESS via rpm: http://pkgs.org/download/nodejs-less

It is however recommended to use Virtualenv to install HyperKitty, even for a
non-development setup (production). Check out :doc:`the development
documentation <development>` for details.


Setup your django project
=========================

You now have installed the necessary packages but you still need to setup the
Django site (project).

First, get the project directory from the source code management system::

    git clone https://github.com/hyperkitty/hyperkitty_standalone.git

Second, change the database setting in ``hyperkitty_standalone/settings.py`` to
your preferred database. Edit this file to reflect the correct database
credentials, the configuration variable is ``DATABASES`` (at the top of the
file).

Or better yet, instead of changing the ``settings.py`` file itself, copy the
values you want to change to a file called ``settings_local.py`` and change
them there. It will override the values in ``settings.py`` and will make future
upgrades easier.

.. note::
    Detailed information on how to use different database engines can be found
    in the `Django documentation`_.

.. _Django documentation: https://docs.djangoproject.com/en/1.6/ref/settings/#databases


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

    django-admin collectstatic --pythonpath hyperkitty_standalone --settings settings
    django-admin compress --pythonpath hyperkitty_standalone --settings settings

.. note::
    Your ``django-admin`` command may be called ``django-admin.py`` depending
    on your installation method.

These static files will be collected in the ``hyperkitty_standalone/static``
directory and served by Apache. You should now be all set. Try accessing
HyperKitty in your web browser.


Connecting to Mailman
=====================

To receive incoming emails from Mailman, you must install the
`mailman-hyperkitty`_ module available on PyPI in Mailman's virtualenv, and
then add the following lines to ``mailman.cfg``::

    [archiver.hyperkitty]
    class: mailman_hyperkitty.Archiver
    enable: yes
    configuration: /path/to/hyperkitty_standalone/hyperkitty.cfg

An `example of the hyperkitty.cfg file`_ is shipped with the `mailman-hyperkitty`_ package.
You must set the URL to your HyperKitty installation in that file.
It is also highly recommanded to change the API secret key and in the
``MAILMAN_ARCHIVER_KEY`` variable in ``settings.py`` (or
``settings_local.py``).

.. _mailman-hyperkitty: http://pypi.python.org/pypi/mailman-hyperkitty
.. _`example of the hyperkitty.cfg file`: https://github.com/hyperkitty/mailman-hyperkitty/blob/master/mailman-hyperkitty.cfg

After having made these changes, you must restart Mailman. Check its log files
to make sure the emails are correctly archived. You should not see "``Broken
archiver: hyperkitty``" messages.


Initial setup
=============

After installing HyperKitty for the first time, you can populate the database
with some data that may be useful, for example a set of thread categories to
assign to your mailing-list threads. This can be done by running the following
command::

    django-admin loaddata --pythonpath hyperkitty_standalone --settings settings first_start

Thread categories can be edited and added from the Django administration
interface (append ``/admin`` to your base URL).


Upgrading
=========

To upgrade an existing installation of HyperKitty, you need to update the code
base and run the commands that will update the database schemas. Before
updating any of those databases, it is recommended to shut down the webserver
which serves HyperKitty (Apache HTTPd for example).

To update the HyperKitty database, if you're using Django 1.6, run::

    django-admin syncdb --migrate --pythonpath hyperkitty_standalone --settings settings

If you're using Django 1.7 or later, the command is::

    django-admin migrate --pythonpath hyperkitty_standalone --settings settings

After this command complete, your database will be updated, you can start
your webserver again.


Maintenance
===========

There are a few tasks in HyperKitty that need to be run at regular intervals.
The ``hyperkitty_standalone`` directory contains an example ``crontab`` file
that you can put in your ``/etc/cron.d`` directory.


RPMs
====
Some preliminary RPMs for Fedora 20 are available from the repository described in this repo file::

    http://repos.fedorapeople.org/repos/abompard/hyperkitty/hyperkitty.repo

Only Fedora 20 has packages for now, but there will be RPMs for EPEL7 (RHEL-7
compatible), and the plan is to submit HyperKitty and Mailman3 for inclusion
into Fedora when Mailman3 itself is out. At the moment, the packages are rather
stable, but the dependencies can change a lot. These packages have been tested
on Fedora 20 with the targeted SELinux policy set to enforcing.


License
=======

HyperKitty is licensed under the `GPL v3.0`_

.. _GPL v3.0: http://www.gnu.org/licenses/gpl-3.0.html
