---
week: {{week}}
track: "{{track}}"
layout: "{{layout}}"
season: "2026 Season 1"
series: "Ray FF1600 Rookie Fixed"
schedule:
  start: "{{start_date}}"
  end: "{{end_date}}"
---

# Week {{week}} – {{track}} – {{layout}}

> Track dossier: [{{track}}](../../tracks/{{track_file}})

> **Intent:** _{{intent}}_

## Events

| # | Date | Type | Laps | Best | σ | Notes | Details |
|---|------|------|------|------|---|-------|---------|
{{events_table}}

## Week Progress

![Week Progress](../../images/week{{week}}/week-progress.png)

{{#if lap_comparison}}
### Lap Comparison (Best Laps)

![Lap Comparison](../../images/week{{week}}/lap-comparison.png)
{{/if}}

## Summary

{{summary}}

## Reflection

- Track craft takeaways: ...
- Brake bias learnings: ...
- Driver mindset notes: ...

### Next Week Intent

- _Seed a sentence for next week..._

---

[← Back to Season](../../README.md)

