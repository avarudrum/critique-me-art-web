import re

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
    """Groups the `tags` checkboxes by category and handles the medium rules.

    Medium is not a field on Artwork -- it is whichever tags have
    category == 'medium'. This mixin therefore has to do two extra jobs:

      * offer a free-text box so an artist whose medium isn't listed can add it,
        instead of being stuck with the predefined chips;
      * require at least one medium, so the browse filter stays complete.

    The new Tag is created in save(), never in clean(). Creating it during
    validation would leave an orphan tag behind whenever the surrounding request
    fails for some other reason -- on upload, `CritiqueRequestForm` is validated
    alongside this one and either can fail.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set here rather than on the class so the tag list is read fresh each
        # request. This only changes rendering -- ModelMultipleChoiceField still
        # validates submitted ids against its queryset, not against these choices.
        self.fields['tags'].choices = grouped_tag_choices()
        self.fields['tags'].label = 'Tags'

        # Declared here because a plain (non-Form) mixin's class attributes are
        # not collected by Django's form metaclass. Appending it in __init__ also
        # puts it directly after the tag chips, which is where it belongs.
        self.fields['new_medium'] = forms.CharField(
            required=False,
            max_length=50,
            label='Medium not listed? Add it',
            help_text='It becomes a medium tag others can filter by.',
            widget=forms.TextInput(attrs={'placeholder': 'e.g. gouache'}),
        )

    def clean_new_medium(self):
        name = re.sub(r'\s+', ' ', (self.cleaned_data.get('new_medium') or '').strip())
        if not name:
            return ''

        if len(name) < 2:
            raise forms.ValidationError('Give the medium a slightly longer name.')

        # A name that already exists under another category would otherwise be
        # reused as-is, silently leaving the artwork with no medium tag at all.
        clash = Tag.objects.filter(name__iexact=name).exclude(category=Tag.MEDIUM).first()
        if clash:
            label = clash.get_category_display()
            raise forms.ValidationError(
                f'"{clash.name}" already exists as a {label.lower()} tag. '
                f'Select it from the {label} list instead.'
            )
        return name

    def clean(self):
        cleaned = super().clean()
        tags = cleaned.get('tags') or []

        # A pending new_medium counts, since save() is about to turn it into one.
        has_medium = (
            any(tag.category == Tag.MEDIUM for tag in tags)
            or bool(cleaned.get('new_medium'))
        )
        if not has_medium and 'tags' not in self.errors:
            self.add_error(
                'tags',
                'Pick at least one medium, or add your own in the box below.',
            )
        return cleaned

    def save(self, commit=True):
        name = self.cleaned_data.get('new_medium')
        if name:
            # Case-insensitive, so "Oil", "oil" and " oil " don't become three
            # tags. Tag.name is unique, but that constraint is case-sensitive.
            tag = Tag.objects.filter(name__iexact=name).first()
            if tag is None:
                tag = Tag.objects.create(name=name, category=Tag.MEDIUM)

            tags = list(self.cleaned_data.get('tags') or [])
            if tag not in tags:
                tags.append(tag)
            # save_m2m() reads cleaned_data when it runs, so this reaches the
            # M2M whether the caller uses commit=True or commit=False.
            self.cleaned_data['tags'] = tags

        return super().save(commit=commit)


class ArtworkForm(GroupedTagsMixin, forms.ModelForm):
    class Meta:
        model = Artwork
        fields = ('title', 'description', 'image', 'tags')
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
        fields = ('title', 'description', 'tags')
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