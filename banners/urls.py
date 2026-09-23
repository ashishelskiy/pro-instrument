# banners/urls.py
from django.urls import path
from . import views

app_name = 'banners'

urlpatterns = [
    path('click/<int:pk>/', views.banner_click, name='click'),
]