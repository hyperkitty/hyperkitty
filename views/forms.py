from django import forms

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


