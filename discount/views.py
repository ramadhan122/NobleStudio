from django.http import HttpResponse

from booking.models import Booking
from discount.models import UserDiscount
from .messages import discount_wa_message
from .utils import send_wa_fonnte
from django.shortcuts import redirect, render



def index(request):
    return HttpResponse("app discount aktif")

def create_discount(request):
    if request.method == 'POST':
        booking = Booking.objects.get(id=request.POST['booking'])

        discount = UserDiscount.objects.create(
            booking=booking,
            discount_type=request.POST['discount_type'],
            discount_value=request.POST['discount_value'],
            description=request.POST.get('description', ''),
            expired_at=request.POST['expired_at'],
            is_active=True
        )

        if booking.phone and not discount.wa_sent:
            message = discount_wa_message(booking, discount)
            send_wa_fonnte(booking.phone, message)

            discount.wa_sent = True
            discount.save()

        return redirect('admin_discount_list')


# Create your views here.
