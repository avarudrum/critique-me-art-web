from django.db import models
from django.conf import settings
from core.constants import FOCUS_AREAS


class Critique(models.Model):
    artwork = models.ForeignKey(
        'artworks.Artwork',
        on_delete=models.CASCADE,
        related_name='critiques',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='critiques',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Critique by {self.user.username} on {self.artwork.title}"


class CritiqueSection(models.Model):
    TYPE_CHOICES = [
        ('strength', 'Strength'),
        ('growth', 'Area for growth'),
    ]
    critique = models.ForeignKey(
        Critique,
        on_delete=models.CASCADE,
        related_name='sections',
    )
    category = models.CharField(max_length=20, choices=FOCUS_AREAS)
    body = models.TextField()
    section_type = models.CharField(max_length=10, choices=TYPE_CHOICES)

    def __str__(self):
        return f"{self.get_category_display()} — {self.get_section_type_display()}"