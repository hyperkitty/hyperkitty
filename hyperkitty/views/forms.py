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
                           'class': 'span2',
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


