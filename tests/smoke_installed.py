"""Verify a built, installed SignalDesk wheel serves its bundled UI without API calls."""
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
from urllib.request import urlopen

with tempfile.TemporaryDirectory() as directory:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    env = {**os.environ, "DATABASE_URL": f"sqlite:///{Path(directory) / 'smoke.db'}"}
    cmd = [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(port)]
    proc = subprocess.Popen(cmd, cwd=directory, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    try:
        for i in range(60):
            if proc.poll() is not None:
                raise RuntimeError("Installed application exited during startup: " + proc.stderr.read().decode(errors="replace")[-4000:])
            try:
                with urlopen(f"http://127.0.0.1:{port}/", timeout=2) as response:
                    assert response.status == 200
                break
            except Exception:
                time.sleep(0.25)
        else:
            raise RuntimeError("Installed application did not start")
        for route, expected in [
            ("/acquisition", b"<html"),
            ("/acquisition/ui.css", b""),
            ("/acquisition/ui.js", b""),
            ("/", b"<html"),
        ]:
            with urlopen(f"http://127.0.0.1:{port}{route}", timeout=5) as response:
                body = response.read()
                assert response.status == 200 and body, f"Empty or failed: {route}"
                assert expected.lower() in body.lower(), f"Unexpected content: {route}"
        print("Installed wheel serves SDR and Acquisition Intelligence UI: PASS")
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
