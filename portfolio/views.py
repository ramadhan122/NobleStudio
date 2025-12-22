from django.shortcuts import render
from .models import Work

def portfolio_view(request):
    works = Work.objects.select_related('photographer', 'category').all()
    return render(request, 'myporto.html', {'works': works})

def photo_gallery(request):
    works = Work.objects.all().select_related('photographer', 'category')
    return render(request, 'viewall.html', {'works': works})
