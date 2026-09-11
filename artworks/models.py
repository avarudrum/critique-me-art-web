from django.db import models
from django.conf import settings
from cloudinary.models import CloudinaryField

# Defining the Tag model to categorize artworks by medium, technique, or subject.
class Tag(models.Model):
    CATEGORY_CHOICES = [
        ('medium', 'Medium'),
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
    medium = models.CharField(max_length=50)
    tags = models.ManyToManyField(Tag, blank=True, related_name='artworks')
    critique_status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default='open'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


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