# Codebase map (onboarding 2026-07-08)

**enigma2-homematic** — Enigma2 (OpenATV 7.6) plugin: Homematic CCU
(smart-home) control on the TV. Python.

## Layout
- `src/HomematicCCU/plugin.py` — entry.
- `src/HomematicCCU/api.py` (~220 LOC) — CCU access (XML-RPC / JSON-RPC to the
  CCU). **Data layer.**
- `src/HomematicCCU/core.py` (~241) — orchestration/state (note: a `core.py`
  module, not yet a `core/` package).
- `src/HomematicCCU/screens.py` (~772) — enigma2 GUI.
- `res/`, `control/`, `build/` (gitignored ipk).

## Conventions
- Enigma2 Py3; timeouts on all CCU calls (main reactor thread).

## Kodi portability: **partially (data + core.py already separated)**
Already has `api.py` + `core.py` split from `screens.py`; 4 files import
enigma2 (screens/plugin + possibly config in core). Port = promote
`api.py`+`core.py` into a `core/` package, strip any enigma2/config imports
from them, add `platform/kodi/`. Closest of the "monolithic" group to the
target shape.
