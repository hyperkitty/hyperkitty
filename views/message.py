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
from gsoc.models import Rating
from pages import SearchForm, STORE

logger = logging.getLogger(__name__)


def index (request, mlist_fqdn, messageid):
    ''' Displays a single message identified by its messageid '''
    list_name = mlist_fqdn.split('@')[0]

    search_form = SearchForm(auto_id=False)
    t = loader.get_template('message.html')
    message = STORE.get_email(list_name, messageid)
    message.email = message.email.strip()
    c = RequestContext(request, {
        'app_name': settings.APP_NAME,
        'list_name' : list_name,
        'list_address': mlist_fqdn,
        'message': message,
	'messageid' : messageid,
    })
    return HttpResponse(t.render(c))



@login_required
def vote (request, mlist_fqdn):
    """ Add a rating to a given message identified by messageid. """
    if not request.user.is_authenticated():
	return redirect('user_login')

    value = request.POST['vote']
    messageid = request.POST['messageid']

    # Checks if the user has already voted for a this message. If yes modify db entry else create a new one.
    try:
	v = Rating.objects.get(user = request.user, messageid = messageid, list_address = mlist_fqdn)
    except Rating.DoesNotExist:
    	v = Rating(list_address=mlist_fqdn, messageid = messageid, vote = value) 

    v.user = request.user
    v.vote = value  
    v.save()
    response_dict = { }

    return HttpResponse(simplejson.dumps(response_dict), mimetype='application/javascript')
