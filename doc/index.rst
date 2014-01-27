=====================================================
HyperKitty, the next-generation mailing-list archiver
=====================================================

HyperKitty is a Django-based application providing a web interface to access
GNU Mailman v3 archives, and interact with the lists.

The project page is https://fedorahosted.org/hyperkitty/ and the code is
available from https://github.com/hyperkitty/hyperkitty .

The authors are listed in the ``AUTHORS.txt`` file.

Contents:

.. toctree::
   :maxdepth: 1
   
   news.rst
   install.rst
   development.rst


Why HyperKitty?
===============

Mailman is in need for replacement of its default Pipermail archiver. It is
over 10 years old, users' expectations have changed and their requirements are
more sophisticated than the current archiver can deliver on. Mailman3 is the
currently under active development and it offers a pluggable architecture where
multiple archivers can be plugged to the core without too much pain.

Some of drawbacks of Pipermail :

- It does not support stable URLs.
- It has scalability issues (it was not suitable for organizations working with
  hundred of thousand of messages per day, e.g, Launchpad)
- The web interface is dated and does not output standards-compliant HTML nor
  does it take advantage of new technologies such as AJAX.

The HyperKitty archiver addresses most of the drawbacks of Pipermail.


Copyright
=========

Copyright (C) 2012 by the Free Software Foundation, Inc.

HyperKitty is free software: you can redistribute it and/or
modify it under the terms of the GNU General Public License as
published by the Free Software Foundation, version 3 of the License.

HyperKitty is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser
General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with HyperKitty. If not, see <http://www.gnu.org/licenses/>.

