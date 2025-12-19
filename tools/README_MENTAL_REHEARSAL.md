# Mental Rehearsal Protocol

**Status:** ✅ Implemented  
**Issue:** [#27](https://github.com/leonvanbokhorst/master-lonn-iracing-s1-2026/issues/27)  
**Author:** Manus AI  
**Date:** 2025-12-19

---

## Overview

The Mental Rehearsal Protocol enables systematic tracking of pre-session mental rehearsal (visualization) and post-session mental replay (corrections rehearsal). This feature is grounded in **motor imagery research** showing that mental practice enhances skill acquisition and performance when combined with physical practice.

## Scientific Background

Mental rehearsal activates many of the same neural pathways as physical practice, leading to:

- **Improved motor learning** through neural pathway reinforcement
- **Enhanced confidence** through mental preparation
- **Better error correction** through mental replay of proper technique
- **Increased consistency** through mental consolidation of skills

Research shows that combining mental and physical practice is more effective than physical practice alone.

---

## Features

### 1. Pre-Session Mental Rehearsal

Track visualization practice **before** a session:

- **Duration**: How long you spent visualizing
- **Focus area**: What you concentrated on (e.g., "T1-T3 transitions")
- **Corners rehearsed**: Specific corners you mentally practiced
- **Confidence rating**: How confident you feel (1-5 scale)
- **Notes**: Additional observations

### 2. Post-Session Mental Replay

Track mental practice **after** a session:

- **Duration**: How long you spent on mental replay
- **Corrections rehearsed**: What mistakes you mentally corrected
- **Corners replayed**: Specific corners you practiced mentally
- **Clarity rating**: How vivid your mental imagery was (1-5 scale)
- **Notes**: Additional observations

### 3. Impact Visualization

Analyze the correlation between mental rehearsal and performance:

- Performance comparison: rehearsal vs. no rehearsal
- Confidence ratings vs. actual performance
- Rehearsal frequency over time
- Duration distribution
- Correlation analysis

---

## Usage

### Command-Line Interface

#### Record Pre-Session Rehearsal

```bash
python tools/mental_rehearsal.py pre weeks/week02/events/01-2025-12-20-solo.md
```

**Interactive prompts:**
```
PRE-SESSION MENTAL REHEARSAL
======================================================================

Mental rehearsal (visualization) before a session helps activate
the neural pathways you'll use during actual practice.

How long did you spend on mental rehearsal? (minutes)
  Recommended: 3-5 minutes
Duration (minutes): 5

What did you focus on during visualization?
  Examples:
    - 'T1-T3 transitions and braking points'
    - 'Smooth throttle application in T6-T7'
    - 'Maintaining patience in traffic'
Focus area: T1-T3 transitions and braking points

Which corners did you mentally rehearse? (comma-separated)
  Examples: 'T1, T3, T6' or 'all' or 'none'
Corners: T1, T2, T3

How confident do you feel going into this session?
  1 = Very uncertain, 5 = Very confident
Confidence (1-5): 4

Any additional notes? (optional, press Enter to skip)
Notes: Focused on smooth steering inputs

✓ Pre-session rehearsal recorded
✅ Mental rehearsal data added to 01-2025-12-20-solo.md
```

#### Record Post-Session Replay

```bash
python tools/mental_rehearsal.py post weeks/week02/events/01-2025-12-20-solo.md
```

**Interactive prompts:**
```
POST-SESSION MENTAL REPLAY
======================================================================

Mental replay after a session helps consolidate learning and
correct mistakes by rehearsing the proper technique mentally.

Did you perform mental replay after this session?
Yes/No: yes

How long did you spend on mental replay? (minutes)
  Recommended: 2-5 minutes
Duration (minutes): 3

What corrections did you mentally rehearse?
  Examples:
    - 'Earlier braking in T1, smoother turn-in'
    - 'Higher apex speed in T3 with better line'
    - 'More patient throttle application in T6'
Corrections: Earlier braking in T1, smoother turn-in

Which corners did you replay with corrections? (comma-separated)
  Examples: 'T1, T3' or 'all'
Corners: T1, T3

How clear was your mental replay?
  1 = Vague/difficult, 5 = Very clear and vivid
Clarity (1-5): 4

Any additional notes? (optional, press Enter to skip)
Notes: 

✓ Post-session replay recorded
✅ Mental replay data added to 01-2025-12-20-solo.md
```

#### View Rehearsal Data

```bash
python tools/mental_rehearsal.py view weeks/week02/events/01-2025-12-20-solo.md
```

**Output:**
```
======================================================================
MENTAL REHEARSAL DATA: 01-2025-12-20-solo.md
======================================================================

📋 PRE-SESSION REHEARSAL
  Duration: 5 minutes
  Focus: T1-T3 transitions and braking points
  Corners: T1, T2, T3
  Confidence: 4/5
  Notes: Focused on smooth steering inputs

📋 POST-SESSION REPLAY
  Duration: 3 minutes
  Corrections: Earlier braking in T1, smoother turn-in
  Corners: T1, T3
  Clarity: 4/5
```

---

### Makefile Shortcuts

#### Pre-Session Rehearsal

```bash
make rehearsal-pre EVENT=weeks/week02/events/01-2025-12-20-solo.md
```

#### Post-Session Replay

```bash
make rehearsal-post EVENT=weeks/week02/events/01-2025-12-20-solo.md
```

#### View Data

```bash
make rehearsal-view EVENT=weeks/week02/events/01-2025-12-20-solo.md
```

#### Visualize Impact

```bash
make rehearsal-viz WEEK=02
```

---

## Data Schema

Mental rehearsal data is stored in the event file's frontmatter:

### Pre-Session Schema

```yaml
mental_rehearsal:
  pre_session: true
  duration_minutes: 5
  focus: "T1-T3 transitions and braking points"
  corners_rehearsed: ["T1", "T2", "T3"]  # or "all"
  confidence_rating: 4
  timestamp: "2025-12-20T10:30:00"
  notes: "Focused on smooth steering inputs"  # optional
```

### Post-Session Schema

```yaml
mental_rehearsal:
  # ... pre-session data preserved ...
  post_session: true
  duration_minutes: 3
  corrections_rehearsed: "Earlier braking in T1, smoother turn-in"
  corners_replayed: ["T1", "T3"]  # or "all"
  clarity_rating: 4
  timestamp: "2025-12-20T12:45:00"
  notes: ""  # optional
```

### No Post-Session Replay

If you didn't do post-session replay:

```yaml
mental_rehearsal:
  # ... pre-session data ...
  post_session: false
  timestamp: "2025-12-20T12:45:00"
```

---

## Visualization

### Generate Impact Analysis

```bash
python tools/visualize_rehearsal_impact.py weeks/week02
```

**Output:**
- Saved to: `weeks/week02/images/mental_rehearsal_impact.png`
- 6-panel comprehensive analysis

### Visualization Panels

1. **Rehearsal Frequency Over Time**
   - Cumulative count of pre-session and post-session practice
   - Shows adoption and consistency

2. **Rehearsal Adoption Rate**
   - Percentage of events with rehearsal
   - Bar chart comparing pre vs. post

3. **Confidence Ratings Distribution**
   - Histogram of pre-session confidence
   - Shows mean confidence level

4. **Performance Comparison**
   - Box plot: rehearsal vs. no rehearsal
   - Shows performance improvement percentage

5. **Confidence vs. Performance Correlation**
   - Scatter plot with trend line
   - Correlation coefficient displayed

6. **Rehearsal Duration Distribution**
   - Histogram of session durations
   - Shows mean duration

### Summary Statistics

The visualization script also prints summary statistics:

```
======================================================================
MENTAL REHEARSAL SUMMARY STATISTICS
======================================================================

📊 Overall Statistics:
  Total events: 10
  Events with pre-session rehearsal: 8 (80.0%)
  Events with post-session replay: 6 (60.0%)

📈 Confidence Ratings:
  Mean: 3.75
  Std Dev: 0.71
  Range: 3 - 5

⏱️  Rehearsal Duration:
  Mean: 4.2 minutes
  Std Dev: 1.1 minutes
  Range: 3 - 6 minutes

🏁 Performance Impact:
  Mean lap time without rehearsal: 85.234s
  Mean lap time with rehearsal: 84.876s
  Improvement: +0.42%
```

---

## Workflow Integration

### Recommended Daily Workflow

#### Before a Session

1. **Mental Rehearsal** (3-5 minutes)
   - Close your eyes
   - Visualize the track from driver's perspective
   - Focus on specific corners or techniques
   - Feel the car's movements and your inputs

2. **Record Rehearsal**
   ```bash
   make rehearsal-pre EVENT=weeks/week02/events/XX-date-type.md
   ```

3. **Drive the Session**

#### After a Session

1. **Mental Replay** (2-5 minutes)
   - Review mistakes mentally
   - Visualize the correct technique
   - Rehearse proper execution

2. **Record Replay**
   ```bash
   make rehearsal-post EVENT=weeks/week02/events/XX-date-type.md
   ```

3. **Complete Event Debrief**

### Weekly Review

At the end of each week:

```bash
make rehearsal-viz WEEK=02
```

Review the visualization to:
- Track rehearsal consistency
- Identify performance correlations
- Adjust rehearsal practice as needed

---

## Best Practices

### Pre-Session Rehearsal

**Duration:**
- Start with 3-5 minutes
- Quality over quantity
- Focus on clarity, not duration

**Focus:**
- Be specific (e.g., "T1 braking point" not "drive better")
- Choose 2-3 corners or one technique
- Visualize from driver's perspective

**Confidence:**
- Be honest - this is data for learning
- Low confidence is valuable information
- Track how confidence changes over time

### Post-Session Replay

**Duration:**
- 2-5 minutes is sufficient
- Do it soon after the session (within 1 hour)
- Fresh memory = better mental imagery

**Corrections:**
- Focus on 1-2 specific mistakes
- Visualize the correct technique, not the error
- Feel the proper inputs in your mind

**Clarity:**
- Rate honestly - vague imagery is normal at first
- Clarity improves with practice
- High clarity = better learning transfer

---

## Tips for Effective Mental Rehearsal

### Visualization Techniques

1. **First-Person Perspective**
   - See the track from the driver's seat
   - Include peripheral vision and mirrors
   - Feel the car's movements

2. **Multi-Sensory**
   - Hear the engine sound
   - Feel the steering feedback
   - Sense the G-forces

3. **Real-Time Speed**
   - Rehearse at actual speed, not slow motion
   - Match the timing of real laps
   - Include transitions between corners

### Building the Skill

- **Start simple**: One corner at a time
- **Increase complexity**: Chain corners together
- **Add details**: Include more sensory information
- **Track progress**: Use clarity ratings to measure improvement

### Common Mistakes

❌ **Watching from outside**: Visualize from driver's perspective  
❌ **Slow motion**: Rehearse at real speed  
❌ **Vague imagery**: Be specific about what you're practicing  
❌ **Only successes**: Also rehearse corrections for mistakes  

---

## Research References

The mental rehearsal protocol is based on:

1. **Motor Imagery Research**
   - Jeannerod, M. (1995). Mental imagery in the motor context. *Neuropsychologia*.
   - Shows mental practice activates motor cortex

2. **Expert Performance**
   - Ericsson, K. A. (2008). Deliberate practice and acquisition of expert performance.
   - Mental rehearsal is a component of deliberate practice

3. **Motorsport Applications**
   - MacIntyre, T. E., et al. (2014). Mental imagery in sport.
   - Evidence for mental practice in racing performance

---

## Troubleshooting

### "I can't visualize clearly"

**This is normal!** Mental imagery is a skill that improves with practice.

**Solutions:**
- Start with simple visualizations (one corner)
- Use recent memories (rehearse right after a session)
- Practice regularly - clarity improves over time
- Rate clarity honestly - track your progress

### "I don't have time"

**3-5 minutes is enough!**

**Solutions:**
- Do it while waiting for the session to load
- Combine with warm-up routine
- Even 2 minutes is better than nothing
- Quality > quantity

### "I'm not sure what to focus on"

**Use your event debriefs!**

**Solutions:**
- Review your last event's "areas for improvement"
- Focus on your current hypothesis
- Choose the corner you struggled with most
- Ask Little Padawan for suggestions

---

## Integration with Other Tools

Mental rehearsal works best when combined with:

- **Hypothesis Testing** (Issue #28): Test hypotheses mentally first
- **Spaced Repetition** (Issue #29): Mentally review tracks before they're due
- **Visual Scanning** (Issue #4): Rehearse eye movement patterns
- **Race Scenarios** (Issue #5): Mentally practice race situations

---

## Future Enhancements

Potential additions:

- [ ] Guided mental rehearsal scripts
- [ ] Audio cues for timing
- [ ] Track-specific rehearsal protocols
- [ ] Correlation with telemetry data
- [ ] Long-term trend analysis across seasons

---

## Questions?

See the [Technical Implementation Guide](../docs/technical_implementation_guide.md) for more details on the mental rehearsal system design.

---

## License

MIT License (same as repository)
