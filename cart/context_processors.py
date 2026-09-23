# cart/context_processors.py
from .models import Cart


def cart_count(request):
    """Добавляет в контекст всех шаблонов количество товаров в корзине."""
    if request.user.is_authenticated:
        try:
            cart = request.user.cart
            return {'cart_total_items': cart.total_items}
        except Cart.DoesNotExist:
            return {'cart_total_items': 0}
    return {'cart_total_items': 0}