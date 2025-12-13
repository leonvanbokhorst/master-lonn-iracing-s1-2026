# iRacing Season Logbook - Makefile
# =================================
# Workflow shortcuts for the AI dojo 🥋

.PHONY: help update-week viz-event viz-week clean

# Default target
help:
	@echo "🏎️  iRacing Season Logbook Commands"
	@echo "===================================="
	@echo ""
	@echo "  make update-week WEEK=01     Update week file from CSVs (regenerates viz + summary)"
	@echo "  make viz-event FILE=...     Visualize a single event CSV"
	@echo "  make viz-week WEEK=01       Generate week progress visualization only"
	@echo ""
	@echo "Examples:"
	@echo "  make update-week WEEK=01"
	@echo "  make viz-event FILE=results/week01/my-event.csv"
	@echo ""

# Update week file from all CSVs in results/weekXX/
# Usage: make update-week WEEK=01
update-week:
	@if [ -z "$(WEEK)" ]; then echo "❌ Usage: make update-week WEEK=01"; exit 1; fi
	@echo "🔄 Updating week$(WEEK)..."
	@WEEK_FILE=$$(ls weeks/week$(WEEK)-*.md 2>/dev/null | head -1); \
	if [ -z "$$WEEK_FILE" ]; then echo "❌ No week file found for week $(WEEK)"; exit 1; fi; \
	uv run python tools/update_week.py results/week$(WEEK)/ "$$WEEK_FILE"
	@echo ""
	@echo "✅ Done! Check weeks/week$(WEEK)-*.md and images/week$(WEEK)/"

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
	uv run python tools/visualize_week.py results/week$(WEEK)/ --output images/week$(WEEK)/week-progress.png

# Clean generated images (careful!)
clean:
	@echo "🧹 This would remove generated images. Are you sure? (Ctrl+C to cancel)"
	@read -p "Press Enter to continue..."
	find images/ -name "*.png" -type f -delete
	@echo "✅ Cleaned"

