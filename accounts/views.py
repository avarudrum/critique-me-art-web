from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView

from artworks.models import Artwork
from critiques.models import Critique
from .forms import ProfileForm, SignUpForm
from .models import User


class SignUpView(CreateView):
    form_class = SignUpForm
    template_name = 'registration/signup.html'
    success_url = reverse_lazy('browse')

    def form_valid(self, form):
        """Log the new account in instead of bouncing them to the login page.

        They just proved they know the password by choosing it; making them
        type it again is friction with nothing behind it.
        """
        response = super().form_valid(form)
        login(self.request, self.object)
        messages.success(
            self.request,
            f"Welcome to Atelier, {self.object.username}.",
        )
        return response


@login_required
def profile(request, username):
    """Everything one person has made: their work, and the critiques they wrote.

    Readable by any signed-in member, not just the owner -- seeing what someone
    has written before is how you judge whether their critique is worth much.
    """
    person = get_object_or_404(User, username=username)

    artworks = (
        Artwork.objects.filter(user=person)
        .prefetch_related('tags', 'critiques')
    )
    critiques = (
        Critique.objects.filter(user=person)
        .select_related('artwork', 'artwork__user')
        .prefetch_related('sections')
    )

    return render(request, 'accounts/profile.html', {
        'person': person,
        'artworks': artworks,
        'critiques': critiques,
        'is_self': person == request.user,
        'artwork_count': artworks.count(),
        'critique_count': critiques.count(),
    })


@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile has been updated.")
            return redirect('profile', username=request.user.username)
    else:
        form = ProfileForm(instance=request.user)

    return render(request, 'accounts/edit_profile.html', {'form': form})
