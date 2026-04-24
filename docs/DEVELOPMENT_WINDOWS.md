# Windows Development Setup

This note keeps Windows 11 + VS Code development predictable after switching
from macOS.

## Current baseline

Verified on 2026-04-24 on Windows 11:

- Git works.
- Python 3.11 works.
- Python 3.13 is also installed.
- A local `.venv` can be created and used successfully.
- `python -m unittest discover -s tests` passes from Windows when `PYTHONPATH`
  is set to `src`.
- Node.js LTS is installed for Companion extension syntax checks.

## Recommended workflow

Use one project-local virtual environment and let VS Code use that interpreter.
That avoids the common Windows mismatch where:

- `python` points to one version
- `py` points to another

Create and install once:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e .
```

If you prefer Python 3.11, the same pattern works with `py -3.11`.

## Run tests on Windows

```powershell
$env:PYTHONPATH='src'
.\.venv\Scripts\python.exe -m unittest discover -s tests
```

## Python compile check on Windows

PowerShell does not expand `*.py` for `python -m py_compile` the same way a
POSIX shell does, so use:

```powershell
Get-ChildItem src\linkvault\*.py, tests\*.py |
  ForEach-Object { .\.venv\Scripts\python.exe -m py_compile $_.FullName }
```

## Companion extension syntax check

After installing Node.js, open a new terminal so `node` and `npm` are on PATH.

```powershell
node --check extensions\linkvault-companion\shared.js
node --check extensions\linkvault-companion\options.js
node --check extensions\linkvault-companion\popup.js
```

## VS Code

The repo includes tasks for:

- Python compile check
- unit tests
- Companion extension JS syntax check

Open:

- `Terminal -> Run Task`

Then choose one of the `LinkVault:` tasks.

## Notes

- `pip install -e .` on Windows may install `linkvault.exe` into the user
  scripts directory if global site-packages are not writable.
- If the command is not found directly, calling the venv Python remains the
  most reliable path during development.
- If `node` still is not found after installation, restart VS Code or open a
  fresh terminal window.
