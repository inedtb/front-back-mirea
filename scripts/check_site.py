"""Проверка HTML и внутренних ссылок. Только стандартная библиотека Python."""
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
errors = []

class Page(HTMLParser):
    def __init__(self, path):
        super().__init__(convert_charrefs=True)
        self.path = path
        self.tags = Counter()
        self.ids = set()
        self.references = []
        self.fields = []
        self.labels = set()
        self.title = ''
        self.in_title = False
        self.stylesheet = False
        self.language = False
        self.feed(path.read_text(encoding='utf-8'))

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.tags[tag] += 1
        if tag == 'html':
            self.language = attrs.get('lang') == 'ru'
        if tag == 'title':
            self.in_title = True
        if 'id' in attrs:
            if attrs['id'] in self.ids:
                errors.append(f'{self.path.name}: повтор id={attrs["id"]}')
            self.ids.add(attrs['id'])
        if tag == 'link' and attrs.get('href') == 'css/style.css':
            self.stylesheet = True
        if tag == 'label' and attrs.get('for'):
            self.labels.add(attrs['for'])
        if tag in ('input', 'select', 'textarea'):
            self.fields.append((tag, attrs))
        if tag == 'img' and 'alt' not in attrs:
            errors.append(f'{self.path.name}: изображение без alt')
        for attribute in ('href', 'src', 'action'):
            if attrs.get(attribute):
                self.references.append(attrs[attribute])

    def handle_endtag(self, tag):
        if tag == 'title':
            self.in_title = False

    def handle_data(self, data):
        if self.in_title:
            self.title += data

pages = {p.name: Page(p) for p in sorted(ROOT.glob('*.html'))}
required = {'index.html', 'catalog.html', 'product.html', 'order.html', 'contacts.html'}
if not required <= pages.keys():
    errors.append(f'Отсутствуют обязательные страницы: {required - pages.keys()}')

titles = [page.title for page in pages.values()]
if len(set(titles)) != len(titles):
    errors.append('Заголовки title должны быть уникальны')

for filename, page in pages.items():
    source = page.path.read_text(encoding='utf-8')
    if not source.lower().startswith('<!doctype html>'):
        errors.append(f'{filename}: отсутствует HTML5 doctype')
    if not page.language or not page.stylesheet or not page.title:
        errors.append(f'{filename}: проверьте lang, title, общий CSS')
    for tag in ('main', 'h1', 'head', 'body'):
        if page.tags[tag] != 1:
            errors.append(f'{filename}: требуется ровно один {tag}')
    for tag in ('header', 'nav', 'footer'):
        if not page.tags[tag]:
            errors.append(f'{filename}: отсутствует {tag}')
    for ref in page.references:
        parsed = urlsplit(ref)
        if parsed.scheme or parsed.netloc:
            continue
        target = (page.path.parent / unquote(parsed.path)).resolve() if parsed.path else page.path
        if not target.is_relative_to(ROOT):
            errors.append(f'{filename}: ссылка выходит за каталог проекта: {ref}')
        elif not target.is_file():
            errors.append(f'{filename}: не существует {ref}')
        elif parsed.fragment and target.suffix == '.html':
            if unquote(parsed.fragment) not in pages[target.name].ids:
                errors.append(f'{filename}: не найден якорь {ref}')
    for tag, attrs in page.fields:
        if not attrs.get('name'):
            errors.append(f'{filename}: у {tag} нет name')
        if attrs.get('type') not in ('checkbox', 'radio', 'hidden'):
            if not attrs.get('id') or attrs['id'] not in page.labels:
                errors.append(f'{filename}: поле без связанного label: {attrs.get("name")}')

css = ROOT / 'css/style.css'
for url in re.findall(r'url\([\'"]?([^\)\'\"]+)', css.read_text()):
    if not urlsplit(url).scheme and not (css.parent / url).resolve().is_file():
        errors.append(f'CSS: не существует ресурс {url}')

if errors:
    print('\n'.join(errors), file=sys.stderr)
    raise SystemExit(1)
print(f'OK: {len(pages)} страниц; HTML-структура, title, label, ресурсы и все внутренние ссылки проверены.')
