from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    # Capped like Artwork.description: form-level validation plus a maxlength
    # on the textarea, so a profile can't become a wall of text.
    bio = models.TextField(blank=True, max_length=600)
    primary_medium = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.username