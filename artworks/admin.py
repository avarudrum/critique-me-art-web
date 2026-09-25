from django.contrib import admin
from .models import Artwork, Tag, CritiqueRequest


class CritiqueRequestInline(admin.StackedInline):
    model = CritiqueRequest
    extra = 1


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'category')
    list_filter = ('category',)


@admin.register(Artwork)
class ArtworkAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'mediums', 'critique_status', 'created_at')
    # Medium is a tag now, so filter on the relation instead of a CharField.
    list_filter = ('tags', 'critique_status')
    search_fields = ('title', 'description')
    filter_horizontal = ('tags',)
    inlines = [CritiqueRequestInline]

    def get_queryset(self, request):
        # mediums() reads artwork.tags.all(), so prefetch to avoid a query per row.
        return super().get_queryset(request).prefetch_related('tags')

    @admin.display(description='Medium')
    def mediums(self, obj):
        return ', '.join(obj.medium_names()) or '—'


admin.site.register(CritiqueRequest)