import logging
import django.utils.simplejson as simplejson

from django import forms
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext, loader
from django.conf import settings
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger, InvalidPage
from django.contrib.auth.decorators import (login_required,
                                            permission_required,
                                            user_passes_test)
from kittystore.kittysastore import KittySAStore

from gsoc.models import Rating
from lib.mockup import *
from forms import *

logger = logging.getLogger(__name__)

STORE = KittySAStore(settings.KITTYSTORE_URL)

def thread_index (request, mlist_fqdn, threadid):
    ''' Displays all the email for a given thread identifier '''
    list_name = mlist_fqdn.split('@')[0]

    search_form = SearchForm(auto_id=False)
    t = loader.get_template('thread.html')
    threads = STORE.get_thread(list_name, threadid)
    #prev_thread = mongo.get_thread_name(list_name, int(threadid) - 1)
    prev_thread = []
    if len(prev_thread) > 30:
        prev_thread = '%s...' % prev_thread[:31]
    #next_thread = mongo.get_thread_name(list_name, int(threadid) + 1)
    next_thread = []
    if len(next_thread) > 30:
        next_thread = '%s...' % next_thread[:31]

    participants = {}
    cnt = 0

    for message in threads:
     	# @TODO: Move this logic inside KittyStore?
	message.email = message.email.strip()

	# Extract all the votes for this message
	try:
		votes = Rating.objects.filter(messageid = message.message_id)
	except Rating.DoesNotExist:
		votes = {}

	likes = 0
    	dislikes = 0

    	for vote in votes:
		if vote.vote == 1:
			likes = likes + 1
		elif vote.vote == -1:
			dislikes = dislikes + 1
		else:
			pass
	
	message.votes = votes
	message.likes = likes
	message.dislikes = dislikes

        # Statistics on how many participants and threads this month
        participants[message.sender] = {'email': message.email}
        cnt = cnt + 1

    archives_length = STORE.get_archives_length(list_name)
    from_url = '/thread/%s/%s/' %(mlist_fqdn, threadid)
    tag_form = AddTagForm(initial={'from_url' : from_url})
    print dir(search_form)

    c = RequestContext(request, {
        'list_name' : list_name,
        'list_address': mlist_fqdn,
        'search_form': search_form,
        'addtag_form': tag_form,
        'month': 'Thread',
        'participants': participants,
        'answers': cnt,
        'first_mail': threads[0],
        'threads': threads[1:],
        'next_thread': next_thread,
        'next_thread_id': 0,
        'prev_thread': prev_thread,
        'prev_thread_id': 0,
        'archives_length': archives_length,
    })
    return HttpResponse(t.render(c))


@login_required
def add_tag(request, mlist_fqdn, email_id):
    """ Add a tag to a given thread. """
    t = loader.get_template('threads/add_tag_form.html')
    if request.method == 'POST':
        form = AddTagForm(request.POST)
        if form.is_valid():
            print "THERE WE ARE"
            # TODO: Add the logic to add the tag
            if form.data['from_url']:
                return HttpResponseRedirect(form.data['from_url'])
            else:
                return HttpResponseRedirect('/')
    else:
        form = AddTagForm()
    c = RequestContext(request, {
        'list_address': mlist_fqdn,
        'email_id': email_id,
        'addtag_form': form,
        })
    return HttpResponse(t.render(c))

