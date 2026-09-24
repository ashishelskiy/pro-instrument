# users/views.py
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import PasswordChangeView
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import View
from django.views.decorators.http import require_POST
from django.views.generic import (
    DetailView, UpdateView, TemplateView, CreateView, ListView, DeleteView,
)
from .models import (
    User, Organization, Favorite, StockNotification,
    PriceRequest, ViewedProduct, Comparison,
)
from .forms import (
    CustomUserCreationForm, UserProfileForm, OrganizationForm,
    StockNotificationForm, PriceRequestForm,
)


# ============================================================
# ХЕЛПЕР: безопасный возврат на ту же страницу
# ============================================================

def _safe_referer(request, fallback='users:organizations'):
    """
    Возвращает URL для redirect:
    - HTTP_REFERER, если он есть и ведёт на тот же хост
    - иначе — fallback (по умолчанию 'users:organizations')
    """
    referer = request.META.get('HTTP_REFERER', '')
    if referer and url_has_allowed_host_and_scheme(
        referer, allowed_hosts={request.get_host()}
    ):
        return referer
    return fallback


# ============================================================
# ЛИЧНЫЙ КАБИНЕТ
# ============================================================

class ProfileView(LoginRequiredMixin, DetailView):
    model = User
    template_name = 'users/profile.html'
    context_object_name = 'user_profile'

    def get_object(self):
        return self.request.user


class ProfileEditView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserProfileForm
    template_name = 'users/profile_edit.html'
    success_url = reverse_lazy('users:profile')

    def get_object(self):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, 'Профиль успешно обновлён!')
        return super().form_valid(form)


class MyPasswordChangeView(PasswordChangeView):
    template_name = 'users/password_change.html'
    success_url = reverse_lazy('users:profile_edit')

    def form_valid(self, form):
        messages.success(self.request, 'Пароль успешно изменён.')
        return super().form_valid(form)


class OrdersView(LoginRequiredMixin, ListView):
    template_name = 'users/orders.html'
    context_object_name = 'orders'
    paginate_by = 10

    def get_queryset(self):
        from orders.models import Order
        return Order.objects.filter(user=self.request.user).prefetch_related('items')


class OrderDocumentsView(LoginRequiredMixin, ListView):
    template_name = 'users/order_documents.html'
    context_object_name = 'orders'
    paginate_by = 20

    def get_queryset(self):
        from orders.models import Order
        return Order.objects.filter(user=self.request.user).prefetch_related('items')


class PurchaseHistoryView(LoginRequiredMixin, TemplateView):
    """История покупок — уникальные товары из заказов пользователя."""
    template_name = 'users/purchase_history.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from orders.models import OrderItem
        from collections import OrderedDict

        # Все позиции из заказов пользователя
        items = OrderItem.objects.filter(
            order__user=self.request.user,
            product__isnull=False,
        ).select_related('product', 'order').order_by('-order__created_at')

        # Группируем по товару
        history = OrderedDict()
        for item in items:
            pid = item.product_id
            if pid not in history:
                history[pid] = {
                    'product': item.product,
                    'total_quantity': 0,
                    'orders_count': 0,
                    'last_bought': item.order.created_at,
                }
            history[pid]['total_quantity'] += item.quantity
            history[pid]['orders_count'] += 1
            # Обновляем дату — берём самую свежую
            if item.order.created_at > history[pid]['last_bought']:
                history[pid]['last_bought'] = item.order.created_at

        context['history'] = list(history.values())
        return context


class FavoritesView(LoginRequiredMixin, TemplateView):
    template_name = 'users/favorites.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        favorites = Favorite.objects.filter(
            user=self.request.user
        ).select_related('product')
        context['favorites'] = [f.product for f in favorites]
        return context


class CartView(LoginRequiredMixin, TemplateView):
    def get(self, request):
        return redirect('cart:cart_detail')


class ViewedView(LoginRequiredMixin, TemplateView):
    template_name = 'users/viewed.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        viewed = ViewedProduct.objects.filter(
            user=self.request.user
        ).select_related('product').order_by('-viewed_at')[:50]
        context['viewed_products'] = [v.product for v in viewed]
        return context


class SupportView(LoginRequiredMixin, TemplateView):
    template_name = 'users/support.html'


class RegisterView(CreateView):
    form_class = CustomUserCreationForm
    template_name = 'registration/register.html'
    success_url = reverse_lazy('users:login')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('/')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        # Приветственное письмо
        try:
            send_mail(
                subject='Добро пожаловать в PRO-инструмент!',
                message=(
                    f'Здравствуйте, {self.object.get_display_name()}!\n\n'
                    f'Спасибо за регистрацию на сайте pro-instrument.ru.\n\n'
                    f'Теперь вы можете:\n'
                    f'• добавлять товары в корзину и оформлять заказы;\n'
                    f'• сохранять товары в избранное;\n'
                    f'• подписываться на уведомления о поступлении;\n'
                    f'• добавлять организации для заказа от юрлица.\n\n'
                    f'Ваш логин: {self.object.username}\n\n'
                    f'С уважением,\n'
                    f'команда PRO-инструмент\n'
                    f'https://pro-instrument.ru'
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[self.object.email],
                fail_silently=True,
            )
        except Exception:
            pass
        return response

@require_POST
def account_delete(request):
    user = request.user
    logout(request)
    user.delete()
    messages.success(request, 'Аккаунт удалён.')
    return redirect('home')


# ============================================================
# ОРГАНИЗАЦИИ
# ============================================================

class OrganizationListView(LoginRequiredMixin, ListView):
    model = Organization
    template_name = 'users/organization_list.html'
    context_object_name = 'organizations'

    def get_queryset(self):
        return Organization.objects.filter(user=self.request.user)


class OrganizationCreateView(LoginRequiredMixin, CreateView):
    model = Organization
    form_class = OrganizationForm
    template_name = 'users/organization_form.html'
    success_url = reverse_lazy('users:organizations')

    def get_initial(self):
        """Если в GET передан org_type — подставляем в форму."""
        initial = super().get_initial()
        org_type = self.request.GET.get('org_type')
        if org_type in ('ooo', 'ip'):
            initial['org_type'] = org_type
        return initial

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Добавить организацию'
        context['button_text'] = 'Добавить'
        context['current_org_type'] = self._current_org_type()
        return context

    def _current_org_type(self):
        if self.request.POST:
            return self.request.POST.get('org_type', 'ooo')
        return self.request.GET.get('org_type', 'ooo')


class OrganizationUpdateView(LoginRequiredMixin, UpdateView):
    model = Organization
    form_class = OrganizationForm
    template_name = 'users/organization_form.html'
    success_url = reverse_lazy('users:organizations')

    def get_queryset(self):
        return Organization.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Редактировать организацию'
        context['button_text'] = 'Сохранить'
        context['current_org_type'] = self._current_org_type()
        return context

    def _current_org_type(self):
        if self.request.POST:
            return self.request.POST.get('org_type', 'ooo')
        if self.request.GET.get('org_type') in ('ooo', 'ip'):
            return self.request.GET.get('org_type')
        return self.object.org_type if self.object else 'ooo'


class OrganizationDeleteView(LoginRequiredMixin, DeleteView):
    model = Organization
    template_name = 'users/organization_confirm_delete.html'
    success_url = reverse_lazy('users:organizations')

    def get_queryset(self):
        return Organization.objects.filter(user=self.request.user)

    def form_valid(self, form):
        org = self.get_object()
        was_default = org.is_default
        response = super().form_valid(form)
        if was_default:
            next_org = Organization.objects.filter(user=self.request.user).first()
            if next_org:
                next_org.is_default = True
                next_org.save()
        return response


class OrganizationSetDefaultView(LoginRequiredMixin, View):
    def post(self, request, pk):
        org = get_object_or_404(Organization, pk=pk, user=request.user)
        org.is_default = True
        org.save()
        messages.success(request, f'Организация «{org.name}» выбрана основной.')
        return redirect(_safe_referer(request))


@require_POST
def organization_unset_default(request):
    """Сбрасывает основную организацию — заказ от физлица."""
    Organization.objects.filter(user=request.user, is_default=True).update(is_default=False)
    messages.success(request, 'Заказы оформляются от физлица.')
    return redirect(_safe_referer(request))


# ============================================================
# ИЗБРАННОЕ
# ============================================================

@login_required
@require_POST
def favorite_add(request, product_id):
    """Добавить товар в избранное."""
    from catalog.models import Product
    product = get_object_or_404(Product, id=product_id)
    Favorite.objects.get_or_create(user=request.user, product=product)
    messages.success(request, f'«{product.name}» добавлен в избранное')
    return redirect(request.META.get('HTTP_REFERER', 'catalog:index'))


@login_required
@require_POST
def favorite_remove(request, product_id):
    """Удалить товар из избранного."""
    Favorite.objects.filter(user=request.user, product_id=product_id).delete()
    messages.success(request, 'Товар удалён из избранного')
    return redirect(request.META.get('HTTP_REFERER', 'users:favorites'))


# ============================================================
# УВЕДОМЛЕНИЕ О ПОСТУПЛЕНИИ
# ============================================================

@login_required
@require_POST
def stock_notification_add(request, product_id):
    """Подписка на уведомление о поступлении товара."""
    from catalog.models import Product
    product = get_object_or_404(Product, id=product_id)

    form = StockNotificationForm(request.POST)
    if form.is_valid():
        email = form.cleaned_data['email']
        notification, created = StockNotification.objects.get_or_create(
            email=email,
            product=product,
            defaults={
                'user': request.user if request.user.is_authenticated else None,
            },
        )
        if created:
            messages.success(request, f'Вы подписаны на уведомление о поступлении «{product.name}»')
        else:
            messages.info(request, 'Вы уже подписаны на уведомление о поступлении этого товара')
    else:
        messages.error(request, 'Проверьте правильность email')

    return redirect(request.META.get('HTTP_REFERER', 'catalog:index'))


@login_required
@require_POST
def stock_notification_remove(request, pk):
    """Удалить подписку."""
    notification = get_object_or_404(
        StockNotification, pk=pk, user=request.user
    )
    product_name = notification.product.name
    notification.delete()
    messages.success(request, f'Вы отписаны от «{product_name}»')
    return redirect('users:stock_notifications')


@login_required
@require_POST
def stock_notification_remove_by_product(request, product_id):
    """Отписаться от уведомления по ID товара (для карточек и страницы товара)."""
    StockNotification.objects.filter(
        user=request.user, product_id=product_id
    ).delete()
    messages.success(request, 'Вы отписаны от уведомления')
    return redirect(request.META.get('HTTP_REFERER', 'catalog:index'))


class StockNotificationsView(LoginRequiredMixin, TemplateView):
    """Подписки пользователя на поступление товаров."""
    template_name = 'users/stock_notifications.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        notifications = StockNotification.objects.filter(
            user=self.request.user
        ).select_related('product').order_by('-created_at')
        context['notifications'] = notifications
        return context


# ============================================================
# ЗАПРОС ЦЕНЫ
# ============================================================

class PriceRequestView(CreateView):
    """Страница заявки «Запросить цену»."""
    form_class = PriceRequestForm
    template_name = 'users/price_request.html'
    success_url = reverse_lazy('users:price_request_success')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        if self.request.user.is_authenticated:
            form.instance.user = self.request.user
            if not form.cleaned_data.get('name'):
                form.instance.name = self.request.user.get_full_name() or self.request.user.username
            if not form.cleaned_data.get('phone'):
                form.instance.phone = self.request.user.phone or ''
            if not form.cleaned_data.get('email'):
                form.instance.email = self.request.user.email

        response = super().form_valid(form)

        # === ПИСЬМА ===
        self._send_price_request_emails(self.object)

        return response

    def _send_price_request_emails(self, price_request):
        """Письма админу и клиенту о новой заявке на цену."""

        # 1. Письмо админу
        try:
            send_mail(
                subject=f'📩 Новая заявка на цену от {price_request.name}',
                message=(
                    f'Новая заявка на цену №{price_request.pk}\n'
                    f'Дата: {price_request.created_at:%d.%m.%Y %H:%M}\n\n'
                    f'Клиент: {price_request.name}\n'
                    f'Телефон: {price_request.phone or "—"}\n'
                    f'Email: {price_request.email}\n\n'
                    f'Описание товара:\n{price_request.description}\n\n'
                    f'Комментарий:\n{price_request.comment or "—"}\n\n'
                    f'Открыть в админке: '
                    f'https://pro-instrument.ru/admin/users/pricerequest/{price_request.pk}/change/'
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.ADMIN_EMAIL],
                fail_silently=True,
            )
        except Exception:
            pass

        # 2. Письмо клиенту — подтверждение
        try:
            send_mail(
                subject=f'Заявка на цену принята — PRO-инструмент',
                message=(
                    f'Здравствуйте, {price_request.name}!\n\n'
                    f'Мы получили вашу заявку на подбор товара:\n\n'
                    f'{price_request.description}\n\n'
                    f'Наш менеджер свяжется с вами в ближайшее время '
                    f'по телефону {price_request.phone} или email {price_request.email} '
                    f'и сообщит цену и сроки поставки.\n\n'
                    f'С уважением,\n'
                    f'команда PRO-инструмент\n'
                    f'https://pro-instrument.ru'
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[price_request.email],
                fail_silently=True,
            )
        except Exception:
            pass


class PriceRequestSuccessView(TemplateView):
    """Страница «Спасибо за заявку»."""
    template_name = 'users/price_request_success.html'


# ============================================================
# СРАВНЕНИЕ ТОВАРОВ
# ============================================================

@login_required
@require_POST
def comparison_add(request, product_id):
    """Добавить товар в сравнение."""
    from catalog.models import Product
    product = get_object_or_404(Product, id=product_id)
    Comparison.objects.get_or_create(user=request.user, product=product)
    messages.success(request, f'«{product.name}» добавлен в сравнение')
    return redirect(request.META.get('HTTP_REFERER', 'catalog:index'))


@login_required
@require_POST
def comparison_remove(request, product_id):
    """Удалить товар из сравнения."""
    Comparison.objects.filter(user=request.user, product_id=product_id).delete()
    messages.success(request, 'Товар удалён из сравнения')
    return redirect(request.META.get('HTTP_REFERER', 'users:comparison'))


@login_required
def comparison_clear(request):
    """Очистить всё сравнение."""
    Comparison.objects.filter(user=request.user).delete()
    messages.success(request, 'Сравнение очищено')
    return redirect('users:comparison')


# class ComparisonView(LoginRequiredMixin, TemplateView):
#     """Страница сравнения товаров."""
#     template_name = 'users/comparison.html'
#
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         items = Comparison.objects.filter(
#             user=self.request.user
#         ).select_related('product').order_by('-added_at')
#
#         products = [item.product for item in items]
#
#         # Собираем все характеристики всех товаров
#         from catalog.models import ProductProperty
#         all_property_names = set()
#         for product in products:
#             for prop in product.properties.all():
#                 all_property_names.add(prop.name)
#
#         # Формируем таблицу характеристик
#         properties_table = []
#         for name in sorted(all_property_names):
#             row = {'name': name, 'values': []}
#             for product in products:
#                 prop = product.properties.filter(name=name).first()
#                 row['values'].append(prop.value if prop else '—')
#             properties_table.append(row)
#
#         context['products'] = products
#         context['properties_table'] = properties_table
#         return context


class ComparisonView(LoginRequiredMixin, TemplateView):
    """Страница сравнения товаров, сгруппированных по категориям."""
    template_name = 'users/comparison.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        items = Comparison.objects.filter(
            user=self.request.user
        ).select_related('product', 'product__category').order_by('-added_at')

        # Группируем товары по категории
        from collections import OrderedDict
        groups = OrderedDict()

        for item in items:
            product = item.product
            category = product.category
            key = category.id if category else 0

            if key not in groups:
                groups[key] = {
                    'category': category,
                    'category_name': category.name if category else 'Без категории',
                    'products': [],
                }
            groups[key]['products'].append(product)

        # Для каждой группы строим свою таблицу характеристик
        for group in groups.values():
            products = group['products']

            # Собираем все названия характеристик внутри группы
            all_property_names = set()
            for product in products:
                for prop in product.properties.all():
                    all_property_names.add(prop.name)

            # Строим строки таблицы
            properties_table = []
            for name in sorted(all_property_names):
                row = {'name': name, 'values': []}
                for product in products:
                    prop = product.properties.filter(name=name).first()
                    row['values'].append(prop.value if prop else '—')
                properties_table.append(row)

            group['properties_table'] = properties_table
            group['products_count'] = len(products)

        context['groups'] = list(groups.values())
        context['total_count'] = sum(g['products_count'] for g in groups.values())
        return context