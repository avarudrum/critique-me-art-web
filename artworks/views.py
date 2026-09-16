from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from .forms import ArtworkForm, CritiqueRequestForm
from .models import Artwork, Tag
from core.constants import FOCUS_AREAS

def browse(request):
    # Prevents n+1 query problem. 
    # Optimizes database queries by fetching related user and tags in a single query.
    artworks = Artwork.objects.select_related('user').prefetch_related('tags')

    # Reading query parameters from the request to filter artworks based on medium, tag, and critique status.
    medium = request.GET.get('medium', '').strip()
    tag_id = request.GET.get('tag', '').strip()
    needs_critique = request.GET.get('needs_critique')

    # Conditionally filter artworks based on the provided query parameters.
    if medium:
        # Case insensitive filtering for medium.
        artworks = artworks.filter(medium__iexact=medium)

    if tag_id.isdigit():
        # Gaurds against invalid tag IDs by checking if it is a digit before filtering.
        artworks = artworks.filter(tags__id=int(tag_id))

    if needs_critique:
        artworks = artworks.filter(critique_status='open')

    mediums = (
        Artwork.objects.values_list('medium', flat=True)
        .distinct()
        .order_by('medium')
    )

    return render(request, 'artworks/browse.html', {
        'artworks': artworks,
        'tags': Tag.objects.all().order_by('category', 'name'),
        'mediums': mediums,
        'selected_medium': medium,
        'selected_tag': tag_id,
        'needs_critique': needs_critique,
    })

@login_required
def upload_artwork(request):
    if request.method == 'POST':
        artwork_form = ArtworkForm(request.POST, request.FILES)
        request_form = CritiqueRequestForm(request.POST)

        if artwork_form.is_valid() and request_form.is_valid():
            # Save the artwork and critique request, associating them with the logged-in user.
            artwork = artwork_form.save(commit=False)
            artwork.user = request.user
            artwork.save()
            artwork_form.save_m2m()

            critique_request = request_form.save(commit=False)
            critique_request.artwork = artwork
            critique_request.save()

            return redirect('artwork_detail', pk=artwork.pk)
    else:
        artwork_form = ArtworkForm()
        request_form = CritiqueRequestForm()

    return render(request, 'artworks/upload.html', {
        'artwork_form': artwork_form,
        'request_form': request_form,
    })

def artwork_detail(request, pk):
    artwork = get_object_or_404(
        Artwork.objects.prefetch_related('critiques__sections', 'tags'),
        pk=pk,
    )
    return render(request, 'artworks/detail.html', {'artwork': artwork})