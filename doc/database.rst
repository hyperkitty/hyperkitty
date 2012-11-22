Setting up the databases
========================

Now you can create the KittyStore and HyperKitty databases, and set their
access URLs in ``hyperkitty_standalone/settings.py`` (or
``hyperkitty_standalone/settings_local.py``). HyperKitty's database can be
created using the following command::

    python hyperkitty_standalone/manage.py syncdb

KittyStore's database will be created automatically on first access.

Then, you can run ``kittystore-import`` to import existing archives into the
mailman database. Thoses archives can be downloaded by a script similar to the
``get_mbox.py`` script provided in the ``kittystore`` module. If you're
installing hyperkitty on the machine which hosted the previous version of
mailman, the archived are already available locally and you can use them
directly.

.. warning::
    If you're using SQLite and you're getting "Database is locked" errors, stop
    your webserver during the import.

