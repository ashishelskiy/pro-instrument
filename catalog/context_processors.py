# catalog/context_processors.py
from django.urls import reverse
from .models import Category, Product

# def menu_categories(request):
#     """Подготавливает данные каталога для mega-menu."""
#     categories = (
#         Category.objects
#         .filter(parent__isnull=True)
#         .prefetch_related("children")
#     )
#
#     menu_data = []
#     for category in categories:
#         children = list(category.children.all())
#         menu_data.append({
#             "category": category,
#             "children": children,
#             "has_children": bool(children),
#         })
#
#         # Новинки
#     new_products = Product.objects.filter(in_stock=True).order_by('-created_at')[:5]
#
#     # Баннеры (заглушка)
#     # banners = [
#     #     {
#     #         'image': '/static/images/shutterstock_103105808.jpg',
#     #         'title': 'Скидки до 50%',
#     #         'description': 'На все электроинструменты',
#     #         'link': '/catalog/'
#     #     },
#     #     {
#     #         'image': '/static/images/shutterstock_1172592745.jpg',
#     #         'title': 'Новинки',
#     #         'description': 'Аккумуляторный инструмент',
#     #         'link': '/catalog/akkumulyatornyy-instrument/'
#     #     },
#     #     {
#     #         'image': '/static/images/Oil_Rig_Worker.jpg',
#     #         'title': 'Акции',
#     #         'description': 'Товары со скидкой',
#     #         'link': '/catalog/?on_sale=1'
#     #     },
#     # ]
#
#     # КАРТОЧКИ КАТЕГОРИЙ (заглушка)
#     # 6 карточек: 468×185, 224×185, 224×185, 224×185, 468×185, 224×185
#     category_cards = [
#         {
#             'title': 'Электроинструмент',
#             'image': '/static/images/istockphoto-1404774639-612x612.jpg',
#             'link': reverse('catalog:category_detail', kwargs={'slug': 'elektroinstrumenty'}),
#             'width': 468,
#             'height': 185
#         },
#         {
#             'title': 'Ручной инструмент',
#             'image': '/static/images/istockphoto-492201907-612x612.jpg',
#             'link': reverse('catalog:category_detail', kwargs={'slug': 'ruchnoj-instrument'}),
#             'width': 224,
#             'height': 185
#         },
#         {
#             'title': 'Садовая техника и инвентарь',
#             'image': '/static/images/istockphoto-185568132-612x612.jpg',
#             'link': reverse('catalog:category_detail', kwargs={'slug': 'sadovaya-tehnika-i-inventar'}),
#             'width': 224,
#             'height': 185
#         },
#         {
#             'title': 'Строительная техника',
#             'image': '/static/images/istockphoto-946780084-612x612.jpg',
#             'link': reverse('catalog:category_detail', kwargs={'slug': 'stroitelnaya-tehnika'}),
#             'width': 224,
#             'height': 185
#         },
#         {
#             'title': 'Климатическое оборудование',
#             'image': '/static/images/',
#             'link': '/catalog/klimaticheskoe-oborudovanie/',
#             'width': 468,
#             'height': 185
#         },
#         {
#             'title': 'Крепеж и метизы',
#             'image': '/static/images/',
#             'link': '/catalog/krepezh/',
#             'width': 224,
#             'height': 185
#         },
#     ]
#
#     return {
#         "menu_data": menu_data,
#         'new_products': new_products,
#         # 'banners': banners,
#         'category_cards': category_cards,
#     }


def menu_categories(request):
    """Каталог для mega-menu + bento на главной."""
    categories = (
        Category.objects
        .filter(parent__isnull=True)
        .prefetch_related("children")
    )

    menu_data = []
    for category in categories:
        children = list(category.children.all())
        menu_data.append({
            "category": category,
            "children": children,
            "has_children": bool(children),
        })

    # Новинки
    new_products = Product.objects.filter(in_stock=True).order_by('-created_at')[:5]

    # BENTO — реальные категории из БД (максимум 6)
    # bento_categories = Category.objects.filter(
    #     show_in_bento=True,
    # ).order_by('bento_order', 'name')[:6]
    #
    # category_cards = [
    #     {
    #         'title': cat.name,
    #         'image': cat.image.url if cat.image else '',
    #         'link': cat.get_absolute_url(),
    #     }
    #     for cat in bento_categories
    # ]
    bento_categories = Category.objects.filter(
        show_in_bento=True,
    ).order_by('bento_order', 'name')[:6]

    category_cards = [
        {
            'title': cat.name,
            'image': cat.bento_image.url if cat.bento_image else '',
            'link': cat.get_absolute_url(),
        }
        for cat in bento_categories
    ]

    return {
        "menu_data": menu_data,
        'new_products': new_products,
        'category_cards': category_cards,
    }
