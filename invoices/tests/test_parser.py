from decimal import Decimal
from pathlib import Path
from django.test import SimpleTestCase
from invoices.parser import parse_invoice_pdf

FIXTURES = Path(__file__).parent / 'fixtures'


class ParserTest(SimpleTestCase):
    def test_invoice_887(self):
        data = parse_invoice_pdf(str(FIXTURES / 'invoice_887.pdf'))
        self.assertEqual(data['number'], 'ЦБ-887')
        self.assertEqual(str(data['date']), '2024-09-17')
        self.assertEqual(data['supplier']['inn'], '6154160855')
        self.assertEqual(data['buyer']['inn'], '6154162250')
        self.assertEqual(data['total'], Decimal('12670.00'))
        self.assertEqual(data['vat_total'], Decimal('2111.67'))
        self.assertEqual(len(data['items']), 4)
        self.assertEqual(data['errors'], [])

        first = data['items'][0]
        self.assertEqual(first['code'], '23576325')
        self.assertEqual(first['quantity'], Decimal('2'))
        self.assertEqual(first['price'], Decimal('450.00'))
        self.assertEqual(first['amount'], Decimal('900.00'))

    def test_invoice_918(self):
        data = parse_invoice_pdf(str(FIXTURES / 'invoice_918.pdf'))
        self.assertEqual(data['number'], 'ЦБ-918')
        self.assertEqual(str(data['date']), '2024-09-25')
        self.assertEqual(data['total'], Decimal('29665.00'))
        self.assertEqual(data['vat_total'], Decimal('4944.18'))
        self.assertEqual(len(data['items']), 19)
        self.assertEqual(data['errors'], [])

        # сумма строк == итого
        total = sum(i['amount'] for i in data['items'])
        self.assertEqual(total, data['total'])