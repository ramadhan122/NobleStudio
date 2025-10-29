from django.http import HttpResponse
from django.shortcuts import render, redirect
from portfolio.forms import TestimonialForm
from portfolio.models import Photo, Photographer, Testimonial  # pastikan import Photographer
from booking.forms import BookingForm
from booking.models import Booking
from django.views.decorators.http import require_GET
from django.http import JsonResponse
import json
from django.contrib.auth.decorators import login_required
from django.core.serializers.json import DjangoJSONEncoder
from django.contrib import messages

# Create your views here.
def index(request):
    # === Bagian Notifikasi Booking Approved ===
    user_email = request.user.email if request.user.is_authenticated else None

    approved_bookings = []
    if user_email:
        approved_bookings = Booking.objects.filter(
            email=user_email, approved='approved'
        ).order_by('-date')

    # === Bagian Testimonial ===
    testimonials = Testimonial.objects.order_by('-created_at')[:3]

    if request.method == 'POST':
        form = TestimonialForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('index')
    else:
        form = TestimonialForm()

    return render(request, 'index.html', {
        'approved_bookings': approved_bookings,
        'testimonials': testimonials,
        'form': form
    })

def about(request):
    return render(request,'about.html')

def viewall(request):
    photos = Photo.objects.select_related('photographer', 'category').all()
    return render(request, 'viewall.html', {'photos': photos})

def photo_gallery(request):
    photos = Photo.objects.all().select_related('photographer', 'category')
    return render(request, 'viewall.html', {'photos': photos})



def myporto(request):
    photos = Photo.objects.select_related('photographer', 'category').all()
    photographers = Photographer.objects.all()
    return render(request, 'myporto.html', {
        'photos': photos,
        'photographers': photographers
    })

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

def booking_calendar(request):
    bookings = Booking.objects.filter(approved='approved')  # hanya booking yang sudah di-approve

    events = [
        {
            'title': booking.name,
            'start': booking.date.strftime('%Y-%m-%d'),
            'color': 'red'
        }
        for booking in bookings
    ]

    context = {
        'events': json.dumps(events)
    }
    return render(request, 'schedule.html', context)

def home(request):
    testimonials = Testimonial.objects.all()
    return render(request, "index.html", {"testimonials": testimonials})

