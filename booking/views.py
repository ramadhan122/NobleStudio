from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import BookingForm

# Create your views here.
def booking_view(request):
    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Booking submitted successfully!")
            return redirect('booking')
    else:
        form = BookingForm()
    return render(request, 'booking.html', {'form': form})

