from django.contrib import admin
from .models import Hall, Club, Review

@admin.register(Hall)
class HallAdmin(admin.ModelAdmin):
    list_display = ('name', 'address', 'hall_type', 'price_per_hour')
    list_filter = ('hall_type', 'coating', 'dressing_room')
    search_fields = ('name', 'address')

@admin.register(Club)
class ClubAdmin(admin.ModelAdmin):
    list_display = ('name', 'coach', 'price_per_month', 'hall')
    list_filter = ('age_groups', 'hall')
    search_fields = ('name', 'coach')

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('author', 'rating', 'hall', 'club', 'created_at')
    list_filter = ('rating', 'hall', 'club')
    search_fields = ('text',)