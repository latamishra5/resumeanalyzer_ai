"""Architectural boundary, compile, and deprecation checks."""

import ast
import os
from pathlib import Path
import py_compile
import re

ROOT_DIR = Path(__file__).resolve().parent.parent
_EMOJI_RE = re.compile(r"[\U0001F300-\U0001FAFF\u2600-\u27BF\u2300-\u23FF\u2B50\u2705\u274C\ufe0f]")


def _iter_python_files():
    targets = ["app.py", "run_app.py", "run_admin.py", "frontend", "backend", "scripts", "tests"]
    py_files = []
    for target in targets:
        full = ROOT_DIR / target
        if full.is_file():
            py_files.append(full)
        elif full.is_dir():
            for dp, dn, fns in os.walk(full):
                dn[:] = [d for d in dn if d not in ("__pycache__", "venv", ".venv")]
                for fn in fns:
                    if fn.endswith(".py"):
                        py_files.append(Path(dp) / fn)
    return sorted(py_files)


def test_all_python_files_compile():
    files = _iter_python_files()
    assert len(files) >= 45
    for path in files:
        py_compile.compile(str(path), doraise=True)


def test_architecture_boundaries_and_frontend_hygiene():
    boundary_errors = []
    frontend_violations = []
    deprecation_hits = []

    for path in _iter_python_files():
        rel = path.relative_to(ROOT_DIR).as_posix()
        src = path.read_text(encoding="utf-8")
        tree = ast.parse(src, filename=rel)

        for node in ast.walk(tree):
            mods = []
            if isinstance(node, ast.Import):
                mods = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                mods = [node.module]
            for mod in mods:
                top = mod.split(".")[0]
                if rel.startswith("backend/") and rel != "backend/admin/app.py":
                    if top in ("streamlit", "frontend"):
                        boundary_errors.append((rel, mod))
                elif rel.startswith("frontend/"):
                    if top in ("sqlite3", "sqlalchemy") or mod.startswith("backend.admin"):
                        boundary_errors.append((rel, mod))

        if rel.startswith(("frontend/", "backend/", "scripts/", "app.py", "run_app.py", "run_admin.py")):
            for lineno, line in enumerate(src.splitlines(), 1):
                if rel.startswith("frontend/"):
                    for bad in (
                        "is_admin",
                        "Admin Login",
                        "current_admin_email",
                        "render_admin_",
                        "verify_admin",
                        "log_admin_action",
                        "Check out these repositories:",
                        "st.snow(",
                        "st.balloons(",
                    ):
                        if bad in line:
                            frontend_violations.append((rel, lineno, bad))
                for dep in ("use_container_width", "use_column_width", "experimental_rerun", "google.generativeai", "datetime.utcnow"):
                    if dep in line:
                        deprecation_hits.append((rel, lineno, dep))
                if rel.startswith(("frontend/", "backend/admin/", "backend/builders/", "backend/jobs/", "backend/services/")) and _EMOJI_RE.search(line):
                    frontend_violations.append((rel, lineno, "unicode_emoji"))

    assert not boundary_errors, f"Boundary violations: {boundary_errors}"
    assert not frontend_violations, f"Frontend hygiene violations: {frontend_violations}"
    assert not deprecation_hits, f"Deprecation hits: {deprecation_hits}"
