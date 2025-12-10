# Tooling Cheatsheet

Home base for the automation helpers that keep the weekly ritual breezy.

## Week Generator – `create_week.py`

Create a fresh weekly note pre-filled with metadata and placeholders.

```
uv run python tools/create_week.py --week 1
```

Optional flags:

- `--start YYYY-MM-DD` – opening date for the official schedule window.
- `--end YYYY-MM-DD` – closing date for the official schedule window.
- `--season` / `--series` – override the default labels if they ever change.
- `--force` – overwrite an existing week file (use when re-rolling a draft).
- `--track` – override the auto-track if you want a custom label.

Generated files land in `weeks/` using the pattern `weekXX-track-slug.md`. Edit the intent line first, then log prep sessions and races as the week unfolds.

> `tracks.yaml` powers the defaults. If PyYAML is not installed you’ll be prompted to run `uv add pyyaml`.

## Track Schedule Data – `tracks.yaml`

- Holds per-week metadata (dates, track/layout, race length, special event info, conditions).
- The generator auto-fills YAML front matter using this table, then computes a default end date (start + 6 days).
- Update this file if iRacing shuffles the schedule; rerun the generator with `--force` to refresh an existing file.

## Logging Reminders

- **Prep sessions**: one row per session using the table under “Preparation Sessions”.
- **Races**: append a row under “Official Races” with all columns filled where possible. Leave cells blank rather than guessing.
- **Reflection**: three short bullets (track craft, brake bias, mindset) plus a “Next Week Intent” bridge sentence.

## Extensibility Hooks

- Scripts can safely parse the YAML front matter block plus the markdown tables.
- Add future helpers (stats, exports, telemetry linking) in this folder; document usage alongside the tool.
