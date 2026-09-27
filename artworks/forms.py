import difflib
import re

from django import forms
from django.db.models import Count
from django.template.defaultfilters import filesizeformat
from PIL import Image, UnidentifiedImageError
from core.constants import FOCUS_AREAS, MAX_IMAGE_BYTES
from core.forms import NoLabelSuffixMixin
from .models import Artwork, CritiqueRequest, Tag


def grouped_tag_choices():
    """Tag choices bucketed by category, as [(group label, [(pk, name), ...]), ...].

    Django's ChoiceWidget understands this nested shape and renders each bucket
    as its own labelled group, which turns one long flat column of checkboxes
    into three short scannable ones.

    Ordered by how many artworks use each tag, so that when a category outgrows
    GroupedTagSelect.visible_per_group it is the least-used tags that get tucked
    away. Ties break alphabetically.
    """
    by_category = {}
    tags = Tag.objects.annotate(use_count=Count('artworks')).order_by('-use_count', 'name')
    for tag in tags:
        by_category.setdefault(tag.category, []).append((tag.pk, tag.name))

    # Follow the order declared on Tag.CATEGORY_CHOICES rather than alphabetical,
    # and skip any category that has no tags yet.
    return [
        (label, by_category[key])
        for key, label in Tag.CATEGORY_CHOICES
        if key in by_category
    ]


def similar_tags(name, category, limit=4):
    """Existing tags in `category` whose names look like `name`.

    Catching near-duplicates at creation time is what keeps the tag list usable;
    hiding them better in the picker only treats the symptom. Returns [] for an
    exact match, which callers handle separately by reusing that tag.

    Two passes, because neither alone is enough:

      * difflib for close spellings -- 'portraits' -> 'portrait',
        'watercolor' -> 'watercolour', 'charcole' -> 'charcoal';
      * per-word prefix overlap for the multi-word names difflib scores too low --
        'pastel' vs 'oil pastel' only reaches 0.75 and 'oils' vs 'oil paint' 0.46,
        both under the cutoff.

    The second pass compares against each word of the existing name rather than
    using a plain `in`, so 'ink' can match 'acrylic ink' without also matching
    'linework'. It needs 3 characters to start, since two-letter prefixes match
    far too much to be a useful suggestion.
    """
    typed = name.lower()
    candidates = {tag.name.lower(): tag for tag in Tag.objects.filter(category=category)}

    if typed in candidates:
        return []

    hits = []
    for match in difflib.get_close_matches(typed, candidates, n=limit, cutoff=0.8):
        hits.append(candidates[match])

    if len(typed) >= 3:
        for lowered, tag in sorted(candidates.items()):
            if tag in hits:
                continue
            words = [w for w in re.split(r'[\s\-]+', lowered) if len(w) >= 3]
            if any(word.startswith(typed) or typed.startswith(word) for word in words):
                hits.append(tag)

    return hits[:limit]


class GroupedTagSelect(forms.CheckboxSelectMultiple):
    """Checkboxes grouped by category, with the long tail behind a <details>.

    Only the most-used `visible_per_group` tags in each category are shown up
    front; the rest sit in a collapsed "N more" disclosure. Collapsed options are
    still in the DOM, so a box ticked inside one is submitted normally -- that is
    exactly why this works where paginating the picker would not, since paging
    would drop selections made on a page you navigated away from.

    Does nothing until a category actually exceeds the threshold.
    """

    template_name = 'artworks/widgets/grouped_tag_select.html'
    visible_per_group = 8
    # Hiding one or two tags behind a "2 more" toggle costs a click and saves
    # almost no space, so don't collapse until the tail is worth collapsing.
    min_overflow = 3

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)

        groups = []
        for label, options, _index in context['widget']['optgroups']:
            head, tail = options[:self.visible_per_group], options[self.visible_per_group:]
            if len(tail) < self.min_overflow:
                head, tail = options, []

            # Usage decides which tags are visible; alphabetical order decides how
            # they are arranged, so chips don't shuffle around as counts change.
            by_name = lambda option: option['label'].lower()
            groups.append({
                'label': label,
                'visible': sorted(head, key=by_name),
                'overflow': sorted(tail, key=by_name),
                # Open the disclosure when it hides a ticked box, so someone
                # editing an artwork can always see every tag they have chosen.
                'overflow_has_selection': any(option['selected'] for option in tail),
                # Each category is collapsed behind its own toggle, so the
                # toggle has to name what is ticked inside it -- otherwise
                # closing it hides the choice you just made, on the one screen
                # where choosing is the whole task. Read off every option in the
                # category, visible and overflow alike, in the order shown.
                'selected_labels': [
                    option['label']
                    for option in sorted(options, key=by_name)
                    if option['selected']
                ],
            })

        context['widget']['groups'] = groups
        return context


class MediumEntry(forms.TextInput):
    """Text box that carries its own Add button.

    A bare text field gave no sign that anything had happened: the artist typed a
    medium and only found out on save whether it was reused or created. Pairing
    the input with a submit button makes adding a medium a deliberate act with an
    immediate, visible answer.

    Being a widget rather than template markup means `as_p` still renders the
    field normally -- the button comes along with it.
    """

    template_name = 'artworks/widgets/medium_entry.html'


class GroupedTagsMixin(NoLabelSuffixMixin):
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

    # Buttons belonging to the medium box. Pressing one updates the form and
    # re-renders it; only the form's own submit button saves anything.
    INTERIM_BUTTONS = ('add_medium', 'use_existing_tag', 'confirm_new_medium')

    # Filled in by clean_new_medium() when the typed name looks like an existing
    # tag; the template renders one button per suggestion.
    medium_suggestions = ()
    attempted_medium = ''
    # ('selected', tag) or ('pending', name) -- inline feedback while editing.
    medium_notice = None
    # ('reused', tag) or ('created', tag) -- what save() actually did, so the
    # view can say so afterwards.
    medium_outcome = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.medium_suggestions = ()
        self.medium_notice = None
        self.medium_outcome = None

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
            help_text='Type it, then press Add.',
            widget=MediumEntry(attrs={'placeholder': 'e.g. gouache'}),
        )

        # Resolve the medium box's buttons before any cleaning happens, so the
        # rest of the form behaves as if the artist had ticked a box themselves.
        if self.is_bound:
            chosen = self.data.get('use_existing_tag')
            if chosen:
                self._select_suggested_tag(chosen)
                # Confirm the swap in the same words the Add button uses. A bad
                # id just yields no notice; `tags` rejects it during validation.
                if str(chosen).isdigit():
                    tag = Tag.objects.filter(pk=int(chosen)).first()
                    if tag:
                        self.medium_notice = ('selected', tag)
            elif self.data.get('add_medium'):
                self._resolve_typed_medium()

    @property
    def is_interim_submit(self):
        """True when one of the medium box's own buttons was pressed.

        The view uses this to re-render instead of saving, so 'Add' means 'add
        this medium to my selection', not 'post the artwork'.
        """
        return self.is_bound and any(key in self.data for key in self.INTERIM_BUTTONS)

    def is_valid(self):
        # An interim press is never a valid submission, whatever else the form
        # says. Without this, pruning errors below would make is_valid() return
        # True for data that was never meant to be saved -- and since pruning
        # does not put anything back into cleaned_data, a caller that trusted it
        # would blow up in save_m2m().
        return super().is_valid() and not self.is_interim_submit

    def full_clean(self):
        super().full_clean()
        # Errors about a missing image or title are premature on an interim
        # press, so keep only the medium box's own feedback for display.
        if self.is_interim_submit and self._errors:
            self._errors = {
                field: errors for field, errors in self._errors.items()
                if field == 'new_medium'
            }

    def _resolve_typed_medium(self):
        """Handle the Add button: turn the typed name into a ticked chip if it
        already exists, so the artist sees the answer immediately.

        A name that is genuinely new is left in the box; clean_new_medium() then
        either offers near-matches or marks it as pending. It is still not
        created until save(), so abandoning the form leaves no orphan tag.
        """
        typed = re.sub(r'\s+', ' ', (self.data.get('new_medium') or '').strip())
        if not typed:
            return

        existing = Tag.objects.filter(name__iexact=typed, category=Tag.MEDIUM).first()
        if existing:
            self._select_suggested_tag(existing.pk)
            self.medium_notice = ('selected', existing)

    def _select_suggested_tag(self, tag_id):
        """Tick `tag_id` in the submitted data and clear the typed medium.

        `request.POST` is an immutable multi-value QueryDict, but a plain dict is
        also valid form input, so read through the widget (which knows both
        shapes) and write back with whichever API the copy supports.

        The id is not trusted here -- it goes through `tags`, so
        ModelMultipleChoiceField validates it against the queryset as usual.
        """
        data = self.data.copy()
        widget = self.fields['tags'].widget
        selected = [str(value) for value in
                    (widget.value_from_datadict(data, self.files, 'tags') or [])]

        if str(tag_id) not in selected:
            selected.append(str(tag_id))

        if hasattr(data, 'setlist'):
            data.setlist('tags', selected)
        else:
            data['tags'] = selected
        data['new_medium'] = ''
        self.data = data

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

        # An exact medium match is reused as-is by save(); nothing to suggest.
        # The Add button resolves this case into a ticked chip before cleaning,
        # so reaching here means the artist typed it and pressed the main submit.
        if Tag.objects.filter(name__iexact=name, category=Tag.MEDIUM).exists():
            return name

        # Offer near-matches once. If the artist submits again with the confirm
        # button, take them at their word and let the new tag through.
        if not self.data.get('confirm_new_medium'):
            suggestions = similar_tags(name, Tag.MEDIUM)
            if suggestions:
                self.medium_suggestions = suggestions
                self.attempted_medium = name
                raise forms.ValidationError(
                    f'"{name}" looks close to a medium that already exists.'
                )

        # Genuinely new. Say so plainly, and be explicit that nothing is created
        # until the artwork itself is saved.
        if self.is_interim_submit:
            self.medium_notice = ('pending', name)

        return name

    def clean(self):
        cleaned = super().clean()
        tags = cleaned.get('tags') or []

        # A pending new_medium counts, since save() is about to turn it into one.
        has_medium = (
            any(tag.category == Tag.MEDIUM for tag in tags)
            or bool(cleaned.get('new_medium'))
        )
        # Stay quiet if new_medium already raised: the artist is being asked about
        # their medium there, and a second error about it only adds noise.
        if not has_medium and 'tags' not in self.errors and 'new_medium' not in self.errors:
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
                self.medium_outcome = ('created', tag)
            else:
                # Reusing an existing tag used to happen silently, which left the
                # artist unsure whether their medium had registered at all.
                self.medium_outcome = ('reused', tag)

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
            'tags': GroupedTagSelect(),
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
            'tags': GroupedTagSelect(),
        }


class CritiqueRequestForm(NoLabelSuffixMixin, forms.ModelForm):
    # Overriding the default widget for focus_areas to use checkboxes instead of a multi-select dropdown.
    focus_areas = forms.MultipleChoiceField(
        choices=FOCUS_AREAS,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'focus-picker'}),
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