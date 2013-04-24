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

Then, you can run ``kittystore-import`` to import existing archives into the
mailman database. Thoses archives can be downloaded by calling
``kittystore-download21``. If you're installing hyperkitty on the machine which
hosted the previous version of mailman, the archives are already available
locally and you can use them directly.

.. note::
    If you're using SQLite and you're getting "Database is locked" errors, stop
    your webserver during the import.

