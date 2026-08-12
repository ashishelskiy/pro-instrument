# catalog/templatetags/catalog_tags.py
from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Получить значение из словаря по ключу.
    Использование: {{ dict|get_item:key }}
    """
    if dictionary and key:
        return dictionary.get(key, '')
    return ''

@register.filter
def get_list_item(dictionary, key):
    """
    Получить список значений из словаря по ключу.
    Использование: {{ dict|get_list_item:key }}
    """
    if dictionary and key:
        return dictionary.getlist(key, [])
    return []

@register.filter
def in_list(value, lst):
    """
    Проверить, находится ли значение в списке.
    Использование: {{ value|in_list:list }}
    """
    if lst:
        return value in lst
    return False