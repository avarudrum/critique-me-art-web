from django import forms
from .models import CritiqueSection


class CritiqueSectionForm(forms.Form):
    category = forms.CharField(widget=forms.HiddenInput())
    section_type = forms.ChoiceField(
        choices=CritiqueSection.TYPE_CHOICES,
        widget=forms.RadioSelect,
        initial='growth',
        label='This is a',
    )
    body = forms.CharField(
        label='Your feedback',
        widget=forms.Textarea(attrs={
            'rows': 4,
            'placeholder': 'Describe what you see before you suggest changes.',
        }),
    )


CritiqueSectionFormSet = forms.formset_factory(
    CritiqueSectionForm,
    extra=0,
)