from django.contrib import admin
from .models import Booking

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'date', 'time','message','service', 'submitted_at', 'approved')
    search_fields = ('name', 'email')
    list_filter = ('date', 'approved')
