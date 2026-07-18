# Failure Analysis v2

## Overview
Evaluation of AI Bug Investigator after prompt version 2.0.0.

## Observed Failures

### 1. Incorrect Root Cause
Problem:
The model sometimes gives a technically possible but incorrect root cause.

Example:
Hidden trailing whitespace bug.

Issue:
The model assumed complex build issues instead of simple whitespace validation.

Improvement:
Add more specific examples in prompts and evaluation data.

---

### 2. Generic Fix Recommendations
Problem:
Some fixes are too broad.

Example:
"Add better testing."

Improvement:
Require concrete commands, tools, and code-level fixes.

---

### 3. Missing Context Handling
Problem:
When bug details are limited, model makes assumptions.

Improvement:
Force model to clearly mark assumptions.

---

## Next Improvements

- Add more edge cases
- Improve evaluation dataset
- Add stricter JSON validation
- Improve prompt instructions