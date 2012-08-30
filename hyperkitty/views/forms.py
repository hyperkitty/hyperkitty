from django import forms
from django.core import validators
from django.contrib.auth.models import User

def isValidUsername(username):
        try:
            User.objects.get(username=username)
        except User.DoesNotExist:
            return
        raise validators.ValidationError('The username "%s" is already taken.' % username)

class RegistrationForm(forms.Form):

    username =  forms.CharField(label='username', help_text=None,
                widget=forms.TextInput(
                    attrs={'placeholder': 'username...'}
                    ), required = True, validators=[isValidUsername]
                )

    email     = forms.EmailField(required=True)

    password1 = forms.CharField(widget=forms.PasswordInput)

    password2 = forms.CharField(widget=forms.PasswordInput)

    def save(self, new_user_data):
        u = User.objects.create_user(new_user_data['username'],
                                     new_user_data['email'],
                                     new_user_data['password1'])
        u.is_active = True
        u.save()
        return u


class AddTagForm(forms.Form):
    tag =  forms.CharField(label='', help_text=None,
                widget=forms.TextInput(
                    attrs={'placeholder': 'Add a tag...'}
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


