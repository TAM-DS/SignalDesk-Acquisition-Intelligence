"""Run locally; API key input is hidden and never placed in shell history."""
from getpass import getpass
from pathlib import Path
import os
import sys
from dotenv import dotenv_values, set_key


def main():
    if not sys.stdin.isatty():
        raise SystemExit('Run this in an interactive terminal so the API key is not echoed.')
    path = Path(__file__).resolve().parent / '.env'
    current = dotenv_values(path) if path.exists() else {}
    print('Configure SignalDesk locally. Do not share the key in chat or screenshots.')
    print('Live API and web-search usage is billed to your OpenAI API account.')
    key = getpass('OpenAI API key (hidden; Enter keeps an existing key): ').strip()
    if not key and not current.get('OPENAI_API_KEY'):
        raise SystemExit('No key supplied. Nothing changed.')
    if key and (any(c.isspace() for c in key) or len(key) < 15):
        raise SystemExit('The key format looks incomplete. Nothing changed.')
    default = current.get('OPENAI_MODEL') or 'gpt-5-mini'
    model = input(f'Model [{default}]: ').strip() or default
    if not model or any(c.isspace() for c in model):
        raise SystemExit('Use one model identifier without whitespace.')
    if not path.exists():
        descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        os.close(descriptor)
    if key:
        set_key(str(path), 'OPENAI_API_KEY', key)
    set_key(str(path), 'OPENAI_MODEL', model)
    os.chmod(path, 0o600)
    print('Saved locally. Restart SignalDesk to load the configuration. No API call was made.')


if __name__ == '__main__':
    main()
