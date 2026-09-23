# pages/views.py
from django.shortcuts import get_object_or_404, render
from django.views.generic import DetailView, ListView
from .models import Page, News


class PageDetailView(DetailView):
    """Статическая страница по slug."""
    model = Page
    template_name = 'pages/page_detail.html'
    context_object_name = 'page'

    def get_queryset(self):
        return Page.objects.filter(is_published=True)


class NewsListView(ListView):
    """Список новостей."""
    model = News
    template_name = 'pages/news_list.html'
    context_object_name = 'news_list'
    paginate_by = 12

    def get_queryset(self):
        return News.objects.filter(is_published=True)


class NewsDetailView(DetailView):
    """Детальная страница новости."""
    model = News
    template_name = 'pages/news_detail.html'
    context_object_name = 'news'

    def get_queryset(self):
        return News.objects.filter(is_published=True)