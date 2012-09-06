import re
import os
import django.utils.simplejson as simplejson

from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext, loader
from django.conf import settings
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger, InvalidPage
from django.contrib.auth.decorators import (login_required,
                                            permission_required,
                                            user_passes_test)
from kittystore import get_store

from hyperkitty.models import Rating
#from hyperkitty.lib.mockup import *
from forms import *
from hyperkitty.utils import log


def index (request, mlist_fqdn, hashid):
    '''
    Displays a single message identified by its message_id_hash (derived from
    message_id)
    '''
    list_name = mlist_fqdn.split('@')[0]

    search_form = SearchForm(auto_id=False)
    t = loader.get_template('message.html')
    store = get_store(settings.KITTYSTORE_URL)
    message = store.get_message_by_hash_from_list(mlist_fqdn, hashid)
    message.sender_email = message.sender_email.strip()
    # Extract all the votes for this message
    try:
        votes = Rating.objects.filter(messageid = hashid)
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

    c = RequestContext(request, {
        'list_name' : list_name,
        'list_address': mlist_fqdn,
        'message': message,
        'hashid' : hashid,
    })
    return HttpResponse(t.render(c))



@login_required
def vote (request, mlist_fqdn):
    """ Add a rating to a given message identified by messageid. """
    if not request.user.is_authenticated():
        return redirect('user_login')

    value = request.POST['vote']
    hashid = request.POST['hashid']

    # Checks if the user has already voted for a this message. If yes modify db entry else create a new one.
    try:
        v = Rating.objects.get(user = request.user, messageid = hashid, list_address = mlist_fqdn)
    except Rating.DoesNotExist:
        v = Rating(list_address=mlist_fqdn, messageid = hashid, vote = value)

    v.user = request.user
    v.vote = value
    v.save()
    response_dict = { }

    return HttpResponse(simplejson.dumps(response_dict), mimetype='application/javascript')
