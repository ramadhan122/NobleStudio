from django.shortcuts import render
from .models import Photo

def portfolio_view(request):
    photos = Photo.objects.select_related('photographer', 'category').all()
    return render(request, 'myporto.html', {'photos': photos})

def photo_gallery(request):
    photos = Photo.objects.all().select_related('photographer', 'category')
    return render(request, 'viewall.html', {'photos': photos})
