# Spaced Repetition System for Track Knowledge

## Overview

The **Spaced Repetition System (SRS)** applies cognitive science principles to consolidate track knowledge into long-term memory. Using the proven SM-2 algorithm, it schedules reviews at optimal intervals to maximize retention while minimizing study time.

This system helps you remember:
- Corner techniques and racing lines
- Braking points and reference markers
- Track-specific strategies
- Racecraft patterns
- Technical details that fade without review

## Scientific Background

### The Spacing Effect

Research in cognitive psychology has consistently shown that **spaced repetition** is the most effective method for long-term retention:

> "Spaced practice produces better long-term retention than massed practice, even when total study time is equated." — Cepeda et al. (2006)

The **spacing effect** works because:
1. **Retrieval strengthens memory**: Each successful recall makes the memory stronger
2. **Optimal difficulty**: Reviews scheduled just before forgetting maximize learning
3. **Consolidation time**: Spacing allows neural connections to stabilize

### The SM-2 Algorithm

This system implements the **SM-2 (SuperMemo 2)** algorithm, developed by Piotr Woźniak in 1987 and used by millions of learners worldwide.

**Key principles:**
- **Easiness Factor (EF)**: Tracks how easy a card is to remember (1.3-2.5+)
- **Interval**: Days until next review, grows exponentially for well-remembered items
- **Quality Rating**: Self-assessment (0-5) after each review

**The algorithm:**
1. First review: 1 day
2. Second review: 6 days
3. Subsequent reviews: Previous interval × Easiness Factor

If you forget (quality < 3), the card resets to day 1.

### Evidence from Research

- **Cepeda et al. (2006)**: Meta-analysis of 317 experiments confirms spacing effect
- **Karpicke & Roediger (2008)**: Retrieval practice (testing) is more effective than re-reading
- **Dunlosky et al. (2013)**: Distributed practice rated as "high utility" learning technique

## Features

### 1. Knowledge Card Creation
- Interactive prompts for adding new cards
- Organized by track and category
- Question/answer format for active recall

### 2. SM-2 Scheduling
- Automatic calculation of optimal review intervals
- Adapts to your performance (easier cards reviewed less often)
- Resets forgotten cards for intensive re-learning

### 3. Review Sessions
- Interactive review with self-assessment
- Immediate feedback on next review date
- Progress tracking (cards reviewed, retention rate)

### 4. Analytics & Visualization
- Retention rate by track and category
- Review schedule (next 30 days)
- Easiness factor distribution
- Learning curve over time
- Review activity patterns

## Installation

No additional dependencies required. Uses existing tools:
- `dataclasses` for card representation
- `matplotlib` and `seaborn` for visualizations

## Usage

### Add a Knowledge Card

```bash
make srs-add
```

**Interactive prompts:**

```
======================================================================
ADD NEW KNOWLEDGE CARD
======================================================================

Spaced repetition helps consolidate track knowledge into long-term memory.
Create cards for corners, braking points, racing lines, and techniques.

Which track is this knowledge for?
  Examples: 'Summit Point Jefferson Circuit', 'Watkins Glen'
Track: Summit Point Jefferson Circuit

What category does this knowledge belong to?
  1 = Corner technique
  2 = Braking point
  3 = Racing line
  4 = General technique
  5 = Racecraft/strategy
Category (1-5): 2

Question (what you're trying to remember):
  Examples:
    - 'What is the optimal braking point for T1?'
    - 'What line maximizes exit speed in T3?'
    - 'How should I approach T6-T7 complex?'
Question: What is the optimal braking point for T1?

Answer (the knowledge you want to remember):
  Be specific and detailed. Include landmarks, techniques, etc.
Answer: Brake at the 2 board (200ft marker). Trail brake to apex. Reference: large crack in pavement on left.

✅ Knowledge card #1 created
   Track: Summit Point Jefferson Circuit
   Category: braking

💡 Review it now with: make srs-review
```

### Review Due Cards

```bash
make srs-review
```

**Interactive review session:**

```
======================================================================
REVIEW SESSION - 3 card(s) due
======================================================================

Rate your recall quality:
  0 = Complete blackout, no recall
  1 = Incorrect, but familiar
  2 = Incorrect, but close
  3 = Correct with difficulty
  4 = Correct after hesitation
  5 = Perfect recall

======================================================================
Card 1/3
======================================================================

📍 Track: Summit Point Jefferson Circuit
📂 Category: braking

❓ What is the optimal braking point for T1?

Press Enter to reveal answer...

✅ Brake at the 2 board (200ft marker). Trail brake to apex. Reference: large crack in pavement on left.

Quality (0-5): 5
  📅 Next review: in 6 days (2025-12-25)

======================================================================
Card 2/3
======================================================================
[...]

======================================================================
✅ Review session complete! Reviewed 3 card(s)
======================================================================
```

### List Knowledge Cards

```bash
# List all cards
make srs-list

# List cards for specific track
make srs-list TRACK="Summit Point"

# List only due cards
make srs-list DUE=yes
```

**Example output:**

```
======================================================================
KNOWLEDGE CARDS
======================================================================

🏁 Summit Point Jefferson Circuit (5 cards, 2 due)
  #1: What is the optimal braking point for T1?...
       🔴 DUE | braking | Retention: 100% | Reviews: 3
  #2: What line maximizes exit speed in T3?...
       📅 2025-12-22 | racing_line | Retention: 80% | Reviews: 5
  #3: How should I approach T6-T7 complex?...
       🔴 DUE | corner | Retention: 75% | Reviews: 4
  #4: What is the key to consistency in T4?...
       📅 2025-12-28 | technique | Retention: 100% | Reviews: 2
  #5: When is it safe to overtake into T1?...
       📅 2025-12-30 | racecraft | Retention: New | Reviews: 0
```

### Show Statistics

```bash
make srs-stats
```

**Example output:**

```
======================================================================
SPACED REPETITION SYSTEM STATISTICS
======================================================================

📊 Overall:
   Total Cards: 15
   Due for Review: 3
   Up to Date: 12

📈 Performance:
   Total Reviews: 47
   Correct Reviews: 42
   Overall Retention: 89.4%
   Average Easiness Factor: 2.68

🏁 By Track:
   Summit Point Jefferson Circuit: 5 cards (2 due)
   Watkins Glen: 4 cards (1 due)
   Road Atlanta: 6 cards (0 due)

📂 By Category:
   braking: 6
   corner: 4
   racing_line: 3
   technique: 1
   racecraft: 1

📅 Next Review:
   Tomorrow
```

### Visualize SRS Data

```bash
make srs-viz
```

**Generates:**
- `coaching/srs_analysis.png` with 6-panel visualization
- Summary statistics printed to console

**Visualization panels:**
1. **Retention Rate by Track**: Bar chart showing which tracks you know best
2. **Retention Rate by Category**: Bar chart by knowledge type
3. **Review Schedule**: Next 30 days of due cards
4. **Easiness Factor Distribution**: Histogram showing card difficulty
5. **Learning Curve**: Cumulative cards added over time
6. **Review Activity**: Bar chart of reviews completed over time

## Workflow Integration

### Daily Workflow

**Morning (5 minutes):**
```bash
make srs-review
```
Review any cards due today. The SM-2 algorithm ensures you only see cards that need reinforcement.

### After Practice/Race

**Add new knowledge immediately:**
```bash
make srs-add
```

**Why?** Fresh memories are easier to encode. If you learned something important during a session, add it as a card while it's still vivid.

### Weekly Review

**Check statistics:**
```bash
make srs-stats
make srs-viz
```

Monitor your retention rates and identify weak areas.

### Pre-Event Preparation

**Review track-specific cards:**
```bash
make srs-list TRACK="Summit Point" DUE=yes
```

Before racing at a track, review all due cards for that track to refresh your memory.

## Best Practices

### Creating Effective Cards

**✅ Good cards:**
- **Atomic**: One concept per card
- **Specific**: Include landmarks, reference points
- **Testable**: Can you recall the answer without seeing it?
- **Actionable**: Practical knowledge you can apply

**Example (Good):**
```
Q: What is the optimal braking point for T1 at Summit Point?
A: Brake at the 2 board (200ft marker). Trail brake to apex. 
   Reference: large crack in pavement on left.
```

**❌ Bad cards:**
- **Vague**: "How do I drive T1?" (too broad)
- **Passive**: "T1 is a fast corner" (not a question)
- **Multiple concepts**: "What are the braking points for T1, T2, and T3?" (split into 3 cards)

### Honest Self-Assessment

The system only works if you're honest about your recall quality:

- **5 (Perfect)**: Instant recall, no hesitation
- **4 (Good)**: Recalled after brief thought
- **3 (Difficult)**: Struggled but got it right
- **2 (Wrong but close)**: Knew the general idea
- **1 (Familiar)**: Recognized it but couldn't recall
- **0 (Blackout)**: No idea

**Don't be too harsh or too lenient.** Accurate ratings lead to optimal scheduling.

### Consistency is Key

**The spacing effect requires consistency:**
- Review daily (even if just 5 minutes)
- Don't skip reviews (defeats the purpose of spacing)
- Add cards regularly as you learn new things

**Better:** 5 minutes every day  
**Worse:** 1 hour once a week

### Categories Guide

**Corner**: Specific corner techniques
- "How should I approach T3?"
- "What's the key to a fast T6?"

**Braking**: Braking points and techniques
- "Where do I brake for T1?"
- "What's the trail braking strategy for T4?"

**Racing Line**: Optimal lines and positioning
- "What line maximizes exit speed in T7?"
- "Where should I position for T1-T2 complex?"

**Technique**: General driving techniques
- "How do I maintain consistency in T4?"
- "What's the key to smooth throttle application?"

**Racecraft**: Strategy and race situations
- "When is it safe to overtake into T1?"
- "How should I defend position in T3?"

## The SM-2 Algorithm in Detail

### Easiness Factor (EF)

Starts at **2.5** for all new cards. After each review:

```
EF' = EF + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
```

Where `q` is quality (0-5).

**Effect:**
- Quality 5: EF increases (card gets easier)
- Quality 4: EF slightly increases
- Quality 3: EF slightly decreases
- Quality 0-2: EF decreases significantly

Minimum EF is **1.3** (even very difficult cards eventually space out).

### Interval Calculation

**First review:** 1 day  
**Second review:** 6 days  
**Subsequent reviews:** `Previous Interval × EF`

**Example progression (Quality 5 each time, EF = 2.5):**
- Review 1: 1 day
- Review 2: 6 days
- Review 3: 15 days (6 × 2.5)
- Review 4: 38 days (15 × 2.5)
- Review 5: 95 days (38 × 2.5)

**If you forget (Quality < 3):**
- Interval resets to 0 (review again today)
- Repetitions reset to 0
- EF decreases (card becomes "harder")

### Why SM-2 Works

1. **Exponential spacing**: Intervals grow rapidly for well-known items
2. **Adaptive difficulty**: EF adjusts based on your performance
3. **Forgetting curve**: Reviews scheduled just before predicted forgetting
4. **Efficient**: Minimizes reviews while maximizing retention

## Data Storage

### Knowledge Cards Database

All cards are stored in `coaching/knowledge_cards.json`:

```json
{
  "cards": [
    {
      "id": 1,
      "track": "Summit Point Jefferson Circuit",
      "category": "braking",
      "question": "What is the optimal braking point for T1?",
      "answer": "Brake at the 2 board (200ft marker). Trail brake to apex. Reference: large crack in pavement on left.",
      "created_at": "2025-12-19T10:00:00",
      "easiness_factor": 2.6,
      "interval": 6,
      "repetitions": 2,
      "next_review": "2025-12-25T10:00:00",
      "last_reviewed": "2025-12-19T10:00:00",
      "total_reviews": 2,
      "correct_reviews": 2
    }
  ],
  "next_id": 2
}
```

## Examples

### Example 1: Braking Point

```
Q: What is the optimal braking point for T1 at Summit Point?
A: Brake at the 2 board (200ft marker). Trail brake to apex. 
   Reference: large crack in pavement on left.

Category: braking
Track: Summit Point Jefferson Circuit

Review history:
- Day 1: Quality 4 → Next review: 6 days
- Day 7: Quality 5 → Next review: 15 days
- Day 22: Quality 5 → Next review: 38 days
```

### Example 2: Racing Line

```
Q: What line maximizes exit speed in T3?
A: Enter wide (outside), apex late (inside), exit wide (outside).
   Key: Patient throttle application at apex. Don't rush it.

Category: racing_line
Track: Summit Point Jefferson Circuit

Review history:
- Day 1: Quality 3 → Next review: 6 days
- Day 7: Quality 4 → Next review: 14 days
- Day 21: Quality 5 → Next review: 35 days
```

### Example 3: Racecraft

```
Q: When is it safe to overtake into T1 at Summit Point?
A: Only if you have significant overlap (front axle past their rear axle) 
   by the 3 board. Otherwise, wait for T3 (safer passing zone).

Category: racecraft
Track: Summit Point Jefferson Circuit

Review history:
- Day 1: Quality 2 (forgot) → Reset to day 1
- Day 1: Quality 3 → Next review: 6 days
- Day 7: Quality 4 → Next review: 13 days
```

## Troubleshooting

### "No cards due for review"

This is good! It means you're up to date. The system will tell you when the next review is due.

To add more cards:
```bash
make srs-add
```

### Cards are too easy (always Quality 5)

This is normal for well-learned material. The intervals will grow exponentially, and you'll see these cards less often.

If a card is truly trivial, you can delete it from `coaching/knowledge_cards.json`.

### Cards are too hard (always Quality 0-2)

The card might be:
- **Too broad**: Split into multiple cards
- **Too vague**: Add more specific details to the answer
- **Not practiced**: The knowledge might not be consolidated yet

Try reviewing the card in practice, then update the answer with more details.

### Too many cards due

This happens if:
- You skipped reviews for several days
- You added many cards at once

**Solution:** Do a "catch-up" session. The algorithm will adapt, and cards you know well will space out quickly.

## Advanced Usage

### Bulk Import

To import many cards at once, edit `coaching/knowledge_cards.json` directly:

```json
{
  "cards": [
    {
      "id": 1,
      "track": "Summit Point Jefferson Circuit",
      "category": "braking",
      "question": "What is the optimal braking point for T1?",
      "answer": "Brake at the 2 board...",
      "created_at": "2025-12-19T10:00:00",
      "easiness_factor": 2.5,
      "interval": 0,
      "repetitions": 0,
      "next_review": "2025-12-19T10:00:00",
      "last_reviewed": null,
      "total_reviews": 0,
      "correct_reviews": 0
    }
  ],
  "next_id": 2
}
```

### Export for Analysis

The JSON database can be analyzed with external tools:

```python
import json
import pandas as pd

with open('coaching/knowledge_cards.json') as f:
    data = json.load(f)

df = pd.DataFrame(data['cards'])
print(df[['track', 'category', 'easiness_factor', 'total_reviews']])
```

### Integration with Track Dossiers

When creating track dossiers, extract key knowledge into SRS cards:

```bash
# After creating a track dossier
make srs-add
# Add cards for each critical corner, braking point, etc.
```

## References

- Cepeda, N. J., Pashler, H., Vul, E., Wixted, J. T., & Rohrer, D. (2006). Distributed practice in verbal recall tasks: A review and quantitative synthesis. *Psychological Bulletin*, 132(3), 354-380.
- Karpicke, J. D., & Roediger, H. L. (2008). The critical importance of retrieval for learning. *Science*, 319(5865), 966-968.
- Dunlosky, J., Rawson, K. A., Marsh, E. J., Nathan, M. J., & Willingham, D. T. (2013). Improving students' learning with effective learning techniques: Promising directions from cognitive and educational psychology. *Psychological Science in the Public Interest*, 14(1), 4-58.
- Woźniak, P. A., & Gorzelańczyk, E. J. (1994). Optimization of repetition spacing in the practice of learning. *Acta Neurobiologiae Experimentalis*, 54, 59-62.

## See Also

- `README_MENTAL_REHEARSAL.md` - Mental practice protocol
- `README_HYPOTHESIS_TESTING.md` - Experimental learning framework
- Issue #29 on GitHub for development roadmap

---

**Remember**: The goal is not to memorize everything, but to consolidate critical knowledge that fades without review. Focus on high-value information: braking points, racing lines, and track-specific techniques that directly impact lap times.

Happy learning! 🧠🏎️
