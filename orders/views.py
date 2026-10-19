# orders/views.py
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect
from django.views.generic import CreateView
from django.urls import reverse_lazy
from django.db import transaction
from cart.models import Cart
from .models import Order, OrderItem, DeliveryMethod
from .forms import OrderForm

from tbank_securepay import PaymentInitParams, TKassaClient
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json

class OrderCreateView(CreateView):
    """Оформление заказа."""
    form_class = OrderForm
    template_name = 'orders/order_form.html'
    success_url = reverse_lazy('orders:order_success')

    def dispatch(self, request, *args, **kwargs):
        # Проверяем, что корзина не пуста
        if request.user.is_authenticated:
            try:
                cart = request.user.cart
                if not cart.items.exists():
                    messages.warning(request, 'Корзина пуста — добавьте товары')
                    return redirect('cart:cart_detail')
            except Cart.DoesNotExist:
                messages.warning(request, 'Корзина пуста — добавьте товары')
                return redirect('catalog:index')
        else:
            messages.warning(request, 'Войдите, чтобы оформить заказ')
            return redirect('users:login')

        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        """Предзаполняем из профиля."""
        initial = super().get_initial()
        user = self.request.user
        initial['name'] = user.get_full_name() or user.username
        initial['phone'] = user.phone or ''
        initial['email'] = user.email or ''
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart = self.request.user.cart
        context['cart'] = cart
        context['organization'] = self.request.user.default_organization

        # Список способов доставки для JS
        context['delivery_methods_json'] = [
            {'id': d.pk, 'price': float(d.price)}
            for d in DeliveryMethod.objects.filter(is_active=True)
        ]

        return context

    @transaction.atomic
    def form_valid(self, form):
        user = self.request.user
        cart = user.cart

        # Создаём заказ
        order = form.save(commit=False)
        order.user = user
        order.organization = user.default_organization

        # Снимок способа доставки и стоимость
        delivery = form.cleaned_data.get('delivery_method')
        # if delivery:
        #     order.delivery_method_name = delivery.name
        #     order.delivery_price = delivery.price
        # else:
        #     order.delivery_method_name = ''
        #     order.delivery_price = 0

        # Если не выбрано — берём самовывоз по умолчанию
        if not delivery:
            delivery = DeliveryMethod.objects.filter(
                name__iexact='Самовывоз',
                is_active=True
            ).first()

        if delivery:
            order.delivery_method = delivery
            order.delivery_method_name = delivery.name
            order.delivery_price = delivery.price
        else:
            order.delivery_method_name = 'Самовывоз'
            order.delivery_price = 0

        # Итого = товары + доставка
        order.total_price = cart.total_price + order.delivery_price
        order.save()

        # Переносим позиции из корзины
        for item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=item.product,
                product_name=item.product.name,
                product_article=item.product.article,
                price=item.product.price,
                quantity=item.quantity,
            )

        # Очищаем корзину
        cart.items.all().delete()

        # === ПИСЬМА ===
        self._send_order_emails(order)

        messages.success(self.request, f'Заказ №{order.pk} оформлен!')
        self.request.session['last_order_id'] = order.pk

        # === НОВОЕ: создаём платёж в Т-Банке ===
        # if order.payment_method == 'card':
        #     with TKassaClient(
        #             terminal_key=settings.TBANK_TERMINAL_KEY,
        #             password=settings.TBANK_PASSWORD
        #     ) as client:
        #         result = client.payment_init(
        #             PaymentInitParams(
        #                 amount=int(order.total_price * 100),  # в копейках
        #                 order_id=str(order.pk),
        #                 description=f"Оплата заказа №{order.pk}",
        #             )
        #         )
        #         if result.success:
        #             order.payment_id = result.payment_id
        #             order.save(update_fields=['payment_id'])
        #             # Редирект на страницу оплаты банка
        #             return redirect(result.payment_url)
        #         else:
        #             messages.error(self.request, f'Ошибка платежа: {result.message}')
        #             return redirect('orders:order_success')

        if order.payment_method == 'card':
            with TKassaClient(
                    terminal_key=settings.TBANK_TERMINAL_KEY,
                    password=settings.TBANK_PASSWORD
            ) as client:
                # Увеличиваем счетчик попыток
                order.payment_attempts += 1
                order.save(update_fields=['payment_attempts'])

                # Формируем уникальный OrderId: "21_1"
                current_order_id = f"{order.pk}_{order.payment_attempts}"

                result = client.payment_init(
                    PaymentInitParams(
                        amount=int(order.total_price * 100),
                        order_id=current_order_id,
                        description=f"Оплата заказа №{order.pk} (попытка {order.payment_attempts})",
                    )
                )
                if result.success:
                    order.payment_id = result.payment_id
                    order.save(update_fields=['payment_id'])
                    return redirect(result.payment_url)
                else:
                    messages.error(self.request, f'Ошибка платежа: {result.message}')
                    return redirect('orders:order_success')

        return super().form_valid(form)

    def _send_order_emails(self, order):
        """Отправляет письма админу и клиенту о новом заказе."""

        # 1. Письмо админу — через HTML-шаблон
        try:
            context = {
                'order': order,
                'site_url': settings.SITE_URL,
            }
            subject = f'🆕 Новый заказ №{order.pk} на {order.total_price} ₽'

            text_content = render_to_string('emails/order_admin.txt', context)
            html_content = render_to_string('emails/order_admin.html', context)

            msg = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[settings.ADMIN_EMAIL],
            )
            msg.attach_alternative(html_content, 'text/html')
            msg.send(fail_silently=True)
        except Exception:
            pass

        # 2. Письмо клиенту
        try:
            context = {
                'order': order,
                'site_url': settings.SITE_URL,
            }
            subject = f'Заказ №{order.pk} принят — PRO-Инструмент'

            text_content = render_to_string('emails/order_client.txt', context)
            html_content = render_to_string('emails/order_client.html', context)

            msg = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[order.email],
            )
            msg.attach_alternative(html_content, 'text/html')
            msg.send(fail_silently=True)
        except Exception:
            pass


def order_success(request):
    """Страница «Спасибо за заказ»."""
    order_id = request.session.pop('last_order_id', None)
    order = None
    if order_id:
        try:
            order = Order.objects.get(pk=order_id, user=request.user)
        except Order.DoesNotExist:
            pass
    return render(request, 'orders/order_success.html', {'order': order})


@login_required
def order_invoice(request, pk):
    """Печатная форма счёта."""
    order = get_object_or_404(Order, pk=pk)

    # Проверяем доступ — свой заказ или staff
    if order.user != request.user and not request.user.is_staff:
        return redirect('home')

    return render(request, 'orders/invoice.html', {'order': order})


# def pay_order(request, pk):
#     """Повторная попытка оплаты для неоплаченного заказа."""
#     order = get_object_or_404(Order, pk=pk, user=request.user)
#
#     if not order.can_be_paid:
#         messages.warning(request, 'Этот заказ уже оплачен или не может быть оплачен.')
#         return redirect('orders:order_success')  # или туда, где список заказов
#
#     with TKassaClient(
#         terminal_key=settings.TBANK_TERMINAL_KEY,
#         password=settings.TBANK_PASSWORD
#     ) as client:
#         # Т-Банк не любит повторные OrderId, поэтому делаем уникальный
#         import uuid
#         unique_order_id = f"{order.pk}_{uuid.uuid4().hex[:6]}"
#
#         result = client.payment_init(
#             PaymentInitParams(
#                 amount=int(order.total_price * 100),
#                 order_id=unique_order_id,
#                 description=f"Повторная оплата заказа №{order.pk}",
#             )
#         )
#         if result.success:
#             order.payment_id = result.payment_id
#             order.save(update_fields=['payment_id'])
#             return redirect(result.payment_url)
#         else:
#             messages.error(request, f'Ошибка платежа: {result.message}')
#             return redirect('orders:order_success')  # или на страницу заказов

def pay_order(request, pk):
    """Повторная попытка оплаты для неоплаченного заказа."""
    order = get_object_or_404(Order, pk=pk, user=request.user)

    if not order.can_be_paid:
        messages.warning(request, 'Этот заказ уже оплачен, отменен или превышен лимит попыток.')
        return redirect('users:orders')  # Убедитесь, что этот URL существует!

    with TKassaClient(
            terminal_key=settings.TBANK_TERMINAL_KEY,
            password=settings.TBANK_PASSWORD
    ) as client:
        # Увеличиваем счетчик попыток
        order.payment_attempts += 1
        order.save(update_fields=['payment_attempts'])

        # Формируем уникальный OrderId: "21_2"
        current_order_id = f"{order.pk}_{order.payment_attempts}"

        result = client.payment_init(
            PaymentInitParams(
                amount=int(order.total_price * 100),
                order_id=current_order_id,
                description=f"Повторная оплата заказа №{order.pk} (попытка {order.payment_attempts})",
            )
        )
        if result.success:
            order.payment_id = result.payment_id
            order.save(update_fields=['payment_id'])
            return redirect(result.payment_url)
        else:
            messages.error(request, f'Ошибка платежа: {result.message}')
            return redirect('users:orders')


# ============================================================
# СИГНАЛЫ: уведомление о поступлении
# ============================================================

from django.db.models.signals import post_save
from django.dispatch import receiver
from catalog.models import Product
from users.models import StockNotification
from django.utils import timezone


@receiver(post_save, sender=Product)
def notify_stock_arrival(sender, instance, created, **kwargs):
    """Когда товар появляется в наличии — рассылаем уведомления подписчикам."""
    if not instance.in_stock:
        return

    # Ищем непроуведомлённые подписки
    notifications = StockNotification.objects.filter(
        product=instance,
        notified=False,
    ).select_related('user')

    # for n in notifications:
    #     try:
    #         send_mail(
    #             subject=f'🔔 Товар «{instance.name[:60]}» снова в наличии',
    #             message=(
    #                 f'Здравствуйте!\n\n'
    #                 f'Товар, который вы ждали, снова в наличии:\n\n'
    #                 f'• {instance.name}\n'
    #                 f'• Артикул: {instance.article or "—"}\n'
    #                 f'• Цена: {instance.price} ₽\n\n'
    #                 f'Ссылка: https://pro-instrument.ru{instance.get_absolute_url()}\n\n'
    #                 f'Спешите оформить заказ — количество ограничено.\n\n'
    #                 f'С уважением,\n'
    #                 f'команда PRO-инструмент'
    #             ),
    #             from_email=settings.DEFAULT_FROM_EMAIL,
    #             recipient_list=[n.email],
    #             fail_silently=True,
    #         )
    #         n.notified = True
    #         n.notified_at = timezone.now()
    #         n.save(update_fields=['notified', 'notified_at'])
    #     except Exception:
    #         pass
    for n in notifications:
        try:
            context = {
                'product': instance,
                'site_url': settings.SITE_URL,
            }
            subject = f'🔔 Товар «{instance.name[:60]}» снова в наличии'

            text_content = render_to_string('emails/stock_arrival.txt', context)
            html_content = render_to_string('emails/stock_arrival.html', context)

            msg = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[n.email],
            )
            msg.attach_alternative(html_content, 'text/html')
            msg.send(fail_silently=True)

            n.notified = True
            n.notified_at = timezone.now()
            n.save(update_fields=['notified', 'notified_at'])
        except Exception:
            pass

import hashlib
import json
import logging

logger = logging.getLogger(__name__)


def _check_tbank_token(data, password):
    token_from_bank = data.get('Token')
    if not token_from_bank:
        return False

    excluded = {'Token', 'Data', 'ForeignReceiver', 'Receipt'}
    check_data = {}
    for k, v in data.items():
        if k in excluded or v is None:
            continue
        # Булевы значения приводим к строке в нижнем регистре
        if isinstance(v, bool):
            check_data[k] = 'true' if v else 'false'
        else:
            check_data[k] = str(v)

    check_data['Password'] = password

    concatenated = ''.join(check_data[k] for k in sorted(check_data.keys()))
    calculated = hashlib.sha256(concatenated.encode('utf-8')).hexdigest()

    return calculated == token_from_bank


@csrf_exempt
def tbank_webhook(request):
    """Обработка уведомлений от Т-Банка."""
    logger.warning("TBANK WEBHOOK START: method=%s", request.method)

    if request.method != 'POST':
        return HttpResponse(status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError as e:
        logger.warning("TBANK WEBHOOK: JSON error: %s", e)
        return HttpResponse(status=400)

    logger.warning("TBANK WEBHOOK DATA: %s", data)

    # Проверка подписи вручную
    if not _check_tbank_token(data, settings.TBANK_PASSWORD):
        logger.warning("TBANK WEBHOOK: invalid token")
        return HttpResponse(status=403)

    # status = data.get('Status')
    # order_id = data.get('OrderId')
    # logger.warning("TBANK WEBHOOK: status=%s, order_id=%s", status, order_id)
    #
    # if status in ('CONFIRMED', 'AUTHORIZED'):
    #     Order.objects.filter(pk=order_id).update(paid=True)
    #
    # return HttpResponse('OK', content_type='text/plain')

    status = data.get('Status')
    order_id_raw = data.get('OrderId')
    logger.warning("TBANK WEBHOOK: status=%s, order_id=%s", status, order_id_raw)

    if status in ('CONFIRMED', 'AUTHORIZED'):
        # Извлекаем настоящий pk: "21_1" -> "21"
        real_order_id = str(order_id_raw).split('_')[0]

        # Ставим оплату и меняем статус
        Order.objects.filter(pk=real_order_id).update(paid=True, status='processing')

    return HttpResponse('OK', content_type='text/plain')
