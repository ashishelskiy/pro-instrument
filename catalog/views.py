# catalog/views.py
from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView
from django.db.models import Q, Min, Max, F
from django.core.paginator import Paginator
from .models import Category, Product, ProductProperty, Brand, CategoryProperty
from banners.models import Banner, BannerPosition



class IndexView(ListView):
    """Главная страница"""
    model = Product
    template_name = 'catalog/index.html'
    context_object_name = 'products'
    paginate_by = 12

    def get_queryset(self):
        return Product.objects.filter(in_stock=True).select_related('brand', 'category')[:12]

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.filter(parent__isnull=True)
        context['new_products'] = Product.objects.filter(in_stock=True).order_by('-created_at')[:8]

        from pages.models import News
        context['latest_news'] = News.objects.filter(is_published=True)[:3]

        # Баннеры из модели
        banners = list(Banner.objects.for_position(BannerPosition.HOME_TOP))
        context['banners'] = banners

        # Считаем показы
        if banners:
            Banner.objects.filter(pk__in=[b.pk for b in banners]).update(
                views_count=F('views_count') + 1
            )

        # Бренды для главной
        context['featured_brands'] = Brand.objects.filter(is_featured=True)[:12]

        # Лидеры продаж — сортируем по количеству проданных
        from orders.models import OrderItem
        from django.db.models import Sum, Count

        top_products = Product.objects.filter(
            in_stock=True,
        ).annotate(
            sold=Sum('orderitem__quantity')
        ).filter(
            sold__gt=0
        ).order_by('-sold')[:6]

        # Если продаж нет — берём просто популярные (последние)
        if not top_products:
            top_products = Product.objects.filter(in_stock=True).order_by('-created_at')[:6]

        context['top_products'] = top_products

        return context


class CategoryListView(ListView):
    """Список категорий"""
    model = Category
    template_name = 'catalog/category_list.html'
    context_object_name = 'categories'

    def get_queryset(self):
        return Category.objects.filter(parent__isnull=True)


# class CategoryDetailView(ListView):
#     """Детальная страница категории"""
#     model = Product
#     paginate_by = 24
#     context_object_name = 'products'
#
#     def get_queryset(self):
#         self.category = get_object_or_404(Category, slug=self.kwargs['slug'])
#
#         if self.category.children.exists():
#             return Product.objects.none()
#
#         queryset = Product.objects.filter(
#             category=self.category,
#         ).select_related('brand', 'category')
#
#         # Фильтрация по цене
#         min_price = self.request.GET.get('min_price')
#         max_price = self.request.GET.get('max_price')
#         if min_price:
#             queryset = queryset.filter(price__gte=min_price)
#         if max_price:
#             queryset = queryset.filter(price__lte=max_price)
#
#         # Фильтрация по бренду
#         brand = self.request.GET.get('brand')
#         if brand:
#             queryset = queryset.filter(brand__slug=brand)
#
#         # Фильтрация по характеристикам
#         property_names = ['Наличие удара', 'Напряжение аккумулятора, В', 'Тип двигателя']
#         for prop_name in property_names:
#             prop_value = self.request.GET.get(prop_name)
#             if prop_value:
#                 queryset = queryset.filter(
#                     properties__name=prop_name,
#                     properties__value=prop_value
#                 )
#
#         # Поиск
#         q = self.request.GET.get('q')
#         if q:
#             queryset = queryset.filter(
#                 Q(name__icontains=q) |
#                 Q(article__icontains=q) |
#                 Q(description__icontains=q)
#             )
#
#         # Сортировка: сначала в наличии, потом под заказ
#         sort = self.request.GET.get('sort')
#         if sort == 'price_asc':
#             queryset = queryset.order_by('-in_stock', 'price')
#         elif sort == 'price_desc':
#             queryset = queryset.order_by('-in_stock', '-price')
#         elif sort == 'name':
#             queryset = queryset.order_by('-in_stock', 'name')
#         else:
#             queryset = queryset.order_by('-in_stock', '-created_at')
#
#         return queryset
#
#     def get_template_names(self):
#         if self.category.children.exists():
#             return ['catalog/subcategory_list.html']
#         return ['catalog/product_list.html']
#
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context['category'] = self.category
#
#         if self.category.children.exists():
#             context['subcategories'] = self.category.children.all().order_by('name')
#         else:
#             context['brands'] = Brand.objects.filter(
#                 products__category=self.category,
#                 products__in_stock=True
#             ).distinct()
#
#             price_range = Product.objects.filter(
#                 category=self.category
#             ).aggregate(
#                 min_price=Min('price'),
#                 max_price=Max('price')
#             )
#             context['min_price'] = price_range.get('min_price') or 0
#             context['max_price'] = price_range.get('max_price') or 0
#
#             property_names = ['Наличие удара', 'Напряжение аккумулятора, В', 'Тип двигателя']
#             filter_properties = []
#
#             for prop_name in property_names:
#                 values = ProductProperty.objects.filter(
#                     product__category=self.category,
#                     product__in_stock=True,
#                     name=prop_name
#                 ).values_list('value', flat=True).distinct().order_by('value')
#
#                 values = [v for v in values if v and v.strip()]
#
#                 if values:
#                     filter_properties.append({
#                         'name': prop_name,
#                         'values': values
#                     })
#
#             context['filter_properties'] = filter_properties
#             context['in_stock_count'] = Product.objects.filter(
#                 category=self.category,
#                 in_stock=True
#             ).count()
#             context['on_order_count'] = Product.objects.filter(
#                 category=self.category,
#                 in_stock=False
#             ).count()
#
#         return context


class CategoryDetailView(ListView):
    """Детальная страница категории"""
    model = Product
    template_name = 'catalog/product_list.html'
    paginate_by = 24
    context_object_name = 'products'

    def get_queryset(self):
        # self.category = get_object_or_404(Category, slug=self.kwargs['slug'])
        #
        # if self.category.children.exists():
        #     return Product.objects.none()
        #
        # queryset = Product.objects.filter(
        #     category=self.category,
        # ).select_related('brand', 'category')
        self.category = get_object_or_404(Category, slug=self.kwargs['slug'])

        # Собираем id самой категории и всех её детей (один уровень)
        child_ids = list(self.category.children.values_list('id', flat=True))
        category_ids = [self.category.id] + child_ids

        queryset = Product.objects.filter(
            category_id__in=category_ids,
        ).select_related('brand', 'category')

        # === Фильтрация по цене ===
        min_price = self.request.GET.get('min_price')
        max_price = self.request.GET.get('max_price')
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)

        # === Фильтрация по бренду ===
        brand = self.request.GET.get('brand')
        if brand:
            queryset = queryset.filter(brand__slug=brand)

        # # === Фильтрация по характеристикам (динамика из CategoryProperty) ===
        # # Получаем список характеристик для этой категории
        # category_props = CategoryProperty.objects.filter(
        #     category=self.category
        # ).values_list('name', flat=True)
        #
        # for prop_name in category_props:
        #     prop_value = self.request.GET.get(prop_name)
        #     if prop_value:
        #         queryset = queryset.filter(
        #             properties__name=prop_name,
        #             properties__value=prop_value
        #         )

        # === Фильтрация по характеристикам (множественный выбор) ===
        category_props = CategoryProperty.objects.filter(
            category=self.category
        ).values_list('name', flat=True)

        for prop_name in category_props:
            prop_values = self.request.GET.getlist(prop_name)
            if prop_values:
                # Q-объект для нескольких значений одной характеристики
                q_prop = Q()
                for v in prop_values:
                    q_prop |= Q(properties__name=prop_name, properties__value=v)
                queryset = queryset.filter(q_prop).distinct()

        # === Поиск ===
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(
                Q(name__icontains=q) |
                Q(article__icontains=q) |
                Q(description__icontains=q)
            )

        # === Сортировка ===
        sort = self.request.GET.get('sort')
        if sort == 'price_asc':
            queryset = queryset.order_by('-in_stock', 'price')
        elif sort == 'price_desc':
            queryset = queryset.order_by('-in_stock', '-price')
        elif sort == 'name':
            queryset = queryset.order_by('-in_stock', 'name')
        else:
            queryset = queryset.order_by('-in_stock', '-created_at')

        return queryset

    # def get_template_names(self):
    #     if self.category.children.exists():
    #         return ['catalog/subcategory_list.html']
    #     return ['catalog/product_list.html']

    # def get_context_data(self, **kwargs):
    #     context = super().get_context_data(**kwargs)
    #     context['category'] = self.category
    #
    #     if self.category.children.exists():
    #         context['subcategories'] = self.category.children.all().order_by('name')
    #     else:
    #         # Бренды в категории
    #         context['brands'] = Brand.objects.filter(
    #             products__category=self.category,
    #             products__in_stock=True
    #         ).distinct()
    #
    #         # Диапазон цен
    #         price_range = Product.objects.filter(
    #             category=self.category
    #         ).aggregate(
    #             min_price=Min('price'),
    #             max_price=Max('price')
    #         )
    #         context['min_price'] = price_range.get('min_price') or 0
    #         context['max_price'] = price_range.get('max_price') or 0
    #
    #         # === ДИНАМИЧЕСКИЕ ФИЛЬТРЫ ПО ХАРАКТЕРИСТИКАМ ===
    #         # Получаем шаблон характеристик для категории
    #         category_props = CategoryProperty.objects.filter(
    #             category=self.category
    #         ).order_by('sort_order', 'name')
    #
    #         filter_properties = []
    #
    #         for prop_template in category_props:
    #             # Значения этой характеристики у товаров категории
    #             values = ProductProperty.objects.filter(
    #                 product__category=self.category,
    #                 product__in_stock=True,
    #                 name=prop_template.name
    #             ).values_list('value', flat=True).distinct().order_by('value')
    #
    #             values = [v for v in values if v and v.strip()]
    #
    #             if values:
    #                 filter_properties.append({
    #                     'name': prop_template.name,
    #                     'values': values,
    #                 })
    #
    #         context['filter_properties'] = filter_properties
    #
    #         # Выбранные значения для фильтров (для галочек)
    #         selected_filters = {}
    #         for prop in filter_properties:
    #             selected_filters[prop['name']] = self.request.GET.getlist(prop['name'])
    #         context['selected_filters'] = selected_filters
    #
    #         # Количество товаров
    #         context['in_stock_count'] = Product.objects.filter(
    #             category=self.category,
    #             in_stock=True
    #         ).count()
    #         context['on_order_count'] = Product.objects.filter(
    #             category=self.category,
    #             in_stock=False
    #         ).count()
    #
    #     return context
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category

        # Всегда передаём подкатегории (в шаблоне покажем, только если они есть)
        context['subcategories'] = self.category.children.all().order_by('name')

        # Бренды в категории и её подкатегориях
        child_ids = list(self.category.children.values_list('id', flat=True))
        category_ids = [self.category.id] + child_ids

        context['brands'] = Brand.objects.filter(
            products__category_id__in=category_ids,
            products__in_stock=True
        ).distinct()

        # Диапазон цен — тоже по всей ветке
        price_range = Product.objects.filter(
            category_id__in=category_ids
        ).aggregate(
            min_price=Min('price'),
            max_price=Max('price')
        )
        context['min_price'] = price_range.get('min_price') or 0
        context['max_price'] = price_range.get('max_price') or 0

        # Фильтры по характеристикам
        category_props = CategoryProperty.objects.filter(
            category=self.category
        ).order_by('sort_order', 'name')

        filter_properties = []
        for prop_template in category_props:
            values = ProductProperty.objects.filter(
                product__category_id__in=category_ids,
                product__in_stock=True,
                name=prop_template.name
            ).values_list('value', flat=True).distinct().order_by('value')

            values = [v for v in values if v and v.strip()]

            if values:
                filter_properties.append({
                    'name': prop_template.name,
                    'values': values,
                })

        context['filter_properties'] = filter_properties

        selected_filters = {}
        for prop in filter_properties:
            selected_filters[prop['name']] = self.request.GET.getlist(prop['name'])
        context['selected_filters'] = selected_filters

        # Счётчики (опционально, если где-то показываете)
        context['in_stock_count'] = Product.objects.filter(
            category_id__in=category_ids,
            in_stock=True
        ).count()
        context['on_order_count'] = Product.objects.filter(
            category_id__in=category_ids,
            in_stock=False
        ).count()

        return context


class ProductDetailView(DetailView):
    """Детальная страница товара"""
    model = Product
    template_name = 'catalog/product_detail.html'
    context_object_name = 'product'

    def get_object(self):
        return get_object_or_404(Product, slug=self.kwargs['slug'])

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)

        # Записываем просмотр
        if request.user.is_authenticated:
            from users.models import ViewedProduct
            product = self.object
            ViewedProduct.objects.update_or_create(
                user=request.user,
                product=product,
            )

        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.get_object()
        context['properties'] = product.properties.all()
        context['related_products'] = Product.objects.filter(
            category=product.category,
            in_stock=True
        ).exclude(id=product.id)[:6]
        return context


def search_view(request):
    """Поиск товаров"""
    q = request.GET.get('q', '')

    # Ищем по ВСЕМ товарам (включая "Под заказ")
    products = Product.objects.all()

    if q:
        products = products.filter(
            Q(name__icontains=q) |
            Q(article__icontains=q) |
            Q(description__icontains=q)
        ).select_related('brand', 'category')

    # Сортировка: сначала в наличии, потом под заказ
    products = products.order_by('-in_stock')

    paginator = Paginator(products, 24)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'products': page_obj,
        'q': q,
        'total': products.count()
    }
    return render(request, 'catalog/search_results.html', context)


class BrandDetailView(ListView):
    """Страница бренда — список товаров."""
    model = Product
    template_name = 'catalog/brand_detail.html'
    context_object_name = 'products'
    paginate_by = 24

    def get_queryset(self):
        self.brand = get_object_or_404(Brand, slug=self.kwargs['slug'])
        queryset = Product.objects.filter(
            brand=self.brand,
            in_stock=True,
        ).select_related('brand', 'category')

        # Сортировка
        sort = self.request.GET.get('sort')
        if sort == 'price_asc':
            queryset = queryset.order_by('price')
        elif sort == 'price_desc':
            queryset = queryset.order_by('-price')
        elif sort == 'name':
            queryset = queryset.order_by('name')
        else:
            queryset = queryset.order_by('-created_at')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['brand'] = self.brand
        return context