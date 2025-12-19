# Hypothesis Testing Framework

## Overview

The **Hypothesis Testing Framework** formalizes the experimental learning approach by enabling systematic hypothesis formulation, testing, and analysis. Based on the scientific method applied to skill acquisition, it provides a structured way to test ideas, collect evidence, and make data-driven decisions about technique improvements.

## Scientific Background

### The Hypothesis-Driven Learning Cycle

Research in motor learning and expert performance shows that **deliberate practice** is most effective when it includes:

1. **Specific goals**: Clear, testable hypotheses about what will improve performance
2. **Focused attention**: Concentration on testing the hypothesis during practice
3. **Immediate feedback**: Objective data to evaluate the hypothesis
4. **Iteration**: Refining or rejecting hypotheses based on evidence

This framework implements the complete cycle:

**Formulate → Test → Analyze → Conclude**

### Evidence from Research

- **Ericsson et al. (1993)**: Deliberate practice requires well-defined tasks with appropriate difficulty
- **Zimmerman & Kitsantas (2005)**: Self-regulated learners who set specific process goals outperform those with vague outcome goals
- **Wulf & Lewthwaite (2016)**: External focus (technique) combined with autonomy support (self-generated hypotheses) enhances motor learning

## Features

### 1. Hypothesis Creation
- Interactive prompts for formulating testable hypotheses
- Structured fields: statement, area, corners, success criteria
- Planned session count for systematic testing

### 2. Testing Phase
- Link hypotheses to specific events
- Rate test results (1-5 scale)
- Record observations for each test
- Track progress toward planned session count

### 3. Conclusion Phase
- Review all test results
- Conclude as: confirmed, partially confirmed, or rejected
- Document findings and next steps
- Build institutional knowledge

### 4. Analysis & Visualization
- Status distribution (active, confirmed, rejected)
- Success rate by focus area
- Test result trends over time
- Hypothesis lifecycle timeline
- Testing activity patterns

## Installation

No additional dependencies required. Uses existing tools:
- `frontmatter_utils.py` for event integration
- `matplotlib` and `seaborn` for visualizations

## Usage

### Create a New Hypothesis

```bash
make hypothesis-create
```

**Interactive prompts:**

```
State your hypothesis (be specific and testable):
  Examples:
    - 'Braking 10m earlier in T1 will improve exit speed'
    - 'Higher apex speed in T3 requires earlier throttle application'
    - 'Maintaining patience in traffic reduces incidents by 50%'
Hypothesis: Braking 10m earlier in T1 will reduce lap time by 0.2s

What area does this hypothesis focus on?
  Examples: 'braking', 'throttle control', 'racecraft', 'consistency'
Focus area: braking

Which corners/sections will you test this on? (comma-separated)
  Examples: 'T1, T2' or 'all' or 'T6-T7 complex'
Corners: T1

What would constitute success? (measurable criteria)
  Examples:
    - 'Lap time improvement of 0.2s'
    - 'Exit speed increase of 3 mph'
    - 'Zero incidents over 3 races'
Success criteria: Lap time improvement of 0.2s or better

How many sessions will you test this hypothesis?
  Recommended: 3-5 sessions for reliable data
Number of sessions: 5

Any additional notes? (optional, press Enter to skip)
Notes: Based on telemetry showing late braking compared to reference lap

✅ Hypothesis #1 created

Next steps:
  1. Test it in practice: make hypothesis-test ID=1 EVENT=...
  2. After 5 sessions, conclude: make hypothesis-conclude ID=1
```

### Test a Hypothesis in an Event

```bash
make hypothesis-test ID=1 EVENT=weeks/week02/events/01-2025-12-20-solo.md
```

**Interactive prompts:**

```
📋 Linking hypothesis #1 to event...
Hypothesis: Braking 10m earlier in T1 will reduce lap time by 0.2s

How did the test go?
  1 = Failed completely
  2 = Mostly failed
  3 = Mixed results
  4 = Mostly successful
  5 = Completely successful
Result (1-5): 4

What did you observe during this test?
Observations: Lap time improved by 0.15s. Exit speed felt better but not quite 0.2s improvement yet.

✅ Hypothesis test recorded
   Event: 01-2025-12-20-solo
   Result: 4/5
```

**What happens:**
1. Test result is recorded in the hypothesis database
2. Event frontmatter is updated with hypothesis test data
3. Progress toward planned session count is tracked

### Conclude a Hypothesis

After completing the planned number of test sessions:

```bash
make hypothesis-conclude ID=1
```

**Interactive prompts:**

```
======================================================================
CONCLUDE HYPOTHESIS #1
======================================================================

Hypothesis: Braking 10m earlier in T1 will reduce lap time by 0.2s
Area: braking
Success criteria: Lap time improvement of 0.2s or better

Sessions completed: 5/5

Test results:
  - 01-2025-12-20-solo: 4/5
  - 02-2025-12-21-race: 3/5
  - 03-2025-12-22-solo: 4/5
  - 04-2025-12-23-solo: 5/5
  - 05-2025-12-24-race: 4/5

Average result: 4.00/5

----------------------------------------------------------------------

Based on your testing, what is your conclusion?
  1 = Rejected (hypothesis was incorrect)
  2 = Partially confirmed (needs refinement)
  3 = Confirmed (hypothesis was correct)
Conclusion (1-3): 2

Summarize your findings:
Findings: Braking 10m earlier improved lap time by avg 0.15s, not quite 0.2s. Technique is sound but needs refinement.

What are the next steps based on this conclusion?
  Examples:
    - 'Continue using this technique'
    - 'Refine: brake 5m earlier instead of 10m'
    - 'Abandon this approach, try different line'
Next steps: New hypothesis: brake 12m earlier + trail brake deeper into apex

✅ Hypothesis #1 concluded as: partially_confirmed

Next steps: New hypothesis: brake 12m earlier + trail brake deeper into apex
```

### List All Hypotheses

```bash
# List all hypotheses
make hypothesis-list

# List only active hypotheses
make hypothesis-list STATUS=active

# Other status filters: confirmed, partially_confirmed, rejected
```

**Example output:**

```
======================================================================
HYPOTHESES
======================================================================

🔬 ACTIVE (2)
  #2: Higher apex speed in T3 with earlier throttle application
       Sessions: 2/4 | Area: throttle control
  #3: Maintaining patience in traffic reduces incidents by 50%
       Sessions: 1/3 | Area: racecraft

✅ CONFIRMED (1)
  #4: Consistent brake markers improve lap-to-lap consistency
       Next steps: Continue using this technique

⚠️  PARTIALLY CONFIRMED (1)
  #1: Braking 10m earlier in T1 will reduce lap time by 0.2s
       Next steps: New hypothesis: brake 12m earlier + trail brake deeper into apex
```

### View Hypothesis Details

```bash
make hypothesis-view ID=1
```

**Example output:**

```
======================================================================
HYPOTHESIS #1
======================================================================

📋 Statement: Braking 10m earlier in T1 will reduce lap time by 0.2s
🎯 Area: braking
🏁 Corners: T1
✅ Success criteria: Lap time improvement of 0.2s or better
📊 Status: Partially Confirmed
📅 Created: 2025-12-20
📝 Notes: Based on telemetry showing late braking compared to reference lap

🔬 TEST SESSIONS (5/5)

  Event: 01-2025-12-20-solo
  Result: 4/5
  Observations: Lap time improved by 0.15s. Exit speed felt better.
  Tested: 2025-12-20

  Event: 02-2025-12-21-race
  Result: 3/5
  Observations: Harder to execute in traffic, need more practice.
  Tested: 2025-12-21

  [... more sessions ...]

  Average result: 4.00/5

📝 CONCLUSION
  Findings: Braking 10m earlier improved lap time by avg 0.15s, not quite 0.2s.
  Next steps: New hypothesis: brake 12m earlier + trail brake deeper into apex
  Concluded: 2025-12-24
```

### Visualize Hypothesis Data

```bash
make hypothesis-viz
```

**Generates:**
- `coaching/hypotheses_analysis.png` with 6-panel visualization
- Summary statistics printed to console

**Visualization panels:**
1. **Status Distribution**: Pie chart of active/confirmed/rejected
2. **Success Rate by Area**: Bar chart showing which areas have highest success
3. **Test Result Trends**: Line chart of all test results over time with trend line
4. **Hypothesis Lifecycle Timeline**: Gantt-style chart showing when each hypothesis was active
5. **Average Test Results**: Bar chart of average result per hypothesis
6. **Testing Activity**: Bar chart of testing frequency over time

## Workflow Integration

### Typical Workflow

1. **Before the week**: Create hypotheses for what you want to test
   ```bash
   make hypothesis-create
   ```

2. **During practice/races**: Test hypotheses and record results
   ```bash
   make hypothesis-test ID=1 EVENT=weeks/week02/events/01-2025-12-20-solo.md
   ```

3. **After planned sessions**: Conclude hypotheses and document findings
   ```bash
   make hypothesis-conclude ID=1
   ```

4. **Weekly review**: Visualize all hypothesis data
   ```bash
   make hypothesis-viz
   ```

### Integration with Event Logging

When you test a hypothesis in an event, the event's frontmatter is automatically updated:

```yaml
---
event: 1
week: "02"
date: "2025-12-20"
type: "solo"
hypothesis_test:
  hypothesis_id: 1
  hypothesis: "Braking 10m earlier in T1 will reduce lap time by 0.2s"
  result: 4
  observations: "Lap time improved by 0.15s. Exit speed felt better."
  tested_at: "2025-12-20T14:30:00"
---
```

This creates a bidirectional link:
- Hypothesis database tracks which events tested it
- Event file shows which hypothesis was being tested

## Best Practices

### Formulating Good Hypotheses

**✅ Good hypotheses are:**
- **Specific**: "Brake 10m earlier in T1" not "brake earlier"
- **Testable**: Include measurable success criteria
- **Focused**: One variable at a time
- **Realistic**: Based on data or observation, not guesswork

**❌ Avoid:**
- Vague statements: "Drive faster"
- Multiple variables: "Brake earlier and turn in later and use more throttle"
- Unmeasurable criteria: "Feel more confident"

### Testing Strategy

1. **Plan enough sessions**: 3-5 tests minimum for reliable data
2. **Control variables**: Test in similar conditions when possible
3. **Be objective**: Rate results honestly, not based on desired outcome
4. **Document observations**: Record what you noticed, even if unexpected

### Conclusion Guidelines

- **Confirmed**: Hypothesis met success criteria consistently (avg 4-5/5)
- **Partially Confirmed**: Hypothesis showed promise but needs refinement (avg 3-4/5)
- **Rejected**: Hypothesis did not improve performance (avg 1-2/5)

**Remember**: Rejected hypotheses are valuable! They tell you what doesn't work, saving time in the future.

### Iterative Refinement

The most powerful use of this framework is **iteration**:

1. Test hypothesis → Partially confirmed
2. Refine based on findings → New hypothesis
3. Test refined hypothesis → Confirmed
4. Integrate into permanent technique

**Example progression:**
- H1: "Brake 10m earlier" → Partially confirmed (0.15s improvement)
- H2: "Brake 12m earlier + trail brake" → Confirmed (0.25s improvement)
- Result: Permanent technique change

## Data Storage

### Hypothesis Database

All hypotheses are stored in `coaching/hypotheses.json`:

```json
{
  "hypotheses": [
    {
      "id": 1,
      "hypothesis": "Braking 10m earlier in T1 will reduce lap time by 0.2s",
      "area": "braking",
      "corners": ["T1"],
      "success_criteria": "Lap time improvement of 0.2s or better",
      "planned_sessions": 5,
      "status": "partially_confirmed",
      "created_at": "2025-12-20T10:00:00",
      "tested_events": [
        {
          "event": "01-2025-12-20-solo",
          "result": 4,
          "observations": "Lap time improved by 0.15s.",
          "tested_at": "2025-12-20T14:30:00"
        }
      ],
      "conclusion": {
        "findings": "Improved lap time by avg 0.15s, not quite 0.2s.",
        "next_steps": "New hypothesis: brake 12m earlier + trail brake",
        "concluded_at": "2025-12-24T18:00:00"
      },
      "concluded_at": "2025-12-24T18:00:00"
    }
  ],
  "next_id": 2
}
```

### Event Integration

Each event that tests a hypothesis includes:

```yaml
hypothesis_test:
  hypothesis_id: 1
  hypothesis: "Braking 10m earlier in T1 will reduce lap time by 0.2s"
  result: 4
  observations: "Lap time improved by 0.15s. Exit speed felt better."
  tested_at: "2025-12-20T14:30:00"
```

## Examples

### Example 1: Braking Technique

```
Hypothesis: "Braking 5m later in T6 will increase corner entry speed by 2 mph"
Area: braking
Corners: T6
Success criteria: Entry speed increase of 2+ mph without incidents
Planned sessions: 4

Test 1 (Solo): 3/5 - "Faster entry but ran wide twice"
Test 2 (Solo): 4/5 - "Better line, 1.5 mph faster"
Test 3 (Race): 2/5 - "Too aggressive in traffic, incident"
Test 4 (Solo): 4/5 - "Consistent 1.8 mph gain"

Conclusion: Partially Confirmed
Findings: Works in solo practice (1.5-1.8 mph gain) but too risky in traffic
Next steps: Use in qualifying only, revert to conservative braking in races
```

### Example 2: Racecraft

```
Hypothesis: "Waiting for T3 to overtake instead of T1 reduces incidents by 50%"
Area: racecraft
Corners: T1, T3
Success criteria: Zero incidents over 3 races when following this strategy
Planned sessions: 3

Test 1 (Race): 5/5 - "Waited for T3, clean pass, zero incidents"
Test 2 (Race): 5/5 - "Two clean passes at T3, zero incidents"
Test 3 (Race): 5/5 - "One pass at T3, zero incidents, gained positions"

Conclusion: Confirmed
Findings: T3 is much safer passing zone, 100% success rate
Next steps: Make this the default strategy for this track
```

### Example 3: Consistency

```
Hypothesis: "Using fixed brake markers improves lap-to-lap consistency by 0.1s"
Area: consistency
Corners: all
Success criteria: Lap time standard deviation < 0.15s over 10-lap stint
Planned sessions: 3

Test 1 (Solo): 4/5 - "Std dev 0.18s, improvement but not quite there"
Test 2 (Solo): 5/5 - "Std dev 0.12s, very consistent"
Test 3 (Race): 5/5 - "Std dev 0.14s even in traffic"

Conclusion: Confirmed
Findings: Fixed markers dramatically improve consistency
Next steps: Continue using, document markers for all corners
```

## Troubleshooting

### "Hypothesis database not found"

The database is created automatically on first use. If you see this error:
```bash
mkdir -p coaching
echo '{"hypotheses": [], "next_id": 1}' > coaching/hypotheses.json
```

### "Event file not found"

Make sure the event file exists before linking a hypothesis:
```bash
ls weeks/week02/events/01-2025-12-20-solo.md
```

### Visualization shows no data

This is normal if:
- No hypotheses created yet → `make hypothesis-create`
- No test sessions recorded yet → `make hypothesis-test ID=1 EVENT=...`

## Advanced Usage

### Batch Analysis

To analyze all hypotheses for a specific area:
```bash
# List all braking hypotheses
make hypothesis-list | grep "braking"

# Or filter in the database directly
cat coaching/hypotheses.json | jq '.hypotheses[] | select(.area=="braking")'
```

### Export for Analysis

The JSON database can be analyzed with external tools:
```python
import json
import pandas as pd

with open('coaching/hypotheses.json') as f:
    data = json.load(f)

# Convert to DataFrame for analysis
df = pd.DataFrame(data['hypotheses'])
print(df[['id', 'hypothesis', 'status', 'area']])
```

## References

- Ericsson, K. A., Krampe, R. T., & Tesch-Römer, C. (1993). The role of deliberate practice in the acquisition of expert performance. *Psychological Review*, 100(3), 363-406.
- Zimmerman, B. J., & Kitsantas, A. (2005). The hidden dimension of personal competence: Self-regulated learning and practice. In A. J. Elliot & C. S. Dweck (Eds.), *Handbook of competence and motivation* (pp. 509-526). Guilford Press.
- Wulf, G., & Lewthwaite, R. (2016). Optimizing performance through intrinsic motivation and attention for learning: The OPTIMAL theory of motor learning. *Psychonomic Bulletin & Review*, 23(5), 1382-1414.

## See Also

- `README_MENTAL_REHEARSAL.md` - Mental practice protocol
- `README_FRONTMATTER_UTILS.md` - Event data management
- Issue #28 on GitHub for development roadmap

---

**Remember**: The goal is not to confirm every hypothesis, but to learn systematically. Rejected hypotheses are just as valuable as confirmed ones - they tell you what doesn't work, saving time and preventing bad habits.

Happy experimenting! 🔬🏎️
