import re
import sys
import logging


from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout, authenticate, login
from django.contrib.auth.decorators import (login_required,
                                            permission_required,
                                            user_passes_test)
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, redirect
from django.template import Context, loader, RequestContext
from django.utils.translation import gettext as _
from urllib2 import HTTPError

logger = logging.getLogger(__name__)

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
    #try:
    #    the_user = User.objects.get(email=user_email)
    #except MailmanApiError:
    #    return utils.render_api_error(request)
    return render_to_response('postorius/user_profile.html',
    #                          {'mm_user': the_user},
                              context_instance=RequestContext(request))

