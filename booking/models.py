from django.db import models

class Customer(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)

    def __str__(self):
        return self.name
    
class Booking(models.Model):
    SERVICE_CHOICES = [
        ('wedding', 'Wedding'),
        ('portrait', 'Portrait'),
        ('product', 'Product'),
        ('event', 'Event'),
    ]
    CONFIRM = [
        ('approved', 'Approved'),
        ('not approved', 'Not Approved'),
    ]

    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    service = models.CharField(max_length=50, choices=SERVICE_CHOICES)
    date = models.DateField()
    time = models.TimeField()
    message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    approved = models.CharField(max_length=30, choices=CONFIRM, default='not approved')
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    # Tambahkan field baru untuk status pembayaran
    payment_status = models.CharField(
        max_length=20,
        choices=[
            ("unpaid", "Belum Dibayar"),
            ("paid", "Sudah Dibayar"),
            ("pending", "Menunggu Konfirmasi"),
        ],
        default="unpaid",
    )

    def __str__(self):
        return f"{self.name} - {self.service} ({self.date}) - {self.payment_status}"


class CustomerCluster(models.Model):
    user_identifier = models.CharField(max_length=255, default="unknown")  # bisa simpan email atau username
    cluster = models.IntegerField()

    def __str__(self):
        return f"{self.user_identifier} - Cluster {self.cluster}"

