# -*- coding: utf-8 -*-
# Copyright (C) 1998-2012 by the Free Software Foundation, Inc.
#
# This file is part of HyperKitty.
#
# HyperKitty is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# HyperKitty is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along with
# HyperKitty.  If not, see <http://www.gnu.org/licenses/>.
#
# Author: Aamir Khan <syst3m.w0rm@gmail.com>
#

# pylint: skip-file

class Email(object):
    """ Email class containing the information needed to store and
    display email threads.
    """

    def __init__(self):
        """ Constructor.
        Instanciate the default attributes of the object.
        """
        self.email_id = ''
        self.title = ''
        self.body = ''
        self.tags = []
        self.category = 'question'
        self.category_tag = None
        self.participants = set(['Pierre-Yves Chibon'])
        self.answers = []
        self.liked = 0
        self.author = ''
        self.avatar = None
        self.age = '6 days'

class Author(object):
    """ Author class containing the information needed to get the top
    author of the month!
    """

    def __init__(self):
        """ Constructor.
        Instanciate the default attributes of the object.
        """
        self.name = None
        self.kudos = 0
        self.avatar = None


def get_email_tag(tag):
    threads = generate_random_thread()
    output = []
    for email in threads:
        if tag in email.tags or tag in email.category:
            output.append(email)
        elif email.category_tag and tag in email.category_tag:
            output.append(email)
    return output


def generate_thread_per_category():
    threads = generate_random_thread()
    categories = {}
    for thread in threads:
        category = thread.category
        if thread.category_tag:
            category = thread.category_tag
        if category in categories.keys():
            categories[category].append(thread)
        else:
            categories[category] = [thread]
    return categories

def generate_top_author():
    authors = []

    author = Author()
    author.name = 'Pierre-Yves Chibon'
    author.avatar = 'https://secure.gravatar.com/avatar/072b4416fbfad867a44bc7a5be5eddb9'
    author.kudos = 3
    authors.append(author)

    author = Author()
    author.name = 'Stanislav Ochotnický'
    author.avatar = 'http://sochotni.fedorapeople.org/sochotni.jpg'
    author.kudos = 4
    authors.append(author)

    author = Author()
    author.name = 'Toshio Kuratomi'
    author.avatar = 'https://secure.gravatar.com/avatar/7a9c1d88f484c9806bceca0d6d91e948'
    author.kudos = 5
    authors.append(author)

    return authors

def generate_random_thread():
    threads = []

    ## 1
    email = Email()
    email.email_id = 1
    email.title = 'Headsup! krb5 ccache defaults are changing in Rawhide'
    email.age = '6 days'
    email.body = '''Dear fellow developers,
with the upcoming Fedora 18 release (currently Rawhide) we are going to change the place where krb5 credential cache files are saved by default.

The new default for credential caches will be the /run/user/username directory.
'''
    email.tags.extend(['rawhide', 'krb5'])
    email.participants = set(['Stephen Gallagher', 'Toshio Kuratomi', 'Kevin Fenzi', 'Seth Vidal'])
    email.answers.extend([1,2,3,4,5,6,7,8,9,10,11,12])
    email.liked = 1
    email.author = 'Stephen Gallagher'
    email.avatar = 'http://fedorapeople.org/~sgallagh/karrde712.png'
    threads.append(email)

    ## 2
    email = Email()
    email.email_id = 2
    email.title = 'Problem in packaging kicad'
    email.age = '6 days'
    email.body = '''Paragraph 1: Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. '''
    email.tags.extend(['packaging', 'kicad'])
    email.participants = set(['Pierre-Yves Chibon', 'Tom "spot" Callaway', 'Toshio Kuratomi', 'Kevin Fenzi'])
    email.answers.extend([1,2,3,4,5,6,7,8,9,10,11,12])
    email.liked = 0
    email.author = 'Pierre-Yves Chibon'
    email.avatar = 'https://secure.gravatar.com/avatar/072b4416fbfad867a44bc7a5be5eddb9'
    threads.append(email)

    ## 3
    email = Email()
    email.email_id = 3
    email.title = 'Update Java Guideline'
    email.age = '6 days'
    email.body = '''Paragraph 1: Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. '''
    email.tags.extend(['rawhide', 'krb5'])
    email.participants = set(['Stanislav Ochotnický', 'Tom "spot" Callaway', 'Stephen Gallagher', 'Jason Tibbitts', 'Rex Dieter', 'Toshio Kuratomi'])
    email.answers.extend([1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19])
    email.liked = 5
    email.category = 'todo'
    email.author = 'Stanislav Ochotnický'
    email.avatar = 'http://sochotni.fedorapeople.org/sochotni.jpg'
    threads.append(email)

    ## 4
    email = Email()
    email.email_id = 4
    email.title = 'Agenda for the next Board Meeting'
    email.age = '6 days'
    email.body = '''Paragraph 1: Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. '''
    email.tags.extend(['agenda', 'board'])
    email.participants = set(['Toshio Kuratomi', 'Tom "spot" Callaway', 'Robyn Bergeron', 'Max Spevack'])
    email.answers.extend([1,2,3,4,5,6,7,8,9,10,11,12])
    email.liked = 20
    email.category = 'agenda'
    email.author = 'Toshio Kuratomi'
    email.avatar = 'https://secure.gravatar.com/avatar/7a9c1d88f484c9806bceca0d6d91e948'
    threads.append(email)

    ## 5
    email = Email()
    email.email_id = 5
    email.title = 'I told you so! '
    email.age = '6 days'
    email.body = '''Paragraph 1: Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. '''
    email.tags.extend(['systemd', 'mp3', 'pulseaudio'])
    email.participants = set(['Pierre-Yves Chibon'])
    email.answers.extend([1,2,3,4,5,6,7,8,9,10,11,12])
    email.liked = 0
    email.author = 'Pierre-Yves Chibon'
    email.avatar = 'https://secure.gravatar.com/avatar/072b4416fbfad867a44bc7a5be5eddb9'
    email.category = 'shut down'
    email.category_tag = 'dead'
    threads.append(email)

    return threads
