from django.contrib import messages
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
        messages.error(request, "You can't critique your own work.")
        return redirect('artwork_detail', pk=artwork.pk)

    if not hasattr(artwork, 'critique_request'):
        messages.error(
            request,
            "This artwork has no feedback request, so there's nothing to respond to.",
        )
        return redirect('artwork_detail', pk=artwork.pk)

    # One critique per person per artwork. Checked here rather than with a DB
    # constraint so revision threads stay possible later. Guarding before the
    # POST branch also blocks a double submit or a hand-crafted POST.
    if Critique.objects.filter(artwork=artwork, user=request.user).exists():
        messages.info(request, "You've already critiqued this piece.")
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
                    category = form.cleaned_data.get('category')
                    body = form.cleaned_data.get('body')
                    if category not in focus_areas or not body:
                        continue
                    CritiqueSection.objects.create(
                        critique=critique,
                        category=category,
                        body=body,
                    )
            messages.success(request, "Your critique has been posted. Thank you!")
            return redirect('artwork_detail', pk=artwork.pk)
    else:
        formset = CritiqueSectionFormSet(initial=initial)

    return render(request, 'critiques/create.html', {
        'artwork': artwork,
        'formset': formset,
    })


@login_required
def edit_critique(request, pk):
    critique = get_object_or_404(
        Critique.objects.select_related('artwork', 'artwork__critique_request'),
        pk=pk,
    )
    artwork = critique.artwork

    if critique.user != request.user:
        messages.error(request, "You can only edit your own critiques.")
        return redirect('artwork_detail', pk=artwork.pk)

    existing = {section.category: section for section in critique.sections.all()}
    requested = getattr(artwork, 'critique_request', None)
    requested_areas = list(requested.focus_areas) if requested else []

    # Every area the artist asked about, plus any this critique already answered.
    # The second part matters if the request changed after the critique was
    # written -- without it an edit would silently drop those sections.
    categories = requested_areas + [c for c in existing if c not in requested_areas]

    initial = [
        {'category': category, 'body': existing[category].body if category in existing else ''}
        for category in categories
    ]

    if request.method == 'POST':
        formset = CritiqueSectionFormSet(request.POST, initial=initial)

        if formset.is_valid():
            with transaction.atomic():
                for form in formset:
                    category = form.cleaned_data.get('category')
                    body = form.cleaned_data.get('body')
                    # category comes from a hidden input, so don't trust it.
                    if category not in categories:
                        continue
                    section = existing.get(category)
                    if body and section:
                        section.body = body
                        section.save()
                    elif body:
                        CritiqueSection.objects.create(
                            critique=critique,
                            category=category,
                            body=body,
                        )
                    elif section:
                        # Cleared out, so the critic no longer answers this area.
                        section.delete()
            messages.success(request, "Your critique has been updated.")
            return redirect('artwork_detail', pk=artwork.pk)
    else:
        formset = CritiqueSectionFormSet(initial=initial)

    return render(request, 'critiques/edit.html', {
        'artwork': artwork,
        'critique': critique,
        'formset': formset,
    })


@login_required
def delete_critique(request, pk):
    critique = get_object_or_404(Critique.objects.select_related('artwork'), pk=pk)
    artwork_pk = critique.artwork_id

    if critique.user != request.user:
        messages.error(request, "You can only delete your own critiques.")
        return redirect('artwork_detail', pk=artwork_pk)

    # Only ever delete on POST. A GET that deleted data would fire on any link
    # preview or crawler, so GET just renders the confirmation page.
    if request.method == 'POST':
        critique.delete()
        messages.success(request, "Your critique has been deleted.")
        return redirect('artwork_detail', pk=artwork_pk)

    return render(request, 'critiques/confirm_delete.html', {
        'critique': critique,
        'artwork': critique.artwork,
    })