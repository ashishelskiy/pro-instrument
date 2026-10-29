import pymupdf
import re
from decimal import Decimal, InvalidOperation
from datetime import datetime


MONTHS = {
    'января': 1, 'февраля': 2, 'марта': 3, 'апреля': 4,
    'мая': 5, 'июня': 6, 'июля': 7, 'августа': 8,
    'сентября': 9, 'октября': 10, 'ноября': 11, 'декабря': 12,
}


def to_decimal(s) -> Decimal:
    if s is None:
        return Decimal('0')
    s = str(s).replace('\u00a0', '').replace(' ', '').replace(',', '.')
    s = re.sub(r'[^\d.\-]', '', s)
    try:
        return Decimal(s) if s else Decimal('0')
    except InvalidOperation:
        return Decimal('0')


def _clean(cell) -> str:
    if cell is None:
        return ''
    return re.sub(r'\s+', ' ', str(cell)).strip()


def parse_invoice_pdf(path: str) -> dict:
    result = {
        'number': None, 'date': None,
        'supplier': {}, 'buyer': {},
        'total': Decimal('0'), 'vat_total': Decimal('0'),
        'items': [], 'errors': [],
    }

    doc = pymupdf.open(path)
    full_text = "\n".join(page.get_text("text") for page in doc)

    m = re.search(
        r'Счет\s+на\s+оплату\s+№\s*([\w\-/]+)\s+от\s+(\d{1,2})\s+([а-яА-Я]+)\s+(\d{4})',
        full_text,
    )
    if m:
        result['number'] = m.group(1)
        month = MONTHS.get(m.group(3).lower())
        if month:
            result['date'] = datetime(int(m.group(4)), month, int(m.group(2))).date()
        else:
            result['errors'].append(f'Неизвестный месяц: {m.group(3)}')
    else:
        result['errors'].append('Не найден номер/дата счёта')

    m = re.search(r'Поставщик:\s*(.+?),?\s*ИНН\s*(\d{10,12}),?\s*КПП\s*(\d{9})', full_text)
    if m:
        result['supplier'] = {'name': m.group(1).strip(), 'inn': m.group(2), 'kpp': m.group(3)}

    m = re.search(r'Покупатель:\s*(.+?),?\s*ИНН\s*(\d{10,12}),?\s*КПП\s*(\d{9})', full_text)
    if m:
        result['buyer'] = {'name': m.group(1).strip(), 'inn': m.group(2), 'kpp': m.group(3)}

    m = re.search(r'Итого:\s*([\d\s\u00a0.,]+)', full_text)
    if m:
        result['total'] = to_decimal(m.group(1))

    m = re.search(r'В\s*т\.ч\.\s*НДС\s*\((\d+)%\):\s*([\d\s\u00a0.,]+)', full_text)
    if m:
        result['vat_total'] = to_decimal(m.group(2))

    for page in doc:
        for table in page.find_tables():
            rows = table.extract()
            if not rows:
                continue
            header = ' '.join(_clean(c) for c in rows[0]).lower()
            if 'товары' not in header or 'количество' not in header:
                continue
            for cells in rows[1:]:
                cells = [_clean(c) for c in cells]
                joined = ' '.join(cells).lower()
                if not any(cells) or 'итого' in joined:
                    continue
                if not re.fullmatch(r'\d+', cells[0] or ''):
                    continue
                try:
                    row_no   = int(cells[0])
                    code     = cells[1]
                    name     = cells[2]
                    qty      = to_decimal(cells[3]) if len(cells) > 3 else Decimal('0')
                    price    = to_decimal(cells[5]) if len(cells) > 5 else Decimal('0')
                    vat_rate = to_decimal(cells[6].replace('%', '')) if len(cells) > 6 else Decimal('20')
                    vat_amt  = to_decimal(cells[7]) if len(cells) > 7 else Decimal('0')
                    amount   = to_decimal(cells[8]) if len(cells) > 8 else Decimal('0')
                except (ValueError, IndexError):
                    result['errors'].append(f'Не удалось разобрать строку: {cells}')
                    continue
                result['items'].append({
                    'row_no': row_no, 'code': code, 'name': name,
                    'quantity': qty, 'price': price,
                    'vat_rate': vat_rate, 'vat_amount': vat_amt, 'amount': amount,
                })

    doc.close()

    if not result['items']:
        result['errors'].append('Товарные строки не найдены')

    if result['items'] and result['total']:
        items_sum = sum(i['amount'] for i in result['items'])
        if abs(items_sum - result['total']) > Decimal('0.02'):
            result['errors'].append(f'Сумма строк {items_sum} != Итого {result["total"]}')

    return result
