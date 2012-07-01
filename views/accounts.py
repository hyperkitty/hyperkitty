import re
import sys

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout, authenticate, login
from django.contrib.auth.decorators import (login_required,
                                            permission_required,
                                            user_passes_test)
from django.contrib.auth.forms import AuthenticationForm
from gsoc.models import UserProfile
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, redirect
from django.template import Context, loader, RequestContext
from django.utils.translation import gettext as _
from urllib2 import HTTPError
from urlparse import urlparse

from forms import RegistrationForm
from gsoc.utils import log

def user_logout(request):
    logout(request)
    return redirect('user_login')

def user_login(request,template = 'login.html'):
    
    parse_r = urlparse(request.META.get('HTTP_REFERER', 'index')) 
    previous = '%s%s' % (parse_r.path, parse_r.query)

    next_var = request.POST.get('next', request.GET.get('next', previous))

    if request.method == 'POST':
        form = AuthenticationForm(request.POST)
        user = authenticate(username=request.POST.get('username'),
                            password=request.POST.get('password'))
        
	if user is not None:
            log('debug', user)
            if user.is_active:
                login(request,user)
	        return redirect(next_var)

    else:
        form = AuthenticationForm()
    return render_to_response(template, {'form': form, 'next' : next_var},
                              context_instance=RequestContext(request))

@login_required
def user_profile(request, user_email = None):
    if not request.user.is_authenticated():
        return redirect('user_login')
    # try to render the user profile.
    try:
    	user_profile = request.user.get_profile()
    # @TODO: Include the error name e.g, ProfileDoesNotExist?
    except:
	user_profile = UserProfile.objects.create(user=request.user)

    t = loader.get_template('user_profile.html')

    c = RequestContext(request, {
        'user_profile' : user_profile,
    })
    
    return HttpResponse(t.render(c))


def user_registration(request):
    if request.user.is_authenticated():
        # Already registered, redirect back to index page
        return redirect('index')
    
    if request.POST:
        form = RegistrationForm(request.POST)
        if form.is_valid():
	    # Save the user data.
	    form.save(form.cleaned_data)
	    user = authenticate(username=form.cleaned_data['username'], 
				password=form.cleaned_data['password1'])

            if user is not None:
            	log('debug', user)
            	if user.is_active:
                	login(request,user)
                	return redirect('index')
    else:
        form = RegistrationForm()
    
    return render_to_response('register.html', {'form': form}, context_instance=RequestContext(request))

