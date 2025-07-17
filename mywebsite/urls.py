from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from . import views
from portfolio.views import photo_gallery

urlpatterns = [
    path('admin/', admin.site.urls),
    path('about/', views.about),
    path('myporto/', views.myporto),
    path('viewall/', photo_gallery),
    path('gallery/', photo_gallery, name='photo_gallery'),
    path('', views.index, name='index'),
    path('booking/', views.booking_view, name='booking'),
    path('schedule/', views.booking_calendar, name='booking_calendar'),

    # Authentication URLs
    path('auth/', include('authentication.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
