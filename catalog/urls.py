from django.urls import path
from .views import (
    IndexView, CategoryListView, CategoryDetailView,
    ProductDetailView, search_view, BrandDetailView,
)

app_name = 'catalog'

urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    path('categories/', CategoryListView.as_view(), name='category_list'),
    path('category/<slug:slug>/', CategoryDetailView.as_view(), name='category_detail'),
    path('product/<slug:slug>/', ProductDetailView.as_view(), name='product_detail'),
    path('search/', search_view, name='search'),
    path('brand/<slug:slug>/', BrandDetailView.as_view(), name='brand_detail'),
]