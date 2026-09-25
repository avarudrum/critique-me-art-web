from django import forms


class CritiqueSectionForm(forms.Form):
    category = forms.CharField(widget=forms.HiddenInput())
    body = forms.CharField(
        label='Your feedback',
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 5,
            'placeholder': 'Describe what you see before you suggest changes.',
        }),
    )


class BaseCritiqueSectionFormSet(forms.BaseFormSet):
    def clean(self):
        super().clean()
        if any(self.errors):
            return
        if not any(form.cleaned_data.get('body') for form in self.forms):
            raise forms.ValidationError(
                "Write feedback for at least one area before submitting."
            )


CritiqueSectionFormSet = forms.formset_factory(
    CritiqueSectionForm,
    formset=BaseCritiqueSectionFormSet,
    extra=0,
)