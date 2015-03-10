Setting up the databases
========================

The HyperKitty database is configured using the ``DATABASE`` setting in
Django's ``settings.py`` file, as usual. If you're using Django 1.6, the
database can be created with the following command::

    django-admin syncdb --migrate --pythonpath hyperkitty_standalone --settings settings

If you're using Django 1.7 or later, the command is::

    django-admin migrate --pythonpath hyperkitty_standalone --settings settings

HyperKitty also uses a fulltext search engine. Thanks to the Django-Haystack
library, the search engine backend is pluggable, refer to the Haystack
documentation on how to install and configure the fulltext search engine
backend.

HyperKitty's default configuration uses the `Whoosh`_ backend, so if you want to use that you just need to install the ``Whoosh`` Python library.

.. _Whoosh: https://pythonhosted.org/Whoosh/


Importing the current archives
==============================

If you are currently running Mailman 2.1, you can run the ``hyperkitty_import``
management command to import existing archives into the mailman database. This
command will import the Mbox files: if you're installing HyperKitty on the
machine which hosted the previous version of Mailman, those files are available
locally and you can use them directly.

The command's syntax is::

    django-admin hyperkitty_import --pythonpath hyperkitty_standalone --settings settings -l ADDRESS mbox_file [mbox_file ...]

where:

* ``ADDRESS`` is the fully-qualified list name (including the ``@`` sign and
  the domain name)
* The ``mbox_file`` arguments are the existing archives to import. Make sure
  you point at the ``*.txt`` version of the files and not the ``*.gz``.

If the previous archives aren't available locally, you need to download them
from your current Mailman 2.1 installation. The ``mailman2_download``
management command can help you do that, its syntax is::

    django-admin mailman2_download --pythonpath hyperkitty_standalone --settings settings -u URL -l LIST_NAME [-d destdir]

where:

* ``URL`` is the base URL of your current Mailman 2.1 installation, typically
  the part before the ``/pipermail`` subdirectory when you're looking at your
  current archives. Make sure you remember to include the 'http://' in this string.
* ``LIST_NAME`` is the name of the mailing-list without the domain (before the
  ``@`` sign)

After importing your existing archives, you must add them to the fulltext
search engine with the following command::

    django-admin update_index --pythonpath hyperkitty_standalone --settings settings

Refer to `the command's documentation`_ for available switches.

.. _`the command's documentation`: http://django-haystack.readthedocs.org/en/latest/management_commands.html#update-index

