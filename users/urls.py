# users/urls.py
from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from django.contrib.auth.views import LoginView, LogoutView
from .views import (
    RegisterView,
    ProfileView, ProfileEditView,
    MyPasswordChangeView,
    OrdersView, OrderDocumentsView, PurchaseHistoryView,
    FavoritesView, CartView, ViewedView, SupportView,
    OrganizationListView, OrganizationCreateView,
    OrganizationUpdateView, OrganizationDeleteView, OrganizationSetDefaultView,
    account_delete,
    organization_unset_default,
    favorite_add, favorite_remove,
    stock_notification_add, stock_notification_remove, stock_notification_remove_by_product,
    StockNotificationsView,
    PriceRequestView, PriceRequestSuccessView,
    comparison_add, comparison_remove, comparison_clear, ComparisonView,
)

app_name = 'users'

urlpatterns = [
    # Аутентификация
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(
        template_name='registration/login.html',
        redirect_authenticated_user=True,
    ), name='login'),
    path('logout/', LogoutView.as_view(next_page='/'), name='logout'),

    # Личный кабинет
    path('profile/', ProfileView.as_view(), name='profile'),
    path('profile/edit/', ProfileEditView.as_view(), name='profile_edit'),

    # Смена пароля
    path('password/change/', MyPasswordChangeView.as_view(), name='password_change'),

    # Удаление аккаунта
    path('account/delete/', account_delete, name='account_delete'),

    # Разделы кабинета
    path('orders/', OrdersView.as_view(), name='orders'),
    path('orders/documents/', OrderDocumentsView.as_view(), name='order_documents'),
    path('orders/history/', PurchaseHistoryView.as_view(), name='purchase_history'),
    path('favorites/', FavoritesView.as_view(), name='favorites'),
    path('cart/', CartView.as_view(), name='cart'),
    path('viewed/', ViewedView.as_view(), name='viewed'),
    path('support/', SupportView.as_view(), name='support'),

    # Организации
    path('organizations/', OrganizationListView.as_view(), name='organizations'),
    path('organizations/add/', OrganizationCreateView.as_view(), name='organization_add'),
    path('organizations/<int:pk>/edit/', OrganizationUpdateView.as_view(), name='organization_edit'),
    path('organizations/<int:pk>/delete/', OrganizationDeleteView.as_view(), name='organization_delete'),
    path('organizations/<int:pk>/set-default/', OrganizationSetDefaultView.as_view(), name='organization_set_default'),
    path('organizations/unset-default/', organization_unset_default, name='organization_unset_default'),

    # Избранное
    path('favorites/add/<str:product_id>/', favorite_add, name='favorite_add'),
    path('favorites/remove/<str:product_id>/', favorite_remove, name='favorite_remove'),

    # Уведомление о поступлении
    path('stock-notification/<str:product_id>/', stock_notification_add, name='stock_notification_add'),
    path('stock-notifications/', StockNotificationsView.as_view(), name='stock_notifications'),
    path('stock-notifications/<int:pk>/remove/', stock_notification_remove, name='stock_notification_remove'),
    path('stock-notification/remove/<str:product_id>/', stock_notification_remove_by_product, name='stock_notification_remove_by_product'),

    # Запрос цены
    path('request-price/', PriceRequestView.as_view(), name='price_request'),
    path('request-price/success/', PriceRequestSuccessView.as_view(), name='price_request_success'),

    # Восстановление пароля
    path('password-reset/',
         auth_views.PasswordResetView.as_view(
             template_name='users/password_reset.html',
             email_template_name='users/password_reset_email.html',
             subject_template_name='users/password_reset_subject.txt',
             success_url=reverse_lazy('users:password_reset_done'),
         ),
         name='password_reset'),

    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='users/password_reset_done.html',
         ),
         name='password_reset_done'),

    path('password-reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='users/password_reset_confirm.html',
             success_url=reverse_lazy('users:password_reset_complete'),
         ),
         name='password_reset_confirm'),

    path('password-reset/complete/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='users/password_reset_complete.html',
         ),
         name='password_reset_complete'),

    # Сравнение
    path('comparison/', ComparisonView.as_view(), name='comparison'),
    path('comparison/add/<str:product_id>/', comparison_add, name='comparison_add'),
    path('comparison/remove/<str:product_id>/', comparison_remove, name='comparison_remove'),
    path('comparison/clear/', comparison_clear, name='comparison_clear'),
]