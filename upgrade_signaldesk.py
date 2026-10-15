"""Run this release's script FROM the existing SignalDesk project directory."""
from datetime import datetime, timezone
from pathlib import Path
import shutil
import socket
import sqlite3


FILES = ['pyproject.toml', '.gitignore', 'requirements-tested.txt', 'README.md',
         'configure_openai.py', 'upgrade_signaldesk.py',
         'app/__init__.py', 'app/main.py', 'app/fixtures.py', 'app/live.py',
         'app/static/index.html', 'app/static/style.css', 'app/static/app.js',
         'tests/test_authority.py', 'tests/test_live.py',
         'docs/PRODUCT_BRIEF.md', 'docs/INTERVIEW_WALKTHROUGH.md',
         'docs/VALIDATION.md', 'docs/UPGRADE.md', 'docs/REPOSITORY_CHECKLIST.md', 'docs/ARCHITECTURE.md']


def main():
    release = Path(__file__).resolve().parent
    target = Path.cwd().resolve()
    if target == release:
        raise SystemExit('Run from your EXISTING project folder, using the full path to this new release script.')
    if not (target / 'app/main.py').is_file() or not (target / 'pyproject.toml').is_file():
        raise SystemExit('Current directory is not a SignalDesk project. Change to your existing project first.')
    if 'name = "signaldesk"' not in (target / 'pyproject.toml').read_text():
        raise SystemExit('Project identity does not match SignalDesk. No files changed.')
    if not all((release / name).is_file() for name in FILES):
        raise SystemExit('Release is incomplete. No files changed.')
    with socket.socket() as probe:
        probe.settimeout(0.3)
        if probe.connect_ex(('127.0.0.1', 8000)) == 0:
            raise SystemExit('Stop the local server with Ctrl+C before upgrading. Port 8000 is still in use.')
    backup = target / 'backups' / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    backup.mkdir(parents=True)
    database = target / 'signaldesk.db'
    if database.exists():
        with sqlite3.connect(database) as src, sqlite3.connect(backup / 'signaldesk.db') as dst:
            src.backup(dst)
    for name in FILES:
        old = target / name
        if old.is_file():
            saved = backup / name
            saved.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(old, saved)
    try:
        for name in FILES:
            dest = target / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(release / name, dest)
    except OSError:
        raise SystemExit(f'Upgrade interrupted. Original files are in {backup}. Restore them before starting.')
    print(f'Updated source in {target}')
    print(f'Previous source and default SQLite backup: {backup}')
    print('Existing database, .env, and virtual environment were preserved.')
    print("Next: python -m pip install -e '.[dev]'")
    print('Existing OpenAI configuration is preserved. If needed, use python configure_openai.py and select gpt-5-mini.')
    print('Start: python -m uvicorn app.main:app --host 127.0.0.1 --port 8000')


if __name__ == '__main__':
    main()
