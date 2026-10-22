"""Подготовка публичных файлов для GitHub Pages, без зависимостей и компиляции."""
from pathlib import Path
import shutil

root = Path(__file__).resolve().parents[1]
output = root / 'dist'
if output.exists():
    shutil.rmtree(output)
output.mkdir()
for file in root.glob('*.html'):
    shutil.copy2(file, output / file.name)
for directory in ('css', 'js', 'images', 'fonts'):
    shutil.copytree(root / directory, output / directory)
(output / '.nojekyll').touch()
print(f'Готово: {len(list(output.glob("*.html")))} страниц и локальные ресурсы в dist/')
