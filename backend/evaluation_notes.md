# Prompt Version 2 Evaluation

## Prompt Version
2.0.0

## Changes Made

- Added strict JSON output
- Added senior debugging role
- Added technical investigation steps
- Added tool and command suggestions
- Added assumption handling

## Observations

The AI output quality improved:
- More detailed investigation steps
- More technical fixes
- Better debugging reasoning

## Evaluation Issue

Current evaluator uses exact keyword matching.

Problem:
AI may use different technical words with the same meaning.

Example:

Expected:
memory allocation issue

AI:
memory exhaustion

Both represent the same concept.

## Improvement Needed

Future evaluator should use:
- semantic similarity
- embedding comparison
- LLM judge evaluation

## Conclusion

Prompt v2 improves debugging responses, but evaluation needs semantic scoring.