from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404

from artworks.models import Artwork
from .forms import CritiqueSectionFormSet
from .models import Critique, CritiqueSection


@login_required
def create_critique(request, artwork_pk):
    artwork = get_object_or_404(Artwork, pk=artwork_pk)

    if artwork.user == request.user:
        return redirect('artwork_detail', pk=artwork.pk)

    if not hasattr(artwork, 'critique_request'):
        return redirect('artwork_detail', pk=artwork.pk)

    focus_areas = artwork.critique_request.focus_areas
    initial = [{'category': area} for area in focus_areas]

    if request.method == 'POST':
        formset = CritiqueSectionFormSet(request.POST, initial=initial)

        if formset.is_valid():
            with transaction.atomic():
                critique = Critique.objects.create(
                    artwork=artwork,
                    user=request.user,
                )
                for form in formset:
                    category = form.cleaned_data['category']
                    if category not in focus_areas:
                        continue
                    CritiqueSection.objects.create(
                        critique=critique,
                        category=category,
                        body=form.cleaned_data['body'],
                        section_type=form.cleaned_data['section_type'],
                    )
            return redirect('artwork_detail', pk=artwork.pk)
    else:
        formset = CritiqueSectionFormSet(initial=initial)

    return render(request, 'critiques/create.html', {
        'artwork': artwork,
        'formset': formset,
    })