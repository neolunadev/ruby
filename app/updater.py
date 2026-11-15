"""Self-update from published GitHub releases only.

Updates follow the latest full release (GitHub's "latest" excludes drafts and
pre-releases), never the main branch, so an in-progress merge never reaches
users. Two modes:

- git checkouts (developer machines): fetch the release tag and fast-forward
  to it.
- installed copies (no .git): download the release tag's zip and overlay the
  code paths, never touching models/, .env, config.json, .venv.

Both then install any requirement that is missing and respawn the app.
Nothing updates without the user's explicit confirmation in the UI.
"""

import importlib.metadata
import logging
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

log = logging.getLogger(__name__)

BASE = Path(__file__).resolve().parents[1]
VERSION_FILE = BASE / "VERSION"
REQUIREMENTS = BASE / "requirements.txt"
TORCH_INDEX = "https://download.pytorch.org/whl/cu128"
REPO = "neolunadev/ruby"
LATEST_RELEASE_URL = f"https://api.github.com/repos/{REPO}/releases/latest"


def tag_zip_url(tag: str) -> str:
    return f"https://codeload.github.com/{REPO}/zip/refs/tags/{tag}"


# Paths replaced by a zip-overlay update. Everything else (models/, .env,
# config.json, .venv, audio/) is user state and must survive updates.
CODE_PATHS = [
    "app", "engine", "scripts", "tests", "docs", ".github",
    "bot.py", "requirements.txt", "VERSION", "CHANGELOG.md",
    "README.md", "LICENSE", "claude.md", ".env.example", ".gitignore",
]


def current_version() -> str:
    try:
        return VERSION_FILE.read_text(encoding="utf-8").strip()
    except OSError:
        return "dev"


def parse_version(text: str) -> tuple[int, ...]:
    """'v0.7.0' or '0.7.0' -> (0, 7, 0); anything unparseable -> ()."""
    nums = re.findall(r"\d+", text.strip().lstrip("vV").split("-")[0])
    return tuple(int(n) for n in nums)


def is_newer(remote: str, local: str) -> bool:
    r, l = parse_version(remote), parse_version(local)
    return bool(r) and r > l


def mode(base: Path = BASE) -> str:
    return "git" if (Path(base) / ".git").is_dir() else "zip"


def _git(*args: str, timeout: int = 120) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args], cwd=BASE, capture_output=True, text=True, timeout=timeout, check=True
    )


def latest_release() -> str:
    """Tag name of the newest full (non-draft, non-pre-release) release."""
    import requests

    r = requests.get(
        LATEST_RELEASE_URL,
        headers={"Accept": "application/vnd.github+json"},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()["tag_name"]


def check() -> dict:
    """Whether a newer full release than the running version exists."""
    tag = latest_release()
    newer = is_newer(tag, current_version())
    return {"version": current_version(), "latest": tag, "behind": int(newer)}


def apply() -> None:
    """Bring the code to the latest release and install missing dependencies."""
    tag = latest_release()
    if not is_newer(tag, current_version()):
        log.info("already at or past %s; nothing to update", tag)
        return
    if mode() == "git":
        _git("fetch", "origin", "tag", tag, "--no-tags", timeout=120)
        _git("merge", "--ff-only", f"refs/tags/{tag}", timeout=120)
    else:
        _apply_zip_overlay(tag)
    install_missing()


def requirement_names(text: str) -> list[str]:
    """Distribution names from requirements.txt text (no extras, pins or comments)."""
    names = []
    for line in text.splitlines():
        line = line.split("#", 1)[0].strip()
        if not line or line.startswith("-"):
            continue
        m = re.match(r"[A-Za-z0-9][A-Za-z0-9._-]*", line)
        if m:
            names.append(m.group(0))
    return names


def missing_requirements(text: str) -> list[str]:
    missing = []
    for name in requirement_names(text):
        try:
            importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            missing.append(name)
    return missing


def install_missing() -> list[str]:
    """pip-install only the requirements that are not installed yet.

    Never reinstalls the whole file: that pulls plain onnxruntime over the
    pinned GPU build (see claude.md) and rewrites DLLs the running app holds.
    Also runs at startup, so an update whose pip step failed heals itself.
    """
    try:
        text = REQUIREMENTS.read_text(encoding="utf-8")
    except OSError:
        return []
    missing = [n for n in missing_requirements(text) if n.lower() != "pytest"]
    if missing:
        log.info("installing missing requirements: %s", missing)
        subprocess.run(
            [
                sys.executable, "-m", "pip", "install", "--quiet", *missing,
                "--extra-index-url", TORCH_INDEX,
            ],
            cwd=BASE, check=True, timeout=1800,
        )
    return missing


def _apply_zip_overlay(tag: str) -> None:
    import requests

    with tempfile.TemporaryDirectory(prefix="neoluna_update_") as tmp:
        tmp = Path(tmp)
        zip_path = tmp / "release.zip"
        with requests.get(tag_zip_url(tag), timeout=300) as r:
            r.raise_for_status()
            zip_path.write_bytes(r.content)
        with zipfile.ZipFile(zip_path) as z:
            z.extractall(tmp)
        root = next(p for p in tmp.iterdir() if p.is_dir())  # ruby-<version>/
        for rel in CODE_PATHS:
            src = root / rel
            dst = BASE / rel
            if not src.exists():
                continue
            if src.is_dir():
                if dst.exists():
                    shutil.rmtree(dst)
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)


def spawn_new_instance() -> None:
    """Launch the updated app; the caller then shuts this instance down."""
    subprocess.Popen(
        [sys.executable, "-m", "app.main"],
        cwd=BASE,
        creationflags=getattr(subprocess, "DETACHED_PROCESS", 0)
        | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
    )
