#!/usr/bin/env python3
"""
Перегенерация slug'ов из названий по правилам транслитерации.

Правила:
    й → y      ё → e      е → e      ц → ts
    щ → shch   ы → y      ый → yy    ой → oy
    ь, ъ → ''  ю → yu     я → ya     ж → zh
    х → kh     ч → ch     ш → sh
"""

import csv
import re

# Порядок важен: длинные сочетания обрабатываются раньше одиночных букв.
RULES = [
    ('ый', 'yy'),
    ('ой', 'oy'),
    ('ий', 'iy'),
    ('ай', 'ay'),
    ('ей', 'ey'),
    ('уй', 'uy'),
    ('ё',  'e'),
    ('й',  'y'),
    ('ц',  'ts'),
    ('щ',  'shch'),
    ('ш',  'sh'),
    ('ч',  'ch'),
    ('ж',  'zh'),
    ('х',  'kh'),
    ('ю',  'yu'),
    ('я',  'ya'),
    ('ы',  'y'),
    ('е',  'e'),
    ('э',  'e'),
    ('а',  'a'),
    ('б',  'b'),
    ('в',  'v'),
    ('г',  'g'),
    ('д',  'd'),
    ('з',  'z'),
    ('и',  'i'),
    ('к',  'k'),
    ('л',  'l'),
    ('м',  'm'),
    ('н',  'n'),
    ('о',  'o'),
    ('п',  'p'),
    ('р',  'r'),
    ('с',  's'),
    ('т',  't'),
    ('у',  'u'),
    ('ф',  'f'),
    ('ь',  ''),
    ('ъ',  ''),
]


def transliterate(text):
    """Русский текст → латинский slug."""
    text = text.lower()
    text = re.sub(r'[«»""\'`]', '', text)
    text = re.sub(r'[–—−]', '-', text)

    result = []
    i = 0
    while i < len(text):
        if i + 1 < len(text):
            pair = text[i:i + 2]
            matched = False
            for src, dst in RULES:
                if len(src) == 2 and src == pair:
                    result.append(dst)
                    i += 2
                    matched = True
                    break
            if matched:
                continue

        ch = text[i]
        matched = False
        for src, dst in RULES:
            if len(src) == 1 and src == ch:
                result.append(dst)
                i += 1
                matched = True
                break
        if matched:
            continue

        result.append(ch)
        i += 1

    slug = ''.join(result)
    slug = re.sub(r'[^a-z0-9]+', '-', slug)
    slug = slug.strip('-')
    return slug


def main():
    with open('../catalog/fixtures/categories.csv', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = reader.fieldnames

    seen = {}
    duplicates = []

    for row in rows:
        old_slug = row['slug']
        new_slug = transliterate(row['name'])
        row['slug'] = new_slug

        if new_slug in seen:
            duplicates.append((row['name'], new_slug, seen[new_slug]))
        else:
            seen[new_slug] = row['name']

        if old_slug != new_slug:
            print(f'{old_slug:<55} → {new_slug}')

    with open('categories_new.csv', 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print()
    if duplicates:
        print(f'ДУБЛИ ({len(duplicates)}):')
        for name, slug, first in duplicates:
            print(f'  {slug}  ←  {name}  (уже у {first})')
    else:
        print('Дублей нет.')

    print(f'\nГотово: categories_new.csv ({len(rows)} строк)')


if __name__ == '__main__':
    main()