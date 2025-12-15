from django.contrib import admin
from .models import UserDiscount
from .services import send_discount_whatsapp

@admin.register(UserDiscount)
class UserDiscountAdmin(admin.ModelAdmin):
    list_display = (
        'booking',
        'discount_type',
        'discount_value',
        'expired_at',
        'is_active',
        'created_at',
    )

    search_fields = (
        'booking.name',
        'booking.email',
        'booking.phone',
    )

    autocomplete_fields = ['booking']

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        # kirim WA HANYA SAAT DISKON AKTIF
        if obj.is_active:
            send_discount_whatsapp(obj.booking, obj)
