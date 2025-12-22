from django.contrib import admin

# Register your models here.
from .models import Photographer, Category, Work, Testimonial

@admin.register(Photographer)
class PhotographerAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_email','bio', 'phone', 'instagram', 'created_at')
    search_fields = ('name', 'contact_email')
    list_filter = ('created_at',)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Work)
class WorkAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'photographer','image_url','description', 'shoot_date', 'created_at')
    list_filter = ('category', 'photographer', 'shoot_date')
    search_fields = ('title', 'description')

@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ('name', 'role', 'rating', 'created_at')
    search_fields = ('name', 'role')
    list_filter = ('rating', 'created_at')
    ordering = ('-created_at',)

