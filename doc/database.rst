Setting up the databases
========================

There are two databases in HyperKitty: one for the Django app, configured in
the regular ``DATABASES`` variable, and one for the KittyStore backend,
configured in the ``KITTYSTORE_URL`` variable.

Now you can create the KittyStore and HyperKitty databases, and set their
access URLs in ``hyperkitty_standalone/settings.py`` (or
``hyperkitty_standalone/settings_local.py``). HyperKitty's database can be
created using the following command::

    python hyperkitty_standalone/manage.py syncdb
    python hyperkitty_standalone/manage.py migrate hyperkitty

KittyStore's database will be created automatically on first access, but you
still need to configure its URI. The syntax is as follows::

    KITTYSTORE_URL = "scheme://username:password@hostname:port/database_name"

The scheme may be "sqlite", "postgres", or "mysql". For example, with sqlite::

    KITTYSTORE_URL = "sqlite:////path/to/hyperkitty/directory/kittystore.db'

.. note::
    If you're using SQLite and you're getting "Database is locked" errors, stop
    your webserver during the import.


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
* The ``mbox_file`` arguments are the existing archives to import.

If the previous archives aren't available locally, you need to download them
from your current Mailman 2.1 installation. The ``kittystore-download21``
command can help you do that, its syntax is::

    kittystore-download21 -u URL -l LIST_NAME [-d destdir]

where:

* ``URL`` is the base URL of your current Mailman 2.1 installation, typically
  the part before the ``/pipermail`` subdirectory when you're looking at your
  current archives.
* ``LIST_NAME`` is the name of the mailing-list without the domain (before the
  ``@`` sign)
