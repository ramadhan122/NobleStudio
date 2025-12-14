from django.contrib import admin
from .models import UserDiscount

@admin.register(UserDiscount)
class UserDiscountAdmin(admin.ModelAdmin):
    autocomplete_fields = ['user']
    list_display = (
        'user',
        'discount_type',
        'discount_value',
        'is_active',
        'expired_at',
        'created_at',
    )
    list_filter = ('discount_type', 'is_active')
# Register your models here.
