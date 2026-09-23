# users/context_processors.py
from .models import Favorite, StockNotification



def favorites_count(request):
    """Добавляет в контекст шаблона количество товаров в избранном."""
    if request.user.is_authenticated:
        return {
            'favorites_count': Favorite.objects.filter(user=request.user).count()
        }
    return {'favorites_count': 0}


def user_favorite_ids(request):
    """Множество ID товаров, которые пользователь добавил в избранное."""
    if request.user.is_authenticated:
        ids = set(
            Favorite.objects.filter(user=request.user).values_list('product_id', flat=True)
        )
        return {'user_favorite_ids': ids}
    return {'user_favorite_ids': set()}


def user_stock_notification_ids(request):
    """Множество ID товаров, на которые пользователь подписан."""
    if request.user.is_authenticated:
        ids = set(
            StockNotification.objects.filter(
                user=request.user
            ).values_list('product_id', flat=True)
        )
        return {'user_stock_notification_ids': ids}
    return {'user_stock_notification_ids': set()}


def user_comparison_ids(request):
    """ID товаров, которые пользователь добавил в сравнение."""
    from .models import Comparison
    if request.user.is_authenticated:
        ids = set(
            Comparison.objects.filter(user=request.user).values_list('product_id', flat=True)
        )
        return {'user_comparison_ids': ids}
    return {'user_comparison_ids': set()}


def comparison_count(request):
    """Количество товаров в сравнении."""
    from .models import Comparison
    if request.user.is_authenticated:
        return {
            'comparison_count': Comparison.objects.filter(user=request.user).count()
        }
    return {'comparison_count': 0}