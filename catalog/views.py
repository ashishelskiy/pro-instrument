# catalog/views.py
from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView
from django.db.models import Q, Min, Max, F, Count
from django.core.paginator import Paginator
from .models import Category, Product, ProductProperty, Brand, CategoryProperty
from banners.models import Banner, BannerPosition

from django.http import JsonResponse
from django.urls import reverse


EN_TO_RU = {
    # строчные буквы
    'q': 'й', 'w': 'ц', 'e': 'у', 'r': 'к', 't': 'е', 'y': 'н', 'u': 'г',
    'i': 'ш', 'o': 'щ', 'p': 'з', '[': 'х', ']': 'ъ',
    'a': 'ф', 's': 'ы', 'd': 'в', 'f': 'а', 'g': 'п', 'h': 'р', 'j': 'о',
    'k': 'л', 'l': 'д', ';': 'ж', "'": 'э',
    'z': 'я', 'x': 'ч', 'c': 'с', 'v': 'м', 'b': 'и', 'n': 'т', 'm': 'ь',
    ',': 'б', '.': 'ю',
    '`': 'ё',

    # заглавные буквы (Shift)
    'Q': 'Й', 'W': 'Ц', 'E': 'У', 'R': 'К', 'T': 'Е', 'Y': 'Н', 'U': 'Г',
    'I': 'Ш', 'O': 'Щ', 'P': 'З', '{': 'Х', '}': 'Ъ',
    'A': 'Ф', 'S': 'Ы', 'D': 'В', 'F': 'А', 'G': 'П', 'H': 'Р', 'J': 'О',
    'K': 'Л', 'L': 'Д', ':': 'Ж', '"': 'Э',
    'Z': 'Я', 'X': 'Ч', 'C': 'С', 'V': 'М', 'B': 'И', 'N': 'Т', 'M': 'Ь',
    '<': 'Б', '>': 'Ю',
    '~': 'Ё',
}


def convert_layout(text: str) -> str:
    """EN → RU по позиции клавиши. 'Ntgkjdfz' → 'Тепловая'."""
    return ''.join(EN_TO_RU.get(ch, ch) for ch in text)


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


class CategoryDetailView(ListView):
    """Детальная страница категории"""
    model = Product
    template_name = 'catalog/product_list.html'
    paginate_by = 24
    context_object_name = 'products'

    def get_queryset(self):
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
        q = self.request.GET.get('q', '').strip()
        if q:
            q_ru = convert_layout(q)
            queryset = queryset.filter(
                Q(name__icontains=q) |
                Q(article__icontains=q) |
                Q(name__icontains=q_ru)
            ).distinct()

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


def search_suggest(request):
    """
    JSON-подсказки для автокомплита строки поиска.
    GET ?q=...
    Возвращает:
    {
      "q": "...",
      "categories": [{"name": ..., "url": ...}],
      "brands":     [{"name": ..., "url": ...}],
      "products":   [{"name": ..., "url": ..., "price": "..."}],
    }
    """
    q = request.GET.get('q', '').strip()[:100]

    if not q:
        return JsonResponse({
            'q': '',
            'categories': [],
            'brands': [],
            'products': [],
        })

    # Варианты запроса: оригинал + раскладка EN→RU
    variants = [q]
    q_ru = convert_layout(q)
    if q_ru != q:
        variants.append(q_ru)

    # --- Категории ---
    cat_q = Q()
    for v in variants:
        cat_q |= Q(name__icontains=v)
    categories = (
        Category.objects.filter(cat_q)
        .order_by('name')[:5]
    )

    # --- Бренды ---
    brand_q = Q()
    for v in variants:
        brand_q |= Q(name__icontains=v)
    brands = (
        Brand.objects.filter(brand_q)
        .order_by('name')[:5]
    )

    # --- Товары ---
    prod_q = Q()
    for v in variants:
        prod_q |= Q(name__icontains=v) | Q(article__icontains=v)
    products = (
        Product.objects
        .filter(prod_q)
        .order_by('-in_stock', '-created_at')
        .only('id', 'name', 'slug', 'price')[:5]
    )

    return JsonResponse({
        'q': q,
        'categories': [
            {'name': c.name, 'url': c.get_absolute_url()}
            for c in categories
        ],
        'brands': [
            {'name': b.name, 'url': b.get_absolute_url()}
            for b in brands
        ],
        'products': [
            {
                'name': p.name,
                'url': p.get_absolute_url(),
                'price': str(p.price),
            }
            for p in products
        ],
    })


def _category_with_children_ids(category):
    """id категории + id всех её прямых детей (один уровень, как в меню)."""
    child_ids = list(category.children.values_list('id', flat=True))
    return [category.id] + child_ids


def search_view(request):
    """
    Сквозной поиск: категории + бренды + товары.

    Логика:
    - по запросу ищем категории (name icontains), бренды (name icontains),
      товары (name/article icontains);
    - если найдены категории — дополнительно подтягиваем товары из этих
      категорий (и их подкатегорий), чтобы ввод «генераторы» давал товары
      раздела, даже если в названии товара слова «генератор» нет;
    - если по оригиналу ничего — пробуем раскладку EN→RU (как раньше).
    """
    q = request.GET.get('q', '').strip()[:200]

    empty_context = {
        'products': [],
        'page_obj': None,
        'is_paginated': False,
        'q': '',
        'total': 0,
        'suggested_q': None,
        'suggested_count': 0,
        'fallback_used': False,
        'found_categories': [],
        'found_brands': [],
        'matched_category': None,
        'query_variants': [],
    }

    if not q:
        return render(request, 'catalog/search_results.html', empty_context)

    # Варианты запроса: оригинал + раскладка (если отличается)
    q_variants = [q]
    q_ru = convert_layout(q)
    if q_ru != q:
        q_variants.append(q_ru)

    # ---------- 1. КАТЕГОРИИ ----------
    cat_q = Q()
    for v in q_variants:
        cat_q |= Q(name__icontains=v)

    found_categories = list(
        Category.objects.filter(cat_q).order_by('name')[:20]
    )

    # ---------- 2. БРЕНДЫ ----------
    brand_q = Q()
    for v in q_variants:
        brand_q |= Q(name__icontains=v)

    found_brands = list(
        Brand.objects.filter(brand_q).order_by('name')[:20]
    )

    # ---------- 3. ТОВАРЫ ----------
    product_q = Q()
    for v in q_variants:
        product_q |= Q(name__icontains=v) | Q(article__icontains=v)

    products_qs = (
        Product.objects
        .select_related('brand', 'category')
        .filter(product_q)
        .distinct()
        .order_by('-in_stock', '-created_at')
    )

    total_by_name = products_qs.count()

    # ---------- 4. ТОВАРЫ ИЗ НАЙДЕННЫХ КАТЕГОРИЙ ----------
    # Если запрос совпал с категорией — добавим товары из неё (и детей),
    # чтобы «генераторы» находило раздел, а не только товары со словом в названии.
    matched_category = None
    if found_categories:
        # Берём самую «точную» категорию: сначала полное совпадение,
        # иначе первую по алфавиту (можно доработать по вкусу).
        exact = next(
            (c for c in found_categories if c.name.lower() == q.lower()),
            None,
        )
        matched_category = exact or found_categories[0]

        cat_ids = _category_with_children_ids(matched_category)
        category_products = (
            Product.objects
            .select_related('brand', 'category')
            .filter(category_id__in=cat_ids)
            .distinct()
            .order_by('-in_stock', '-created_at')
        )
        # Объединяем: сначала товары по названию/артикулу, затем из категории
        product_ids = list(products_qs.values_list('id', flat=True))
        extra_ids = list(
            category_products.exclude(id__in=product_ids)
            .values_list('id', flat=True)
        )
        if extra_ids:
            products_qs = Product.objects.filter(
                id__in=product_ids + extra_ids
            ).select_related('brand', 'category').order_by('-in_stock', '-created_at')

    # ---------- 5. Пагинация ----------
    paginator = Paginator(products_qs, 24)
    page_obj = paginator.get_page(request.GET.get('page'))

    total = paginator.count
    suggested_q = None
    suggested_count = 0
    fallback_used = False

    # Если вообще ничего не нашли (ни товаров, ни категорий, ни брендов) —
    # оставляем «подсказку по раскладке» для совместимости с шаблоном.
    if total == 0 and not found_categories and not found_brands and q_ru != q:
        suggested_q = q_ru
        suggested_count = 0
        fallback_used = False

    return render(request, 'catalog/search_results.html', {
        'products': page_obj,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages() if page_obj else False,
        'q': q,
        'total': total,
        'suggested_q': suggested_q,
        'suggested_count': suggested_count,
        'fallback_used': fallback_used,
        'found_categories': found_categories,
        'found_brands': found_brands,
        'matched_category': matched_category,
        'query_variants': q_variants,
        'total_by_name': total_by_name,
    })


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
        context['total_products'] = context['paginator'].count
        return context