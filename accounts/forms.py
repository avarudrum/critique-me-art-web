from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from core.forms import NoLabelSuffixMixin
from .models import User


class SignUpForm(NoLabelSuffixMixin, UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'email')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # UserCreationForm declares password2 with 'Enter the same password as
        # before, for verification.' Cleared here rather than by redeclaring the
        # field, which would mean copying Django's widget and validation too.
        # The label already says Password confirmation.
        self.fields['password2'].help_text = ''


class LoginForm(NoLabelSuffixMixin, AuthenticationForm):
    """Only exists so the login page's labels match every other form.

    LoginView builds its own form, so it has to be handed this one explicitly
    in config/urls.py.
    """


class ProfileForm(NoLabelSuffixMixin, forms.ModelForm):
    """The bits of a profile someone can write about themselves.

    `bio` and `primary_medium` have existed on the User model since the start but
    had no UI outside the admin, so every profile page would have rendered empty.
    """

    class Meta:
        model = User
        fields = ('bio', 'primary_medium')
        labels = {'primary_medium': 'Primary medium'}
        widgets = {
            'bio': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': "What you make, what you're working on, what you like to critique.",
            }),
            'primary_medium': forms.TextInput(attrs={'placeholder': 'e.g. charcoal'}),
        }
