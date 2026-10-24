"""Подготовка двух независимых работ и страницы выбора в dist/."""
from pathlib import Path
import shutil

root = Path(__file__).resolve().parents[1]
output = root / 'dist'
if output.exists():
    shutil.rmtree(output)
output.mkdir()
shutil.copy2(root / 'index.html', output / 'index.html')
for course in ('kr1', 'kr2'):
    target = output / course
    target.mkdir()
    for file in (root / course).glob('*.html'):
        shutil.copy2(file, target / file.name)
    for directory in ('css', 'js', 'images', 'fonts', 'vendor'):
        source = root / course / directory
        if source.exists():
            shutil.copytree(source, target / directory)
(output / '.nojekyll').touch()
print(f'Готово: {len(list(output.rglob("*.html")))} страниц и локальные ресурсы обеих работ в dist/')
