# SchoolFin (PyQt6 + PyInstaller)

## Run (dev)
```bash
python -m schoolfin.app
```

## Default users
- admin / admin123
- financial / financial123

## Login
- Choose a profile first: Administrator or Financial.
- The menus and available pages adapt to the selected role after login.

## Build
```bash
pyinstaller --clean --noconfirm build.spec
```

## Spell check (French)
Uses `codespell` (French only). Run:
```bash
python -m codespell . --config=codespell.cfg
```

The SQLite database is stored in a persistent per-user application-data location by default.

## Database location
- Default (Windows): `%LOCALAPPDATA%\SchoolFin\schoolfin.sqlite`
- Optional override: set environment variable `SCHOOLFIN_DB_PATH` to an absolute path.

On first run with the new behavior, the app attempts a one-time migration by copying an existing legacy database from old locations (project root / exe folder) if the new DB file does not already exist.

