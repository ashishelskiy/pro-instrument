# banners/views.py
from django.shortcuts import get_object_or_404, redirect
from django.db.models import F
from django.http import HttpResponseRedirect
from .models import Banner


def banner_click(request, pk):
    """Считает клик и редиректит на целевую страницу баннера."""
    banner = get_object_or_404(Banner, pk=pk, is_active=True)
    Banner.objects.filter(pk=pk).update(clicks_count=F('clicks_count') + 1)
    return HttpResponseRedirect(banner.get_link())