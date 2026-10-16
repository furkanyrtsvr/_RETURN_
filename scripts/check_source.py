"""Check source without starting device tests, Flask servers, or network clients."""
import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
count = 0
for folder_name in ('01-gorsel-degerlendirme', '02-islev-testleri'):
    folder = ROOT / folder_name
    assert folder.is_dir(), f'Missing application folder: {folder_name}'
    for path in folder.glob('*.py'):
        tree = ast.parse(path.read_text(encoding='utf-8-sig'), filename=str(path))
        count += 1
        if path.name == 'main.py':
            for node in ast.walk(tree):
                if isinstance(node, ast.Constant) and isinstance(node.value, str):
                    value = node.value
                    if re.fullmatch(r'[a-z][a-z_]*\.py', value):
                        assert '/' not in value and '\\' not in value, f'Nonportable launcher path: {path}'
                        assert (folder / value).is_file(), f'Missing launcher target: {value}'
    for line in (folder / 'requirements.txt').read_text().splitlines():
        assert not line.startswith('pip '), f'Invalid requirement in {folder.name}'
print(f'Checked {count} Python files and launcher targets.')
