# Evaluation System Audit

## Current Scoring Method

The evaluation system currently uses a single score_percent value to measure AI bug analysis quality.

Metrics:
- Average Score
- Accuracy (score >= 50%)

## Identified Failure Modes

### 1. Single blended score

A single score hides the reason behind failures.

Example:
A 40% score does not show whether:
- Root cause was incorrect
- Fix recommendation was wrong
- Investigation steps were incomplete
- Explanation was unclear

### 2. No category-level evaluation

The system cannot separately measure:

- Root cause accuracy
- Fix quality
- Investigation usefulness
- Explanation quality

### 3. Limited prompt improvement feedback

Because failures are not categorized, improving prompts becomes guesswork.

## Proposed Improvement

Replace single scoring with component-based evaluation:

- Root cause score
- Fix recommendation score
- Investigation steps score
- Explanation score

Then calculate overall score from these components.

## Aggregate Statistics (Prompt V1 vs Prompt V2)

| Metric               |    V1 |      V2 |   Change |
| -------------------- | ----: | ------: | -------: |
| Root score (mean)    |  2.31 |    2.21 |    -0.10 |
| Root score (median)  |  2.00 |    2.00 |     0.00 |
| Fix score (mean)     |  1.77 |    1.58 |    -0.19 |
| Fix score (median)   |  2.00 |    1.00 |    -1.00 |
| Total score (mean)   |  4.09 |    3.79 |    -0.30 |
| Total score (median) |  4.00 |    4.00 |     0.00 |
| Latency (mean, ms)   | 22.78 | 2014.79 | +1992.01 |
| Latency (median, ms) | 20.68 | 2012.99 | +1992.31 |

### Observation

Prompt V2 introduced stricter JSON formatting, evidence grounding, and mode-based behavior. However, aggregate scores slightly decreased compared to V1, mainly due to stricter evaluation criteria and increased latency from additional reasoning steps.