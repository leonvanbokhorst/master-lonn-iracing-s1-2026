# iRacing Season Logbook - Makefile
# =================================
# Workflow shortcuts for the AI dojo 🥋

.PHONY: help update-week add-event viz-event viz-week viz-telemetry compare-laps official-report rehearsal-pre rehearsal-post rehearsal-view rehearsal-viz srs-add srs-review srs-list srs-stats srs-viz clean

# Default target
help:
	@echo "🏎️  iRacing Season Logbook Commands"
	@echo "===================================="
	@echo ""
	@echo "  make add-event WEEK=01 FILE=... [TELEMETRY=...]   Add new event (processes all 4 visualizations)"
	@echo "  make update-week WEEK=01                          Regenerate week visualizations + summary"
	@echo "  make compare-laps WEEK=01                         Compare best laps (needs telemetry CSVs)"
	@echo "  make official-report WEEK=01 EVENT=12 JSON=...    Write official race report + summary"
	@echo ""
	@echo "  make rehearsal-pre EVENT=...                      Record pre-session mental rehearsal"
	@echo "  make rehearsal-post EVENT=...                     Record post-session mental replay"
	@echo "  make rehearsal-view EVENT=...                     View mental rehearsal data"
	@echo "  make rehearsal-viz WEEK=01                        Visualize rehearsal impact"
	@echo ""
	@echo "  make srs-add                                      Add knowledge card"
	@echo "  make srs-review                                   Review due cards"
	@echo "  make srs-list [TRACK=...] [DUE=yes]              List knowledge cards"
	@echo "  make srs-stats                                    Show SRS statistics"
	@echo "  make srs-viz                                      Visualize SRS data"
	@echo ""
	@echo "  make viz-event FILE=...           Visualize a single event CSV (lap times)"
	@echo "  make viz-week WEEK=01             Generate week progress visualization only"
	@echo "  make viz-telemetry FILE=...       Analyze single-lap telemetry (speed, pedals, G-forces)"
	@echo ""
	@echo "Workflow:"
	@echo "  1. Export CSV from Garage61 (Session + Fastest Lap Telemetry)"
	@echo "  2. make add-event WEEK=01 FILE=~/Downloads/event.csv TELEMETRY=~/Downloads/lap.csv"
	@echo "  3. Edit debrief: weeks/week01/events/XX-date-type.md"
	@echo ""

# Add a new event to the week structure
# Usage: make add-event WEEK=01 FILE=path/to/export.csv [TELEMETRY=path/to/lap.csv]
add-event:
	@if [ -z "$(WEEK)" ]; then echo "❌ Usage: make add-event WEEK=01 FILE=path/to/export.csv [TELEMETRY=path/to/lap.csv]"; exit 1; fi
	@if [ -z "$(FILE)" ]; then echo "❌ Usage: make add-event WEEK=01 FILE=path/to/export.csv [TELEMETRY=path/to/lap.csv]"; exit 1; fi
	uv run python tools/add_event.py $(WEEK) "$(FILE)" $(if $(TELEMETRY),--telemetry "$(TELEMETRY)",)
	@echo "📊 Updating lap comparison..."
	uv run python tools/compare_laps.py weeks/week$(WEEK)/data/

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

# Generate official race report from eventresult JSON
# Usage: make official-report WEEK=01 EVENT=12 JSON=path/to/eventresult.json [EVENT_FILE=...]
official-report:
	@if [ -z "$(WEEK)" ]; then echo "❌ Usage: make official-report WEEK=01 EVENT=12 JSON=path/to/eventresult.json"; exit 1; fi
	@if [ -z "$(EVENT)" ]; then echo "❌ Usage: make official-report WEEK=01 EVENT=12 JSON=path/to/eventresult.json"; exit 1; fi
	@if [ -z "$(JSON)" ]; then echo "❌ Usage: make official-report WEEK=01 EVENT=12 JSON=path/to/eventresult.json"; exit 1; fi
	@echo "📝 Generating official race report for week $(WEEK) event $(EVENT)..."
	uv run python tools/generate_official_report.py --week $(WEEK) --event $(EVENT) --json "$(JSON)" $(if $(EVENT_FILE),--event-file "$(EVENT_FILE)",)

# Generate track map with sectors from telemetry
# Usage: make track-map FILE=path/to/telemetry.csv
# Optional: make track-map FILE=... SECTORS="0.55 0.77"
track-map:
	@if [ -z "$(FILE)" ]; then echo "❌ Usage: make track-map FILE=path/to/telemetry.csv"; exit 1; fi
	@echo "🗺️  Generating track map from $(FILE)..."
	uv run python tools/generate_track_map.py "$(FILE)" $(if $(SECTORS),--sectors $(SECTORS),)

# Mental Rehearsal Protocol
# Usage: make rehearsal-pre EVENT=weeks/week02/events/01-2025-12-20-solo.md
rehearsal-pre:
	@if [ -z "$(EVENT)" ]; then echo "❌ Usage: make rehearsal-pre EVENT=weeks/weekXX/events/XX-date-type.md"; exit 1; fi
	@echo "🧠 Recording pre-session mental rehearsal..."
	uv run python tools/mental_rehearsal.py pre "$(EVENT)"

# Record post-session mental replay
# Usage: make rehearsal-post EVENT=weeks/week02/events/01-2025-12-20-solo.md
rehearsal-post:
	@if [ -z "$(EVENT)" ]; then echo "❌ Usage: make rehearsal-post EVENT=weeks/weekXX/events/XX-date-type.md"; exit 1; fi
	@echo "🧠 Recording post-session mental replay..."
	uv run python tools/mental_rehearsal.py post "$(EVENT)"

# View mental rehearsal data for an event
# Usage: make rehearsal-view EVENT=weeks/week02/events/01-2025-12-20-solo.md
rehearsal-view:
	@if [ -z "$(EVENT)" ]; then echo "❌ Usage: make rehearsal-view EVENT=weeks/weekXX/events/XX-date-type.md"; exit 1; fi
	uv run python tools/mental_rehearsal.py view "$(EVENT)"

# Visualize mental rehearsal impact for a week
# Usage: make rehearsal-viz WEEK=02
rehearsal-viz:
	@if [ -z "$(WEEK)" ]; then echo "❌ Usage: make rehearsal-viz WEEK=02"; exit 1; fi
	@echo "📊 Visualizing mental rehearsal impact for week$(WEEK)..."
	uv run python tools/visualize_rehearsal_impact.py weeks/week$(WEEK)

# Clean generated images (careful!)
clean:
	@echo "🧹 This would remove generated images. Are you sure? (Ctrl+C to cancel)"
	@read -p "Press Enter to continue..."
	find images/ -name "*.png" -type f -delete
	@echo "✅ Cleaned"


# Spaced Repetition System (SRS)
# Usage: make srs-add
srs-add:
	@echo "📇 Adding new knowledge card..."
	uv run python tools/spaced_repetition.py add

# Review due cards
# Usage: make srs-review
srs-review:
	@echo "🧠 Starting review session..."
	uv run python tools/spaced_repetition.py review

# List knowledge cards
# Usage: make srs-list [TRACK="Summit Point"] [DUE=yes]
srs-list:
	@if [ -n "$(TRACK)" ] && [ -n "$(DUE)" ]; then \
		uv run python tools/spaced_repetition.py list --track "$(TRACK)" --due; \
	elif [ -n "$(TRACK)" ]; then \
		uv run python tools/spaced_repetition.py list --track "$(TRACK)"; \
	elif [ -n "$(DUE)" ]; then \
		uv run python tools/spaced_repetition.py list --due; \
	else \
		uv run python tools/spaced_repetition.py list; \
	fi

# Show SRS statistics
# Usage: make srs-stats
srs-stats:
	uv run python tools/spaced_repetition.py stats

# Visualize SRS data
# Usage: make srs-viz
srs-viz:
	@echo "📊 Visualizing spaced repetition data..."
	uv run python tools/visualize_srs.py
