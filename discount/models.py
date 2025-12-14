from django.db import models
from django.contrib.auth.models import User
# Create your models here.

class UserDiscount(models.Model):
    DISCOUNT_TYPE = {
        ('percent', 'Persen'),
        ('nominal', 'Nominal'),
    }

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    discount_type = models.CharField(max_length=10, choices=DISCOUNT_TYPE)
    discount_value = models.PositiveIntegerField()
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    expired_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.discount_value}"