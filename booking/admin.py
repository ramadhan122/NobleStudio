from django.contrib import admin
from .models import Booking
from .models import CustomerCluster


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'date', 'time','message','service', 'submitted_at', 'approved', 'price', 'payment_status')
    search_fields = ('name', 'email', 'phone')
    list_editable = ('price',)  # supaya bisa langsung edit dari list view

@admin.register(CustomerCluster)
class CustomerClusterAdmin(admin.ModelAdmin):
    list_display = ("id", "user_identifier", "cluster")
    list_filter = ("cluster",)
    search_fields = ("user_identifier",)  # cari berdasarkan email