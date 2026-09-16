from django.contrib import admin
from .models import Critique, CritiqueSection


class CritiqueSectionInline(admin.TabularInline):
    model = CritiqueSection
    extra = 0

# Nesting critique sections within the critique admin 
@admin.register(Critique)
class CritiqueAdmin(admin.ModelAdmin):
    list_display = ('user', 'artwork', 'created_at')
    inlines = [CritiqueSectionInline]