# cart/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from catalog.models import Product
from .models import Cart, CartItem


@login_required
def cart_detail(request):
    """Страница корзины."""
    cart, created = Cart.objects.get_or_create(user=request.user)
    return render(request, 'cart/cart_detail.html', {'cart': cart})


@login_required
@require_POST
def cart_add(request, product_id):
    """Добавить товар в корзину."""
    product = get_object_or_404(Product, id=product_id)
    cart, created = Cart.objects.get_or_create(user=request.user)
    item, created = CartItem.objects.get_or_create(cart=cart, product=product)

    # Получаем количество из формы
    try:
        quantity = int(request.POST.get('quantity', 1))
    except (TypeError, ValueError):
        quantity = 1

    # Ограничиваем: минимум 1, максимум 999
    quantity = max(1, min(quantity, 999))

    if not created:
        item.quantity += quantity
    else:
        item.quantity = quantity
    item.save()

    messages.success(request, f'«{product.name}» добавлен в корзину ({quantity} шт.)')
    return redirect(request.META.get('HTTP_REFERER', 'cart:cart_detail'))


@login_required
@require_POST
def cart_remove(request, item_id):
    """Удалить товар из корзины."""
    item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    item.delete()
    messages.success(request, 'Товар удалён из корзины')
    return redirect('cart:cart_detail')


@login_required
@require_POST
def cart_update(request, item_id):
    """Обновить количество товара."""
    item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    try:
        quantity = int(request.POST.get('quantity', 1))
    except (TypeError, ValueError):
        quantity = 1
    if quantity > 0:
        item.quantity = quantity
        item.save()
    else:
        item.delete()
    return redirect('cart:cart_detail')