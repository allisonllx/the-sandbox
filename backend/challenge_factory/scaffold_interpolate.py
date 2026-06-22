"""Dynamic scaffold generation from TechnicalChallengeSpec."""

from __future__ import annotations

import ast
from copy import deepcopy

from ..sandbox.starter_scaffold import generate_starter_files
from .archetype_catalog import get_archetype_defaults
from .models import TechnicalArchetype
from .scaffold_technical import _optimized_queries_py
from .spec_models import TechnicalChallengeSpec
from .spec_projection import spec_to_readme, spec_to_spec_md


def _module_import_path(module_path: str) -> tuple[str, str]:
    """Return (import_path, module_file) e.g. src/foo.py -> src.foo, src/foo.py"""
    if not module_path.endswith(".py"):
        module_path = f"{module_path}.py"
    import_path = module_path.replace("/", ".").removesuffix(".py")
    return import_path, module_path


def _render_stubs(spec: TechnicalChallengeSpec) -> str:
    defaults = get_archetype_defaults(spec.classification.archetype)
    default_names = {e.name for e in defaults.public_api}
    spec_names = {e.name for e in spec.interface_contract.public_api}
    if defaults.stub_body and default_names == spec_names:
        return defaults.stub_body
    lines = ['"""Primary module — student implementation."""', "", "from __future__ import annotations", ""]
    for entry in spec.interface_contract.public_api:
        sig = entry.signature.strip()
        if not sig.startswith("def "):
            sig = f"def {sig}"
        lines.append(sig + ":")
        lines.append(f'    """TODO: implement {entry.name}."""')
        lines.append("    raise NotImplementedError")
        lines.append("")
    return "\n".join(lines)


def _render_reference(spec: TechnicalChallengeSpec) -> str:
    defaults = get_archetype_defaults(spec.classification.archetype)
    default_names = {e.name for e in defaults.public_api}
    spec_names = {e.name for e in spec.interface_contract.public_api}
    if defaults.reference_body and default_names == spec_names:
        return defaults.reference_body
    lines = ['"""Primary module — reference implementation."""', "", "from __future__ import annotations", ""]
    for entry in spec.interface_contract.public_api:
        sig = entry.signature.strip()
        if not sig.startswith("def "):
            sig = f"def {sig}"
        lines.append(sig + ":")
        lines.append(f"    return None  # reference stub for {entry.name}")
        lines.append("")
    return "\n".join(lines)


def _render_tests(spec: TechnicalChallengeSpec) -> str:
    defaults = get_archetype_defaults(spec.classification.archetype)
    default_names = {e.name for e in defaults.public_api}
    spec_names = {e.name for e in spec.interface_contract.public_api}
    if defaults.test_body and default_names == spec_names:
        return defaults.test_body
    import_path, _ = _module_import_path(spec.interface_contract.primary_module)
    names = [e.name for e in spec.interface_contract.public_api]
    imports = ", ".join(names)
    lines = [
        f'"""Public tests for {import_path}."""',
        "",
        f"from {import_path} import {imports}",
        "",
        "def test_public_api_importable():",
    ]
    for name in names:
        lines.append(f"    assert callable({name})")
    return "\n".join(lines) + "\n"


def _render_main(spec: TechnicalChallengeSpec) -> str:
    import_path, _ = _module_import_path(spec.interface_contract.primary_module)
    first = spec.interface_contract.public_api[0].name if spec.interface_contract.public_api else "main"
    return f'''"""CLI entrypoint — optional local smoke test."""

from __future__ import annotations

from {import_path} import {first}


def main() -> None:
    print("Run pytest tests/ -v to validate your implementation.")


if __name__ == "__main__":
    main()
'''


def _contract_symbol_check(spec: TechnicalChallengeSpec, test_content: str) -> list[str]:
    errors: list[str] = []
    for entry in spec.interface_contract.public_api:
        if entry.name not in test_content:
            errors.append(f"tests/test_public.py missing reference to public API symbol {entry.name}")
    primary = spec.interface_contract.primary_module
    import_path, _ = _module_import_path(primary)
    if import_path not in test_content and primary.replace("/", ".") not in test_content:
        errors.append(f"tests/test_public.py missing import from {import_path}")
    return errors


def generate_scaffold_from_spec(
    challenge_id: str,
    spec: TechnicalChallengeSpec,
) -> tuple[dict[str, str], dict[str, str]]:
    """
    Build starter + reference trees from spec (dynamic stubs/tests, no hardcoded signatures).
    """
    archetype = spec.classification.archetype

    if archetype == TechnicalArchetype.data_core:
        starter = generate_starter_files(challenge_id, spec.title)
        starter["README.md"] = spec_to_readme(spec, challenge_id=challenge_id)
        starter["docs/SPEC.md"] = spec_to_spec_md(spec)
        starter["main.py"] = _render_main(spec)
        reference = deepcopy(starter)
        reference["src/queries.py"] = _optimized_queries_py()
        return starter, reference

    starter: dict[str, str] = {
        "README.md": spec_to_readme(spec, challenge_id=challenge_id),
        "docs/SPEC.md": spec_to_spec_md(spec),
        "main.py": _render_main(spec),
        spec.interface_contract.primary_module: _render_stubs(spec),
        "tests/test_public.py": _render_tests(spec),
    }
    for path, content in spec.fixtures.items():
        starter[path] = content

    reference = deepcopy(starter)
    reference[spec.interface_contract.primary_module] = _render_reference(spec)

    for support in spec.interface_contract.support_modules:
        if support not in starter:
            starter[support] = '"""Support module stub."""\n'
            reference[support] = '"""Support module reference."""\n'

    return starter, reference


def validate_contract_alignment(spec: TechnicalChallengeSpec, starter_files: dict[str, str]) -> list[str]:
    """Fail if tests import symbols not in interface_contract."""
    errors: list[str] = []
    test_blob = starter_files.get("tests/test_public.py", "")
    errors.extend(_contract_symbol_check(spec, test_blob))

    primary = spec.interface_contract.primary_module
    primary_content = starter_files.get(primary, "")
    for entry in spec.interface_contract.public_api:
        if entry.name not in primary_content:
            errors.append(f"{primary} missing public API function {entry.name}")
        try:
            tree = ast.parse(primary_content, filename=primary)
            func_names = {n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
            if entry.name not in func_names:
                errors.append(f"{primary} has no function definition for {entry.name}")
        except SyntaxError as exc:
            errors.append(f"{primary}: syntax error — {exc.msg}")

    if "docs/SPEC.md" not in starter_files:
        errors.append("starter missing docs/SPEC.md")
    if "main.py" not in starter_files:
        errors.append("starter missing main.py")

    return errors
