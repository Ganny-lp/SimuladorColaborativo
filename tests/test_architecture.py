"""
Regras de dependência da Clean Architecture, verificadas sobre os imports reais.

    domain  ←  application  ←  infrastructure          (backend)
                    ↑
                 frontend  (só conhece application/DTOs; nunca domain/infrastructure)
"""
import ast
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

# camada → prefixos de módulos que ela NÃO pode importar
FORBIDDEN = {
    "backend/domain": ("backend.application", "backend.infrastructure", "frontend", "streamlit", "requests", "pandas", "plotly"),
    "backend/application": ("backend.infrastructure", "frontend", "streamlit", "requests", "pandas", "plotly"),
    "backend/infrastructure": ("frontend", "streamlit"),
    "frontend": ("backend.domain", "backend.infrastructure", "requests", "composition_root"),
}


def _imports(path: Path):
    """Módulos importados, ignorando blocos ``if TYPE_CHECKING`` (só tipagem)."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found = []

    def visit(node):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.If) and "TYPE_CHECKING" in ast.dump(child.test):
                continue
            if isinstance(child, ast.Import):
                found.extend(alias.name for alias in child.names)
            elif isinstance(child, ast.ImportFrom) and child.module and child.level == 0:
                found.append(child.module)
            visit(child)

    visit(tree)
    return found


def _cases():
    for layer, forbidden in FORBIDDEN.items():
        for path in sorted((ROOT / layer).rglob("*.py")):
            yield pytest.param(layer, forbidden, path, id=str(path.relative_to(ROOT)))


@pytest.mark.parametrize("layer, forbidden, path", list(_cases()))
def test_layer_does_not_import_forbidden_modules(layer, forbidden, path):
    violations = [
        module for module in _imports(path)
        if any(module == f or module.startswith(f + ".") for f in forbidden)
    ]
    assert not violations, f"{path.relative_to(ROOT)} ({layer}) importa {violations}"
