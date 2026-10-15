# Upgrade your existing SignalDesk workspace

This maintenance release corrects the version label, tightens claim-mapping instructions, and updates documentation. Delivery remains simulated. Keep your existing project: it contains your recorded decisions.

1. Download and unzip `SignalDesk_v0.3.1.zip`. It creates a separate `signaldesk-v0.3.1` release folder. Do not replace your existing project folder with it.
2. In the PyCharm terminal running your existing server, press **Ctrl+C**. Stay in your existing project directory with its `.venv` activated.
3. Type `python ` (including the space), drag **upgrade_signaldesk.py from the NEW release folder** into the terminal to insert its full path, and press Enter. If dragging is unavailable, type `python "/full/path/to/signaldesk-v0.3.1/upgrade_signaldesk.py"` using the actual path.
4. After it reports that your database and environment were preserved, run:

```bash
python -m pip install -e '.[dev]'
```

Your existing API key and model configuration are preserved. There is no need to run configuration again for this update. Installing the update makes no API call.

5. Restart the app:

```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

6. Refresh http://127.0.0.1:8000. If the old interface persists, use **Command+Shift+R**. Verify your prior Do Not Contact decision remains recorded.
7. Confirm the footer reads **Prototype v0.3.1**, your saved draft remains present, and Do Not Contact remains active. These checks need no paid research run.

If you later test research, use a separate lead or copy your edited draft first: rerunning research replaces the current draft and revokes approval. Review source content and publication dates yourself. Delivery remains simulated.

## Preservation and recovery

The updater copies only release source files. It leaves `.env`, `.venv`, and your database in place, and creates `backups/<timestamp>/` with previous source and a consistent backup of the default `signaldesk.db`. This backup contains your local records; keep it private. Custom database locations and PostgreSQL are not backed up by the updater.

If the updater reports an interrupted copy, do not start the app. Restore the backed-up source before continuing. For a fresh installation, follow README.md instead of running the upgrader.
