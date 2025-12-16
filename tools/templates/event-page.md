---
event: { { event_num } }
week: "{{week}}"
date: "{{date}}"
type: "{{type}}"
---

# Event #{{event_num}} – {{date}} – {{type}}

[← Back to Week {{week}}](../README.md) | **[Garage 61 Event Page](https://garage61.net/app/event/{{garage_event_id}})**

## Quick Stats

| Metric              | Value          |
| ------------------- | -------------- |
| **Laps**            | {{laps}}       |
| **Best Lap**        | {{best}}s      |
| **Optimal**         | {{optimal}}s   |
| **Settled Pace**    | {{settled}}s   |
| **Consistency (σ)** | {{sigma}}s     |
| **Clean Laps**      | {{clean_pct}}% |

## Lap Times

![Lap Progression](../images/event-{{event_num_pad}}-laptimes.png)

{{#if telemetry}}

## Telemetry Analysis

![Telemetry](../images/event-{{event_num_pad}}-telemetry.png)

### Pedal Usage

- Full throttle: {{throttle_pct}}%
- Braking: {{brake_pct}}%
- Coasting: {{coast_pct}}%
  {{/if}}

## Debrief

**The Facts:**

- _What happened objectively?_

**The Feelings:**

- _How did it feel? Confidence? Flow?_

**Focus for Next Event:**

1. _First priority_
2. _Second priority_

---

[← Back to Week {{week}}](../README.md) | [Next Event →](./{{next_event}}.md)
