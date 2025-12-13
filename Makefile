# iRacing Season Logbook - Makefile
# =================================
# Workflow shortcuts for the AI dojo 🥋

.PHONY: help update-week add-event viz-event viz-week viz-telemetry compare-laps clean

# Default target
help:
	@echo "🏎️  iRacing Season Logbook Commands"
	@echo "===================================="
	@echo ""
	@echo "  make add-event WEEK=01 FILE=...   Add new event (copies CSV, creates page, updates week)"
	@echo "  make update-week WEEK=01          Regenerate week visualizations + summary"
	@echo "  make compare-laps WEEK=01         Compare best laps (needs telemetry CSVs)"
	@echo ""
	@echo "  make viz-event FILE=...           Visualize a single event CSV (lap times)"
	@echo "  make viz-week WEEK=01             Generate week progress visualization only"
	@echo "  make viz-telemetry FILE=...       Analyze single-lap telemetry (speed, pedals, G-forces)"
	@echo ""
	@echo "Workflow:"
	@echo "  1. Export CSV from Garage61"
	@echo "  2. make add-event WEEK=01 FILE=~/Downloads/export.csv"
	@echo "  3. Edit debrief: weeks/week01/events/XX-date-type.md"
	@echo ""

# Add a new event to the week structure
# Usage: make add-event WEEK=01 FILE=path/to/export.csv
add-event:
	@if [ -z "$(WEEK)" ]; then echo "❌ Usage: make add-event WEEK=01 FILE=path/to/export.csv"; exit 1; fi
	@if [ -z "$(FILE)" ]; then echo "❌ Usage: make add-event WEEK=01 FILE=path/to/export.csv"; exit 1; fi
	uv run python tools/add_event.py $(WEEK) "$(FILE)"

# Compare best laps from telemetry exports
# Usage: make compare-laps WEEK=01
compare-laps:
	@if [ -z "$(WEEK)" ]; then echo "❌ Usage: make compare-laps WEEK=01"; exit 1; fi
	@echo "🔬 Comparing best laps for week$(WEEK)..."
	uv run python tools/compare_laps.py weeks/week$(WEEK)/data/

# Update week visualizations from CSVs
# Usage: make update-week WEEK=01
update-week:
	@if [ -z "$(WEEK)" ]; then echo "❌ Usage: make update-week WEEK=01"; exit 1; fi
	@echo "🔄 Updating week$(WEEK)..."
	uv run python tools/update_week.py weeks/week$(WEEK)/data/ weeks/week$(WEEK)/README.md
	@echo ""
	@echo "✅ Done! Check weeks/week$(WEEK)/"

# Visualize a single event
# Usage: make viz-event FILE=results/week01/event.csv
viz-event:
	@if [ -z "$(FILE)" ]; then echo "❌ Usage: make viz-event FILE=path/to/event.csv"; exit 1; fi
	@echo "📊 Visualizing $(FILE)..."
	uv run python tools/visualize_event.py "$(FILE)"

# Generate week visualization only (no markdown update)
# Usage: make viz-week WEEK=01
viz-week:
	@if [ -z "$(WEEK)" ]; then echo "❌ Usage: make viz-week WEEK=01"; exit 1; fi
	@echo "📊 Generating week$(WEEK) visualization..."
	uv run python tools/visualize_week.py weeks/week$(WEEK)/data/ --output weeks/week$(WEEK)/images/week-progress.png

# Visualize single-lap telemetry (from Garage61 export)
# Usage: make viz-telemetry FILE=path/to/telemetry.csv
viz-telemetry:
	@if [ -z "$(FILE)" ]; then echo "❌ Usage: make viz-telemetry FILE=path/to/telemetry.csv"; exit 1; fi
	@echo "🔬 Analyzing telemetry $(FILE)..."
	uv run python tools/visualize_telemetry.py "$(FILE)"

# Generate track map with sectors from telemetry
# Usage: make track-map FILE=path/to/telemetry.csv
# Optional: make track-map FILE=... SECTORS="0.55 0.77"
track-map:
	@if [ -z "$(FILE)" ]; then echo "❌ Usage: make track-map FILE=path/to/telemetry.csv"; exit 1; fi
	@echo "🗺️  Generating track map from $(FILE)..."
	uv run python tools/generate_track_map.py "$(FILE)" $(if $(SECTORS),--sectors $(SECTORS),)

# Clean generated images (careful!)
clean:
	@echo "🧹 This would remove generated images. Are you sure? (Ctrl+C to cancel)"
	@read -p "Press Enter to continue..."
	find images/ -name "*.png" -type f -delete
	@echo "✅ Cleaned"

