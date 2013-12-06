Setting up the databases
========================

There are two databases in HyperKitty: one for the Django app, configured in
the regular ``DATABASES`` variable, and one for the KittyStore backend,
configured in the ``KITTYSTORE_URL`` variable.

Now you can create the KittyStore and HyperKitty databases, and set their
access URLs in ``hyperkitty_standalone/settings.py`` (or
``hyperkitty_standalone/settings_local.py``). HyperKitty's database can be
created using the following command::

    django-admin syncdb  --pythonpath hyperkitty_standalone --settings settings
    django-admin migrate --pythonpath hyperkitty_standalone --settings settings

KittyStore's database is configured using an URI. The syntax is as follows::

    KITTYSTORE_URL = "scheme://username:password@hostname:port/database_name"

The scheme may be "sqlite", "postgres", or "mysql". For example, with sqlite::

    KITTYSTORE_URL = "sqlite:////path/to/hyperkitty/directory/kittystore.db'

.. note::
    If you're using SQLite and you're getting "Database is locked" errors, stop
    your webserver during the import.

KittyStore also uses a fulltext search engine which resides in a directory on
the filesystem. The path to this directory must be configured in the
``KITTYSTORE_SEARCH_INDEX`` variable. This directory should be writable by the
user running Mailman and readable by the user running HyperKitty (usually your
webserver). It will be automatically created when the regular KittyStore
database is created. The command to create the KittyStore database is::

    kittystore-updatedb -p hyperkitty_standalone -s settings


Importing the current archives
==============================

If you are currently running Mailman 2.1, you can run ``kittystore-import`` to
import existing archives into the mailman database. This command will import
the Mbox files: if you're installing hyperkitty on the machine which hosted the
previous version of mailman, those files are available locally and you can use
them directly.

The command's syntax is::

    kittystore-import --settings MODULE --pythonpath PATH -l NAME mbox_file [mbox_file ...]

where:

* ``MODULE`` is the python module with HyperKitty's Django settings,
* ``PATH`` is an additionnal path to add to Python if the settings module can't be
  imported directly (this should be familiar if you know how to use Django's
  ``django-admin`` command)
* ``NAME`` is the fully-qualified list name (including the ``@`` sign and the
  domain name)
* The ``mbox_file`` arguments are the existing archives to import. Make sure you point 
at the ``*.txt`` version of the files and not the ``*.gz``.

If the previous archives aren't available locally, you need to download them
from your current Mailman 2.1 installation. The ``kittystore-download21``
command can help you do that, its syntax is::

    kittystore-download21 -u URL -l LIST_NAME [-d destdir]

where:

* ``URL`` is the base URL of your current Mailman 2.1 installation, typically
  the part before the ``/pipermail`` subdirectory when you're looking at your
  current archives. Make sure you remember to include the 'http://' in this string.
* ``LIST_NAME`` is the name of the mailing-list without the domain (before the
  ``@`` sign)
