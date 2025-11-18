from django.urls import path
from . import views

urlpatterns = [
    path("classification/", views.run_customer_clustering, name="classification"),
    path('train_from_csv/', views.train_from_csv, name='train_from_csv'),  # ⬅️ tambahkan baris ini
    path('booking/<int:booking_id>/', views.booking_detail, name='booking_detail'),
]
