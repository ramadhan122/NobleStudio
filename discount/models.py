from django.db import models
from booking.models import Booking

class UserDiscount(models.Model):
    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        related_name='discounts'
    )

    discount_type = models.CharField(
        max_length=10,
        choices=(('percent', 'Percent'), ('nominal', 'Nominal'))
    )
    discount_value = models.IntegerField()
    expired_at = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.booking} - {self.discount_value}"
