from django.contrib import admin
from .models import Booking
from .models import CustomerClassification


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'date', 'time','message','service', 'submitted_at', 'approved', 'price', 'payment_status')
    search_fields = ('name', 'email', 'phone')
    list_editable = ('price',)  # supaya bisa langsung edit dari list view

@admin.register(CustomerClassification)
class CustomerClassificationAdmin(admin.ModelAdmin):
    list_display = ("id", "user_identifier", "predicted_class")
    list_filter = ("predicted_class",)
    search_fields = ("user_identifier",)
