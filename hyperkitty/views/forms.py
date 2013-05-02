#-*- coding: utf-8 -*-
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

from django import forms
from django.core import validators
from django.contrib.auth.models import User
from django.utils.safestring import mark_safe



def isValidUsername(username):
        try:
            User.objects.get(username=username)
        except User.DoesNotExist:
            return
        raise validators.ValidationError('The username "%s" is already taken.' % username)



class RegistrationForm(forms.Form):

    username =  forms.CharField(widget=forms.TextInput, required=True,
                                validators=[isValidUsername])

    email     = forms.EmailField(required=True)

    password1 = forms.CharField(widget=forms.PasswordInput,
                                required=True, label="Password")

    password2 = forms.CharField(widget=forms.PasswordInput,
                                required=True, label="Confirm password")

    def clean(self):
        cleaned_data = super(RegistrationForm, self).clean()
        if cleaned_data.get("password1") != cleaned_data.get("password2"):
            self._errors["password2"] = self.error_class(["Passwords do not match."])
            del cleaned_data["password1"]
            del cleaned_data["password2"]
        return cleaned_data



class UserProfileForm(forms.Form):
    first_name = forms.CharField()
    last_name = forms.CharField()



class TextInputWithButton(forms.TextInput):
    """
    Render a text field and a button following the Twitter Bootstrap
    directives: http://twitter.github.com/bootstrap/base-css.html#buttons

    Use the 'button_text' class attribute to set the button's text.
    """

    def render(self, name, value, attrs=None):
        button_text = self.attrs.pop("button_text", u"")
        initial_rendering = forms.TextInput.render(
                self, name, value, attrs)
        button = mark_safe(u'<button type="submit" class="btn">%s</button>'
                           % button_text)
        return "".join([u'<span class="input-append">',
                        initial_rendering, button, u'</span>'])



class AddTagForm(forms.Form):
    tag =  forms.CharField(label='', help_text=None,
                widget=TextInputWithButton(
                    attrs={'placeholder': 'Add a tag...',
                           'class': 'input-medium',
                           'button_text': 'Add'}
                    )
                )
    from_url = forms.CharField(widget=forms.HiddenInput, required=False)



class SearchForm(forms.Form):
    target =  forms.CharField(label='', help_text=None,
                widget=forms.Select(
                    choices=(('Subject', 'Subject'),
                            ('Content', 'Content'),
                            ('SubjectContent', 'Subject & Content'),
                            ('From', 'From'))
                    )
                )

    keyword = forms.CharField(max_length=100,label='', help_text=None,
                widget=forms.TextInput(
                    attrs={'placeholder': 'Search this list.'}
                    )
                )



class ReplyForm(forms.Form):
    newthread = forms.BooleanField(label="", required=False)
    subject = forms.CharField(label="", required=False,
            widget=forms.TextInput(attrs={ 'placeholder': 'New subject'}))
    message = forms.CharField(label="", widget=forms.Textarea)

class PostForm(forms.Form):
    subject = forms.CharField()
    message = forms.CharField(widget=forms.Textarea)
