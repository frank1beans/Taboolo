#!/usr/bin/env python3
"""
Genera la documentazione per ogni script Python presente nella cartella backend.

Il risultato viene scritto in backend/docs/SCRIPT_REFERENCE.md con sezioni
ordinate per sottocartella. Eseguire questo script dopo aver aggiunto o
modificato file .py per mantenere il catalogo aggiornato.
"""

from __future__ import annotations

import ast
import textwrap
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, List, Sequence


try:  # Python 3.9+
    from ast import unparse as ast_unparse
except ImportError:  # pragma: no cover - fallback per versioni vecchie
    def ast_unparse(node: ast.AST) -> str:
        return ast.dump(node)


BACKEND_ROOT = Path(__file__).resolve().parents[1]
DOC_DIR = BACKEND_ROOT / "docs"
DOC_PATH = DOC_DIR / "SCRIPT_REFERENCE.md"


@dataclass
class ClassInfo:
    name: str
    bases: List[str]
    doc: str
    methods: List[str]


@dataclass
class FunctionInfo:
    name: str
    signature: str
    doc: str
    is_async: bool


@dataclass
class ModuleInfo:
    relative_path: str
    category: str
    lines: int
    description: str
    imports: List[str]
    classes: List[ClassInfo] = field(default_factory=list)
    functions: List[FunctionInfo] = field(default_factory=list)
    constants: List[str] = field(default_factory=list)
    has_cli_entrypoint: bool = False
    parser_error: str | None = None


def main() -> None:
    DOC_DIR.mkdir(parents=True, exist_ok=True)
    python_files = sorted(
        path
        for path in BACKEND_ROOT.rglob("*.py")
        if "__pycache__" not in path.parts
    )
    modules: List[ModuleInfo] = []
    for path in python_files:
        rel_path = path.relative_to(BACKEND_ROOT).as_posix()
        category = rel_path.split("/")[0]
        info = analyze_module(path, rel_path, category)
        modules.append(info)

    by_category: dict[str, list[ModuleInfo]] = defaultdict(list)
    for module in modules:
        by_category[module.category].append(module)

    lines: List[str] = []
    lines.append("# Catalogo script backend")
    lines.append("")
    lines.append(
        "Documento generato automaticamente da `backend/scripts/generate_backend_docs.py`."
    )
    lines.append(
        f"Totale script indicizzati: **{len(modules)}** distribuiti in "
        f"{len(by_category)} macro-cartelle."
    )
    lines.append("")

    for category in sorted(by_category):
        bucket = sorted(by_category[category], key=lambda item: item.relative_path)
        lines.append(f"## {category} ({len(bucket)} script)")
        lines.append("")
        for module in bucket:
            lines.extend(render_module(module))
            lines.append("")

    DOC_PATH.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(f"Catalogo aggiornato: {DOC_PATH.relative_to(Path.cwd())}")


def analyze_module(path: Path, rel_path: str, category: str) -> ModuleInfo:
    content = path.read_bytes().decode("utf-8", errors="ignore")
    info = ModuleInfo(
        relative_path=rel_path,
        category=category,
        lines=len(content.splitlines()),
        description="",
        imports=[],
    )

    try:
        tree = ast.parse(content)
    except SyntaxError as exc:  # pragma: no cover - codice difettoso
        info.parser_error = f"Impossibile analizzare il file: {exc}"
        info.description = info.parser_error
        return info

    module_doc = ast.get_docstring(tree)
    info.description = sanitize_docstring(
        module_doc,
        fallback=f"Modulo senza docstring. Contiene {count_defs(tree, ast.ClassDef)} classi "
        f"e {count_defs(tree, (ast.FunctionDef, ast.AsyncFunctionDef))} funzioni.",
    )
    info.imports = extract_imports(tree)
    info.classes = extract_classes(tree)
    info.functions = extract_functions(tree)
    info.constants = extract_constants(tree)
    info.has_cli_entrypoint = detect_cli_entry(tree)
    return info


def extract_imports(tree: ast.AST) -> List[str]:
    values: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                values.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            prefix = "." * node.level + (node.module or "")
            for alias in node.names:
                values.add(f"{prefix}.{alias.name}".strip("."))
    return sorted(values)


def extract_classes(tree: ast.Module) -> List[ClassInfo]:
    classes: List[ClassInfo] = []
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            doc = sanitize_docstring(ast.get_docstring(node), "Nessuna docstring.")
            bases = [ast_unparse(base).strip() for base in node.bases] or ["object"]
            methods = [
                child.name
                for child in node.body
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
                and not child.name.startswith("_")
            ]
            classes.append(ClassInfo(node.name, bases, doc, methods))
    return classes


def extract_functions(tree: ast.Module) -> List[FunctionInfo]:
    functions: List[FunctionInfo] = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            doc = sanitize_docstring(ast.get_docstring(node), "Nessuna docstring.")
            signature = render_signature(node)
            functions.append(
                FunctionInfo(name=node.name, signature=signature, doc=doc, is_async=isinstance(node, ast.AsyncFunctionDef))
            )
    return functions


def extract_constants(tree: ast.Module) -> List[str]:
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id.isupper():
                    names.add(target.id)
        elif isinstance(node, ast.AnnAssign):
            target = node.target
            if isinstance(target, ast.Name) and target.id.isupper():
                names.add(target.id)
    return sorted(names)


def detect_cli_entry(tree: ast.AST) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.If):
            test = node.test
            if (
                isinstance(test, ast.Compare)
                and isinstance(test.left, ast.Name)
                and test.left.id == "__name__"
                and len(test.comparators) == 1
                and isinstance(test.comparators[0], ast.Constant)
                and test.comparators[0].value == "__main__"
            ):
                return True
    return False


def render_module(module: ModuleInfo) -> List[str]:
    lines: List[str] = []
    lines.append(f"### `{module.relative_path}`")
    lines.append(f"- **Linee**: {module.lines}")
    lines.append(f"- **Descrizione**: {module.description}")
    if module.parser_error:
        return lines
    imports_preview = format_list(module.imports, limit=12)
    lines.append(
        f"- **Dipendenze principali ({len(module.imports)})**: {imports_preview or 'Nessuna'}"
    )
    lines.append(render_classes_section(module.classes))
    lines.append(render_functions_section(module.functions))
    constants_preview = format_list(module.constants, limit=12)
    lines.append(
        f"- **Costanti dichiarate ({len(module.constants)})**: {constants_preview or 'Nessuna'}"
    )
    lines.append(
        "- **Entry point CLI**: "
        + ("Presente (`if __name__ == \"__main__\"`)." if module.has_cli_entrypoint else "Assente.")
    )
    return lines


def render_classes_section(classes: Sequence[ClassInfo]) -> str:
    if not classes:
        return "- **Classi**: nessuna."
    lines = ["- **Classi**:"]
    for cls in classes:
        bases = ", ".join(cls.bases)
        methods = ", ".join(f"`{method}`" for method in cls.methods) or "nessun metodo pubblico"
        lines.append(
            f"  - `{cls.name}` (bases: {bases}) - {cls.doc} Metodi: {methods}."
        )
    return "\n".join(lines)


def render_functions_section(functions: Sequence[FunctionInfo]) -> str:
    if not functions:
        return "- **Funzioni**: nessuna."
    lines = ["- **Funzioni**:"]
    for fn in functions:
        prefix = "async " if fn.is_async else ""
        lines.append(
            f"  - `{prefix}{fn.signature}` - {fn.doc}"
        )
    return "\n".join(lines)


def render_signature(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    args = node.args
    parts: List[str] = []

    positionals = args.posonlyargs + args.args
    defaults = list(args.defaults)
    default_offset = len(positionals) - len(defaults)
    defaults_map = {
        arg.arg: ast_unparse(default).strip()
        for arg, default in zip(positionals[default_offset:], defaults)
    }

    for idx, arg in enumerate(args.posonlyargs):
        parts.append(format_argument(arg, defaults_map.get(arg.arg)))
        if idx == len(args.posonlyargs) - 1:
            parts.append("/")

    for arg in args.args[len(args.posonlyargs) :]:
        parts.append(format_argument(arg, defaults_map.get(arg.arg)))

    if args.vararg:
        parts.append(format_argument(args.vararg, prefix="*"))
    elif args.kwonlyargs:
        parts.append("*")

    for arg, default in zip(args.kwonlyargs, args.kw_defaults):
        default_repr = ast_unparse(default).strip() if default is not None else None
        parts.append(format_argument(arg, default_repr))

    if args.kwarg:
        parts.append(format_argument(args.kwarg, prefix="**"))

    return f"{node.name}(" + ", ".join(part for part in parts if part) + ")"


def format_argument(arg: ast.arg, default: str | None = None, prefix: str = "") -> str:
    annotation = f": {ast_unparse(arg.annotation).strip()}" if arg.annotation else ""
    default_part = f" = {default}" if default is not None else ""
    return f"{prefix}{arg.arg}{annotation}{default_part}"


def sanitize_docstring(value: str | None, fallback: str) -> str:
    if not value:
        return fallback
    flattened = " ".join(value.strip().split())
    return textwrap.shorten(flattened, width=320, placeholder="...")


def format_list(values: Iterable[str], limit: int = 10) -> str:
    values = list(values)
    if not values:
        return ""
    preview = values[:limit]
    formatted = ", ".join(f"`{item}`" for item in preview)
    extra = len(values) - len(preview)
    if extra > 0:
        formatted += f", ... (+{extra})"
    return formatted


def count_defs(tree: ast.Module, types: type | tuple[type, ...]) -> int:
    return sum(1 for node in tree.body if isinstance(node, types))


if __name__ == "__main__":
    main()
