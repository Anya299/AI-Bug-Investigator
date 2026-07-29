# Week 3 Product Decision: Richer Bug Context Collection

## Decision

Add more structured context fields before generating a bug investigation report.

## Reason

Developer feedback showed that a bug description alone is often not enough.

The accuracy of debugging depends on understanding:

- where the bug happens
- what environment it runs in
- how to reproduce it
- what changed before the failure

## New Input Fields

The bug report form should collect:

1. Programming Language
2. Framework
3. Environment
   - Local
   - Staging
   - Production

4. Error Message / Stack Trace

5. Steps to Reproduce

6. Expected Behavior

7. Actual Behavior

8. Recent Changes

## Expected Benefit

More context should help the AI:
- generate more relevant root causes
- reduce generic suggestions
- provide better investigation steps

## Priority

High priority for Week 3.