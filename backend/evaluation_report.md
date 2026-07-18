# AI Bug Investigator Evaluation Report v1


## Dataset

Total test cases: 10

Source:
Reddit developer debugging cases collected during Week 1 research.


## Evaluation Goal

Measure whether the AI debugging assistant can:

- Identify probable root causes
- Suggest correct debugging direction
- Provide actionable fixes
- Handle difficult debugging scenarios


# Results Summary


## Successful Analysis

The AI successfully analyzed:

- Race condition
- CSS overflow issue
- Debugger/compiler mismatch
- Dependency conflicts
- DLL mismatch
- Legacy code issues


## Failed Parsing Cases

### ID 1
Bug:
Memory leak causing application crash after 48+ hours

Problem:
AI response could not be parsed.

Improvement:
Need stricter JSON output handling.


### ID 3

Bug:
Hidden trailing whitespace causing code failure

Problem:
AI response format failure.

Improvement:
Improve prompt formatting rules.


### ID 6

Bug:
Confusing stack trace pointing wrong direction

Problem:
AI response parsing failed.

Improvement:
Add stack trace analysis examples.


# Model Problems Found


## 1. Incorrect Root Cause Prediction

Example:

Input:
Old undocumented code causing issue


AI prediction:
Race condition


Expected:

Legacy code / technical debt


Solution:

Add more legacy debugging examples.


## 2. Overly Long Responses

Problem:

AI sometimes generates very detailed answers.

Impact:

JSON parsing failures.


Solution:

Reduce output length using stricter prompt.


## 3. Missing Confidence Scoring

Current output:

Single root cause.


Expected:

Top 3 possible causes with:

- Evidence
- Confidence score


Solution:

Update system prompt.


# Improvements for Prompt Version 2


Changes:

1. Force JSON only output

2. Limit investigation steps to maximum 5

3. Add confidence scores

4. Rank multiple possible causes

5. Avoid guessing when information is missing


# Next Step

Create Prompt Version 2 and compare:

Prompt v1 vs Prompt v2

using the same 10 evaluation cases.