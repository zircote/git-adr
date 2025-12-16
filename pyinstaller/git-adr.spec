# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec file for git-adr.

This spec file bundles git-adr with all optional dependencies ([all] extras)
into a standalone executable.

Usage:
    pyinstaller pyinstaller/git-adr.spec

Output:
    dist/git-adr (single executable)
"""

import sys
from pathlib import Path

# Get the project root
SPEC_DIR = Path(SPECPATH)
PROJECT_ROOT = SPEC_DIR.parent
SRC_DIR = PROJECT_ROOT / "src"

# Add src to path for analysis
sys.path.insert(0, str(SRC_DIR))

block_cipher = None

# Hidden imports that PyInstaller can't detect statically
# These are loaded conditionally or via importlib
hidden_imports = [
    # Core dependencies
    "typer",
    "typer.core",
    "typer.main",
    "typer.completion",
    "click",
    "click.core",
    "click.decorators",
    "click.exceptions",
    "click.formatting",
    "click.parser",
    "click.shell_completion",
    "click.termui",
    "click.testing",
    "click.types",
    "click.utils",
    "rich",
    "rich.console",
    "rich.markdown",
    "rich.panel",
    "rich.prompt",
    "rich.table",
    "rich.text",
    "rich.progress",
    "rich.syntax",
    "rich.traceback",
    "rich._emoji_codes",
    "rich._palettes",
    "pygments",
    "pygments.lexers",
    "pygments.styles",
    "yaml",
    "frontmatter",
    "mistune",
    "jinja2",
    "jinja2.ext",
    "markupsafe",
    # AI extras (langchain ecosystem)
    "langchain_core",
    "langchain_core.callbacks",
    "langchain_core.language_models",
    "langchain_core.messages",
    "langchain_core.outputs",
    "langchain_core.prompts",
    "langchain_core.runnables",
    "langchain_openai",
    "langchain_openai.chat_models",
    "langchain_anthropic",
    "langchain_anthropic.chat_models",
    "langchain_google_genai",
    "langchain_google_genai.chat_models",
    "langchain_ollama",
    "langchain_ollama.chat_models",
    # OpenAI SDK
    "openai",
    "openai._client",
    "openai.types",
    "openai.resources",
    # Anthropic SDK
    "anthropic",
    "anthropic._client",
    "anthropic.types",
    # Google Generative AI
    "google.generativeai",
    "google.ai.generativelanguage",
    "google.api_core",
    "google.auth",
    "google.protobuf",
    # tiktoken (tokenization)
    "tiktoken",
    "tiktoken.core",
    "tiktoken_ext",
    "tiktoken_ext.openai_public",
    "regex",
    # HTTP/networking
    "httpx",
    "httpcore",
    "h11",
    "h2",
    "hpack",
    "hyperframe",
    "anyio",
    "sniffio",
    "certifi",
    "idna",
    # Async
    "asyncio",
    "aiofiles",
    # Data validation
    "pydantic",
    "pydantic.fields",
    "pydantic.main",
    "pydantic.types",
    "pydantic_core",
    "typing_extensions",
    "typing_inspection",
    "annotated_types",
    # Wiki extras
    "github",
    "github.GithubException",
    "github.MainClass",
    "gitlab",
    "gitlab.v4",
    "gitlab.v4.objects",
    # Export extras
    "docx",
    "docx.document",
    "docx.shared",
    "docx.enum",
    "docx.oxml",
    "lxml",
    "lxml.etree",
    "lxml._elementpath",
    # gRPC (required by some langchain providers)
    "grpc",
    "grpc._cython",
    # Other utilities
    "urllib3",
    "charset_normalizer",
    "requests",
    "tenacity",
    "packaging",
    "packaging.version",
    "packaging.specifiers",
    "distro",
    "platformdirs",
    "filelock",
    "tqdm",
    "dataclasses_json",
    "marshmallow",
    "orjson",
    "jsonpatch",
]

# Data files to bundle (templates, etc.)
datas = [
    # Bundle template files
    (str(SRC_DIR / "git_adr" / "templates"), "git_adr/templates"),
]

# Binary files (native extensions)
binaries = []

# Packages to exclude (reduce size)
excludes = [
    # GUI frameworks (not needed for CLI)
    "tkinter",
    "_tkinter",
    "tcl",
    "tk",
    "matplotlib",
    "PIL",
    "PyQt5",
    "PyQt6",
    "PySide2",
    "PySide6",
    "wx",
    # Testing (dev only)
    "pytest",
    "pytest_cov",
    "pytest_asyncio",
    "_pytest",
    "coverage",
    # Linting (dev only)
    "ruff",
    "mypy",
    "bandit",
    "pip_audit",
    # Jupyter (not needed)
    "IPython",
    "jupyter",
    "notebook",
    "ipykernel",
    # Other heavy unused packages
    "scipy",
    "numpy",
    "pandas",
    "sklearn",
    "torch",
    "tensorflow",
    "transformers",
]

# Analysis
a = Analysis(
    [str(SRC_DIR / "git_adr" / "cli.py")],
    pathex=[str(SRC_DIR)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Filter out unnecessary files to reduce size
def filter_binaries(binaries):
    """Remove unnecessary binary files."""
    excluded_patterns = [
        "libopenblas",  # Large numerical library
        "libmkl",       # Intel MKL
        "libtorch",     # PyTorch
        "libtensorflow", # TensorFlow
    ]
    return [
        (name, path, typ)
        for name, path, typ in binaries
        if not any(pattern in name.lower() for pattern in excluded_patterns)
    ]

a.binaries = filter_binaries(a.binaries)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Using onedir mode for fast startup (<1 sec)
# onefile mode has ~3 sec startup due to extraction overhead
exe = EXE(
    pyz,
    a.scripts,
    exclude_binaries=True,  # Don't include binaries in EXE for onedir
    name="git-adr",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # UPX causes issues on macOS
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# Collect all files into directory (dist/git-adr/)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,  # UPX causes issues on macOS
    upx_exclude=[],
    name="git-adr",
)
