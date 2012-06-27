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

from gsoc.utils import log

def user_logout(request):
    logout(request)
    return redirect('user_login')

def user_login(request,template = 'login.html'):
    if request.method == 'POST':
        form = AuthenticationForm(request.POST)
        user = authenticate(username=request.POST.get('username'),
                            password=request.POST.get('password'))
        if user is not None:
            logger.debug(user)
            if user.is_active:
                login(request,user)
                return redirect(request.GET.get('next', 'index'))
    else:
        form = AuthenticationForm()
    return render_to_response(template, {'form': form,},
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
