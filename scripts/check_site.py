"""Проверка обеих работ или одной: python3 scripts/check_site.py [kr1|kr2]."""
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
COURSES = ('kr1', 'kr2')
if len(sys.argv) > 2 or (len(sys.argv) == 2 and sys.argv[1] not in COURSES):
    raise SystemExit('Использование: python3 scripts/check_site.py [kr1|kr2]')
selected = (sys.argv[1],) if len(sys.argv) == 2 else COURSES
errors = []

class Page(HTMLParser):
    def __init__(self, path):
        super().__init__(convert_charrefs=True)
        self.path = path
        self.tags = Counter()
        self.ids = set()
        self.classes = set()
        self.references = []
        self.idrefs = []
        self.fields = []
        self.labels = set()
        self.label_depth = 0
        self.stylesheets = []
        self.scripts = []
        self.title = ''
        self.in_title = False
        self.language = False
        self.feed(path.read_text(encoding='utf-8'))

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.tags[tag] += 1
        self.classes.update(attrs.get('class', '').split())
        if tag == 'html':
            self.language = attrs.get('lang') == 'ru'
        if tag == 'title':
            self.in_title = True
        if 'id' in attrs:
            if attrs['id'] in self.ids:
                errors.append(f'{self.path}: повтор id={attrs["id"]}')
            self.ids.add(attrs['id'])
        if tag == 'link' and attrs.get('rel') == 'stylesheet':
            self.stylesheets.append(attrs.get('href'))
        if tag == 'script' and attrs.get('src'):
            self.scripts.append(attrs['src'])
        if tag == 'label':
            self.label_depth += 1
            if attrs.get('for'):
                self.labels.add(attrs['for'])
        if tag in ('input', 'select', 'textarea'):
            self.fields.append((attrs, self.label_depth > 0))
        if tag == 'img' and 'alt' not in attrs:
            errors.append(f'{self.path}: изображение без alt')
        for attribute in ('href', 'src', 'action'):
            if attrs.get(attribute):
                self.references.append(attrs[attribute])
        for attribute in ('aria-labelledby', 'aria-describedby', 'aria-controls'):
            self.idrefs.extend(attrs.get(attribute, '').split())
        for attribute in ('data-bs-target', 'data-bs-parent'):
            value = attrs.get(attribute, '')
            if value.startswith('#'):
                self.idrefs.append(value[1:])

    def handle_endtag(self, tag):
        if tag == 'title':
            self.in_title = False
        if tag == 'label':
            self.label_depth -= 1

    def handle_data(self, data):
        if self.in_title:
            self.title += data

files = [file.resolve() for course in selected for file in (ROOT / course).glob('*.html')]
if len(selected) == 2:
    files.append(ROOT / 'index.html')
pages = {file: Page(file) for file in files}
for course in selected:
    required = {'index.html', 'catalog.html', 'product.html', 'order.html'}
    if course == 'kr1':
        required.add('contacts.html')
    found = {p.name for p in pages if p.parent.name == course}
    if not required <= found:
        errors.append(f'{course}: отсутствуют {required - found}')

titles = [page.title for page in pages.values()]
if len(set(titles)) != len(titles):
    errors.append('Заголовки title должны быть уникальны')
for file, page in pages.items():
    name = str(file.relative_to(ROOT))
    if not file.read_text().lower().startswith('<!doctype html>'):
        errors.append(f'{name}: нет HTML5 doctype')
    if not page.language or not page.title:
        errors.append(f'{name}: проверьте lang и title')
    for tag in ('main', 'h1', 'head', 'body'):
        if page.tags[tag] != 1:
            errors.append(f'{name}: требуется ровно один {tag}')
    for tag in ('header', 'nav', 'footer'):
        if not page.tags[tag]:
            errors.append(f'{name}: нет {tag}')
    if file.parent.name == 'kr1' and page.stylesheets != ['css/style.css']:
        errors.append(f'{name}: КР1 должна использовать только собственный CSS')
    if file.parent.name == 'kr2':
        if page.stylesheets != ['vendor/bootstrap/css/bootstrap.min.css', 'css/custom.css']:
            errors.append(f'{name}: неверный порядок Bootstrap и custom.css')
        if 'vendor/bootstrap/js/bootstrap.bundle.min.js' not in page.scripts:
            errors.append(f'{name}: нет Bootstrap JS Bundle')
        if not {'navbar', 'modal'} <= page.classes:
            errors.append(f'{name}: нет общего navbar/modal')
    for ref in page.references:
        parsed = urlsplit(ref)
        if parsed.scheme or parsed.netloc:
            continue
        target = (file.parent / unquote(parsed.path)).resolve() if parsed.path else file
        if not target.is_relative_to(ROOT) or not target.is_file():
            errors.append(f'{name}: не существует {ref}')
        elif parsed.fragment and target.suffix == '.html':
            target_page = pages.get(target) or Page(target)
            if unquote(parsed.fragment) not in target_page.ids:
                errors.append(f'{name}: не найден якорь {ref}')
        if file.parent.name in COURSES and not target.is_relative_to(file.parent):
            errors.append(f'{name}: работа зависит от файла вне своей папки: {ref}')
    for target in page.idrefs:
        if target not in page.ids:
            errors.append(f'{name}: нет цели aria/Bootstrap {target}')
    for attrs, wrapped_label in page.fields:
        if not attrs.get('name'):
            errors.append(f'{name}: поле без name')
        if not wrapped_label and attrs.get('id') not in page.labels:
            errors.append(f'{name}: поле без связанного label: {attrs.get("name")}')
    for target in page.labels:
        if target not in page.ids:
            errors.append(f'{name}: label ссылается на несуществующий id {target}')

for course in selected:
    for css in (ROOT / course / 'css').glob('*.css'):
        for url in re.findall(r'url\([\'"]?([^\)\'\"]+)', css.read_text()):
            if not urlsplit(url).scheme and not (css.parent / url).resolve().is_file():
                errors.append(f'{css}: не существует ресурс {url}')
if 'kr2' in selected:
    classes = set().union(*(p.classes for f, p in pages.items() if f.parent.name == 'kr2'))
    required_classes = {'container', 'row', 'col-12', 'col-md-6', 'col-lg-4', 'g-4', 'navbar', 'card', 'btn', 'badge', 'alert', 'modal', 'form-control', 'form-select', 'input-group', 'form-check', 'accordion', 'nav-pills'}
    if not required_classes <= classes:
        errors.append(f'КР2: не найдены компоненты {required_classes - classes}')
if errors:
    print('\n'.join(errors), file=sys.stderr)
    raise SystemExit(1)
print(f'OK: {len(pages)} страниц; структура, ссылки, ресурсы, поля, ARIA и компоненты проверены ({", ".join(selected)}).')
