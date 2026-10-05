# catalog/management/commands/import_categories.py
"""Импорт категорий из CSV. Идемпотентно."""
import csv
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction

from catalog.models import Category


class Command(BaseCommand):
    help = 'Импорт категорий из CSV (id,parent_id,name,slug)'

    def add_arguments(self, parser):
        parser.add_argument('csv_path', type=str)
        parser.add_argument('--dry-run', action='store_true')

    @transaction.atomic
    def handle(self, *args, **options):
        csv_path = Path(options['csv_path'])
        dry_run = options['dry_run']

        with open(csv_path, encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        self.stdout.write(f'Строк в CSV: {len(rows)}')

        # Сначала создаём/обновляем все без parent, потом вторым проходом parent
        id_to_category = {}

        # Проход 1: все категории без parent
        for row in rows:
            cid = row.get('id', '').strip()
            name = row['name'].strip()
            slug = row['slug'].strip()
            if not slug:
                self.stdout.write(self.style.WARNING(f'Пропуск (нет slug): {name}'))
                continue

            if dry_run:
                self.stdout.write(f'[DRY] {name} -> {slug}')
                continue

            cat, created = Category.objects.update_or_create(
                slug=slug,
                defaults={'name': name},
            )
            id_to_category[cid] = cat
            action = 'создана' if created else 'обновлена'
            self.stdout.write(f'{action}: {name} ({slug})')

        # Проход 2: parent
        if not dry_run:
            for row in rows:
                parent_id = (row.get('parent_id') or '').strip()
                cid = (row.get('id') or '').strip()
                if not parent_id or not cid:
                    continue
                child = id_to_category.get(cid)
                parent = id_to_category.get(parent_id)
                if not child or not parent:
                    continue
                if child.parent_id != parent.id:
                    child.parent = parent
                    child.save(update_fields=['parent'])
                    self.stdout.write(f'parent: {child.name} -> {parent.name}')

        self.stdout.write(self.style.SUCCESS('Готово'))