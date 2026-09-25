import logging

import cloudinary.uploader
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.conf import settings
from cloudinary.models import CloudinaryField

logger = logging.getLogger(__name__)

# Defining the Tag model to categorize artworks by medium, technique, or subject.
class Tag(models.Model):
    MEDIUM = 'medium'

    CATEGORY_CHOICES = [
        (MEDIUM, 'Medium'),
        ('technique', 'Technique'),
        ('subject', 'Subject'),
    ]
    name = models.CharField(max_length=50, unique=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)

    def __str__(self):
        return f"{self.name} ({self.category})"


class Artwork(models.Model):
    STATUS_CHOICES = [
        ('open', 'Open for critique'),
        ('closed', 'Closed'),
    ]

    # If a user is deleted, their artworks will also be deleted. The related_name allows reverse access from the User model to their artworks.
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='artworks',
    )
    # Information about the artwork, including title, description, image, medium, tags, critique status, and creation timestamp.
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    image = CloudinaryField('artwork')
    # Medium is not a field here: it lives in `tags` as Tag.category == 'medium'.
    # It used to be a free-text CharField, which duplicated the medium tags and
    # produced one-off values like "graphite and charcoal". See medium_names().
    tags = models.ManyToManyField(Tag, blank=True, related_name='artworks')
    critique_status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default='open'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def medium_names(self):
        """The names of this artwork's medium tags.

        Filters in Python rather than with .filter(category=...) on purpose: the
        views already prefetch_related('tags'), so this reuses that cache instead
        of firing another query per artwork on the browse page.
        """
        return [tag.name for tag in self.tags.all() if tag.category == Tag.MEDIUM]


# A signal rather than code in the delete view, so this also runs when an
# Artwork is removed through the admin or cascaded from a deleted user.
# Note: `manage.py flush` does not fire post_delete, so `seed --flush` still
# leaves old uploads in the Cloudinary Media Library.
@receiver(post_delete, sender=Artwork)
def delete_artwork_image(sender, instance, **kwargs):
    public_id = getattr(instance.image, 'public_id', None)
    if not public_id:
        return
    try:
        cloudinary.uploader.destroy(public_id, invalidate=True)
    except Exception:
        # Deliberately broad: the database row is already gone, and a network
        # blip talking to Cloudinary must not surface as a 500 on a delete.
        logger.warning(
            "Could not delete Cloudinary asset %s", public_id, exc_info=True
        )


class CritiqueRequest(models.Model):
    # Artwork can only have one critique request at a time, but can obtain many critiques over time.
    # If the artwork is deleted, the associated critique request will also be deleted.
    artwork = models.OneToOneField(
        Artwork,
        on_delete=models.CASCADE,
        related_name='critique_request',
    )
    focus_areas = models.JSONField(default=list)
    artist_note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Request for {self.artwork.title}"