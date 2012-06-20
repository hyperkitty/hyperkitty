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

logger = logging.getLogger(__name__)




@login_required
def vote_message (request, mlist_fqdn, messageid):
    """ Add a rating to a given message identified by messageid. """
    if not request.user.is_authenticated():
	return redirect('user_login')

    value = request.POST['vote']

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

@login_required
def add_tag(request, mlist_fqdn, email_id):
    """ Add a tag to a given message. """
    t = loader.get_template('simple_form.html')
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
        'app_name': settings.APP_NAME,
        'list_address': mlist_fqdn,
        'email_id': email_id,
        'addtag_form': form,
        })
    return HttpResponse(t.render(c))

