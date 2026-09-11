from django.contrib import admin
from .models import Artwork, Tag, CritiqueRequest


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'category')
    list_filter = ('category',)


@admin.register(Artwork)
class ArtworkAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'medium', 'critique_status', 'created_at')
    list_filter = ('medium', 'critique_status')
    search_fields = ('title', 'description')


admin.site.register(CritiqueRequest)