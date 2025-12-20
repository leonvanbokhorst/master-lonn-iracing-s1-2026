# Data Structure Analysis: Current System

## Current Frontmatter Structure

### Observed Pattern

**Minimal Frontmatter (Current Standard):**
```yaml
---
event: 12
week: "01"
date: "2025-12-16"
type: "race"
---
```

**Optional Fields (Sometimes Present):**
```yaml
focus: "baseline exploration"  # Only in some early events
```

### Key Findings

1. **Frontmatter is WRITE-ONLY**: The current tools (`add_event.py`, `update_week.py`, `visualize_*.py`) do NOT parse the YAML frontmatter at all. They only:
   - Write frontmatter when creating new event files
   - Parse the markdown tables in the body for stats extraction
   - Read CSV files directly for data processing

2. **No YAML Dependencies**: The codebase has zero YAML parsing. The `parse_event_stats()` function in `add_event.py` uses regex to extract stats from markdown tables, not from frontmatter.

3. **Template-Based Generation**: Event files are created from a template with simple `{{variable}}` substitution. The frontmatter is static text in the template.

4. **Data Flow**:
   ```
   Garage61 CSV → add_event.py → Event Markdown + Processed CSV
                                ↓
                          Visualizations read from CSV
                                ↓
                          update_week.py aggregates CSVs
   ```

5. **Frontmatter Purpose**: Currently serves as metadata for human readers and potential future tooling, but is NOT used by any current automation.

## Integration Points

### Safe Integration Points (Zero Risk)

1. **Frontmatter Extension**: Since no tools parse frontmatter, adding new fields is completely safe.

2. **New Standalone Files**: Creating new files like `coaching/hypotheses.yaml` or `coaching/spaced-repetition.yaml` has zero impact on existing workflows.

3. **New Python Scripts**: Adding new tools in `tools/` directory doesn't affect existing tools.

4. **Makefile Extension**: Adding new targets doesn't break existing commands.

### Potential Conflict Points

1. **Template Modification**: If we modify `tools/templates/event-page.md`, it only affects NEW events. Existing events remain unchanged.

2. **Config.toml Extension**: Adding new sections is safe as long as we don't modify existing sections.

3. **Event File Manual Editing**: If new tools modify existing event files (adding frontmatter fields), we need to ensure:
   - Proper YAML parsing/writing
   - Preservation of existing content
   - Handling of files without the new fields (backward compatibility)

## Current Data Dependencies

### What Existing Tools Depend On

1. **CSV Files** (`weeks/weekXX/data/processed/*.csv`):
   - Required columns: `LapTime`, `LapNumber`, potentially others
   - Used by ALL visualization tools
   - **Critical**: Do not modify CSV structure

2. **Markdown Table Format** (in event body):
   - Used by `parse_event_stats()` to extract metrics
   - Format: `| **Label** | value |`
   - **Important**: Keep this format intact

3. **File Naming Convention**:
   - Events: `XX-YYYY-MM-DD-type.md`
   - CSVs: `XX-YYYY-MM-DD-type.csv`
   - Images: `event-XX-*.png`
   - **Critical**: Maintain naming conventions

4. **Directory Structure**:
   ```
   weeks/weekXX/
   ├── README.md
   ├── events/*.md
   ├── data/processed/*.csv
   └── images/*.png
   ```
   - **Critical**: Do not change directory structure

## Risk Assessment

### Zero-Risk Changes
- Adding new frontmatter fields to existing events
- Creating new YAML files in `coaching/`
- Adding new Python tools
- Adding new Makefile targets
- Adding new sections to `config.toml`

### Low-Risk Changes
- Modifying event template (only affects new events)
- Adding new sections to event body (below existing sections)

### Medium-Risk Changes
- Modifying existing tools to read frontmatter (requires careful YAML parsing)
- Bulk-updating existing event files (requires robust file handling)

### High-Risk Changes (AVOID)
- Changing CSV column names or structure
- Changing markdown table format
- Changing file naming conventions
- Changing directory structure
