# pages/context_processors.py
from .models import SiteSettings


def site_settings(request):
    """Добавляет настройки сайта в контекст всех шаблонов."""
    return {'site_settings': SiteSettings.get()}