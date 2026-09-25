from django import forms
from django.template.defaultfilters import filesizeformat
from PIL import Image, UnidentifiedImageError
from core.constants import FOCUS_AREAS, MAX_IMAGE_BYTES
from .models import Artwork, CritiqueRequest, Tag


def grouped_tag_choices():
    """Tag choices bucketed by category, as [(group label, [(pk, name), ...]), ...].

    Django's ChoiceWidget understands this nested shape and renders each bucket
    as its own labelled group, which turns one long flat column of checkboxes
    into three short scannable ones.
    """
    by_category = {}
    for tag in Tag.objects.order_by('name'):
        by_category.setdefault(tag.category, []).append((tag.pk, tag.name))

    # Follow the order declared on Tag.CATEGORY_CHOICES rather than alphabetical,
    # and skip any category that has no tags yet.
    return [
        (label, by_category[key])
        for key, label in Tag.CATEGORY_CHOICES
        if key in by_category
    ]


class GroupedTagsMixin:
    """Groups the `tags` checkboxes by category.

    Set in __init__ rather than on the class so the tag list is read fresh each
    request. This only changes rendering -- ModelMultipleChoiceField still
    validates submitted ids against its queryset, not against these choices.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['tags'].choices = grouped_tag_choices()


class ArtworkForm(GroupedTagsMixin, forms.ModelForm):
    class Meta:
        model = Artwork
        fields = ('title', 'description', 'image', 'medium', 'tags')
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'tags': forms.CheckboxSelectMultiple(),
        }

    def clean_image(self):
        image = self.cleaned_data.get('image')

        # An already-saved image comes back as a CloudinaryResource with no
        # .size or .read, so only newly uploaded files get checked.
        if not image or not hasattr(image, 'size'):
            return image

        if image.size > MAX_IMAGE_BYTES:
            raise forms.ValidationError(
                f"That file is {filesizeformat(image.size)}. "
                f"Please upload an image under {filesizeformat(MAX_IMAGE_BYTES)}."
            )

        # CloudinaryFileField is a plain FileField, so it never checks that the
        # upload is actually an image. Pillow reads the header and raises if not.
        try:
            image.seek(0)
            Image.open(image).verify()
        except (UnidentifiedImageError, OSError, ValueError):
            raise forms.ValidationError(
                "That file isn't a readable image. Please upload a JPEG, PNG, WebP or GIF."
            )
        finally:
            # verify() leaves the file consumed; rewind so the upload still works.
            image.seek(0)

        return image


class ArtworkEditForm(GroupedTagsMixin, forms.ModelForm):
    """Descriptive fields only.

    The image and the critique request's focus areas are deliberately left out:
    critics responded to that specific image and those specific areas, so
    swapping either one would leave existing critiques answering something the
    viewer can no longer see.
    """

    class Meta:
        model = Artwork
        fields = ('title', 'description', 'medium', 'tags')
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