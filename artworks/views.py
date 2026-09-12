from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from .forms import ArtworkForm, CritiqueRequestForm
from .models import Artwork


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
    # Retrieve the artwork by its primary key or return a 404 error if not found.
    artwork = get_object_or_404(Artwork, pk=pk)
    return render(request, 'artworks/detail.html', {'artwork': artwork})