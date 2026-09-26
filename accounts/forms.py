from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from core.forms import NoLabelSuffixMixin
from .models import User


class SignUpForm(NoLabelSuffixMixin, UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'email')


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
        labels = {'primary_medium': 'What you mostly work in'}
        widgets = {
            'bio': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': "What you make, what you're working on, what you like to critique.",
            }),
            'primary_medium': forms.TextInput(attrs={'placeholder': 'e.g. charcoal'}),
        }
