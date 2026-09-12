from django import forms
from core.constants import FOCUS_AREAS
from .models import Artwork, CritiqueRequest


class ArtworkForm(forms.ModelForm):
    class Meta:
        model = Artwork
        fields = ('title', 'description', 'image', 'medium', 'tags')
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'tags': forms.CheckboxSelectMultiple(),
        }


class CritiqueRequestForm(forms.ModelForm):
    # Overriding the default widget for focus_areas to use checkboxes instead of a multi-select dropdown.
    focus_areas = forms.MultipleChoiceField(
        choices=FOCUS_AREAS,
        widget=forms.CheckboxSelectMultiple,
        help_text="What would you like feedback on?",
    )

    class Meta:
        model = CritiqueRequest
        fields = ('focus_areas', 'artist_note')
        widgets = {
            'artist_note': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': "e.g. I'm struggling with the background depth",
            }),
        }