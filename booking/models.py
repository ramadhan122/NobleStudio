from django.db import models

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
    submitted_at = models.DateTimeField(auto_now=True)
    approved = models.CharField(max_length=30, choices=CONFIRM, default='not approved')
  # Field to indicate if the booking is approved

    def __str__(self):
        return f"{self.name} - {self.service} on {self.date}"
