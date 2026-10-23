# orders/cdek_service.py
import requests
from django.conf import settings

def get_delivery_tariffs(city_code, total_weight_grams=1000, length=20, width=20, height=20):
    """
    Запрашивает у СДЭК тарифы через прямой HTTP-запрос.
    """
    # 1. Определяем базовый URL (тестовый или боевой)
    base_url = "https://api.edu.cdek.ru/v2" if settings.CDEK_TEST_MODE else "https://api.cdek.ru/v2"

    # 2. Получаем токен авторизации
    auth_response = requests.post(
        f"{base_url}/oauth/token",
        params={
            'grant_type': 'client_credentials',
            'client_id': settings.CDEK_ACCOUNT,
            'client_secret': settings.CDEK_SECRET,
        }
    )
    auth_response.raise_for_status()
    token = auth_response.json()['access_token']

    # 3. Запрашиваем тарифы
    # ВАЖНО: замените 44 на код вашего города-отправителя!
    response = requests.post(
        f"{base_url}/calculator/tarifflist",
        headers={'Authorization': f'Bearer {token}'},
        json={
            'type': 1,
            'currency': 1,
            'lang': 'rus',
            'from_location': {'code': 1069},  # ← код города отправителя (1069 = Таганрог)
            'to_location': {'code': int(city_code)},
            'packages': [{
                'weight': total_weight_grams,
                'length': length,
                'width': width,
                'height': height,
            }]
        }
    )
    response.raise_for_status()
    data = response.json()

    # 4. Преобразуем ответ в удобный формат
    result = []
    for t in data.get('tariff_codes', []):
        result.append({
            'id': str(t['tariff_code']),
            'name': t['tariff_name'],
            'price': float(t['delivery_sum']),
            'period_min': t.get('period_min', 1),
            'period_max': t.get('period_max', 5),
        })
    return result


def get_city_code_by_name(city_name):
    """
    Ищет код города СДЭК по названию.
    Возвращает код или None.
    """
    base_url = "https://api.cdek.ru/v2"

    auth_response = requests.post(
        f"{base_url}/oauth/token",
        data={
            'grant_type': 'client_credentials',
            'client_id': settings.CDEK_ACCOUNT,
            'client_secret': settings.CDEK_SECRET,
        }
    )
    auth_response.raise_for_status()
    token = auth_response.json()['access_token']

    response = requests.get(
        f"{base_url}/location/cities",
        headers={'Authorization': f'Bearer {token}'},
        params={
            'city': city_name,
            'country_code': 'RU',
            'size': 100,          # ← с запасом
        }
    )
    response.raise_for_status()
    data = response.json()

    if not data:
        return None

    # Ищем точное совпадение по названию (без учёта регистра)
    city_name_lower = city_name.strip().lower()
    for city in data:
        if city.get('city', '').lower() == city_name_lower:
            return city['code']

    # Если точного совпадения нет — возвращаем первый
    return data[0]['code']


def get_pvz_list(city_code):
    """Получает список ПВЗ (пунктов выдачи заказов) в городе."""
    base_url = "https://api.edu.cdek.ru/v2" if settings.CDEK_TEST_MODE else "https://api.cdek.ru/v2"

    auth_response = requests.post(
        f"{base_url}/oauth/token",
        params={
            'grant_type': 'client_credentials',
            'client_id': settings.CDEK_ACCOUNT,
            'client_secret': settings.CDEK_SECRET,
        }
    )
    auth_response.raise_for_status()
    token = auth_response.json()['access_token']

    response = requests.get(
        f"{base_url}/deliverypoints",
        headers={'Authorization': f'Bearer {token}'},
        params={
            'city_code': city_code,
            'type': 'PVZ',
            'is_handout': 'true',
        }
    )
    response.raise_for_status()
    data = response.json()

    result = []
    for p in data:
        # В боевом API — coordx/coordy, в тестовом может быть location.latitude/longitude
        lat = p.get('coordy') or p.get('location', {}).get('latitude')
        lon = p.get('coordx') or p.get('location', {}).get('longitude')
        if not lat or not lon:
            continue

        location = p.get('location', {})
        result.append({
            'code': p.get('code'),
            'name': p.get('name'),
            'address': location.get('address_full') or location.get('address', ''),
            'lat': float(lat),
            'lon': float(lon),
            'work_time': p.get('work_time', ''),
            'phone': (p.get('phones') or [{}])[0].get('number', ''),
        })

    return result