# AI Bug Investigator - Evaluation Results

## Purpose

This folder contains evaluation artifacts comparing Prompt V1 and Prompt V2 performance.

A hiring manager or reviewer can use these files to quickly understand:
- evaluation methodology
- dataset size
- scoring approach
- performance differences

---

## Methodology

### Dataset

- 20 software bug scenarios were evaluated.
- Scenarios included:
  - memory leaks
  - race conditions
  - dependency conflicts
  - authentication failures
  - database failures
  - frontend bugs
  - production issues

### Evaluation Modes

Each bug was tested using:

- Quick mode
- Full investigation mode

### Metrics

The system was evaluated on:

1. Root cause accuracy
2. Suggested fix quality
3. Total investigation score
4. Response latency

### Comparison

Prompt V1 and Prompt V2 were evaluated using the same dataset and scoring criteria.

The JSON file contains the complete comparison data.

---

## Result Summary

Prompt V2 introduced:
- stricter JSON output formatting
- stronger debugging investigation rules
- better structured responses

Current evaluation shows:
- slightly lower aggregate score
- significantly higher latency

Future improvements should focus on optimizing prompt complexity while maintaining investigation quality.