# orders/urls.py
from django.urls import path
from .views import OrderCreateView, order_success, order_invoice, tbank_webhook, pay_order

app_name = 'orders'

urlpatterns = [
    path('checkout/', OrderCreateView.as_view(), name='order_create'),
    path('success/', order_success, name='order_success'),
    path('<int:pk>/invoice/', order_invoice, name='order_invoice'),
    path('<int:pk>/pay/', pay_order, name='order_pay'),
    path('payment/webhook/', tbank_webhook, name='tbank_webhook'),
]