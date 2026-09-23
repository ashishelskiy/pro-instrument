# pages/urls.py
from django.urls import path
from .views import PageDetailView, NewsListView, NewsDetailView

app_name = 'pages'

urlpatterns = [
    # Новости
    path('news/', NewsListView.as_view(), name='news_list'),
    path('news/<slug:slug>/', NewsDetailView.as_view(), name='news_detail'),
    # Статические страницы — В КОНЦЕ, чтобы не перекрывать другие URL
    path('<slug:slug>/', PageDetailView.as_view(), name='page_detail'),
]