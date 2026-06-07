# Presence of this file at the repo root puts the root on sys.path,
# so `import agentlens` works in tests without installing the package.

# Also load a local `.env` (if present) so the opt-in live agent tests can read
# ANTHROPIC_API_KEY without exporting it in the shell. Stdlib-only — we don't
# pull in python-dotenv, keeping the package's zero-dependency promise intact.
# A real shell env var always wins over the file.
from pathlib import Path


def _load_dotenv() -> None:
    import os

    env_path = Path(__file__).parent / ".env"
    if not env_path.exists():
        return
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)  # don't override a real env var


_load_dotenv()
