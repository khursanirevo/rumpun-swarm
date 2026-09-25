# The writer owes the exit artifact and the engine marks the gap

## The prior

A writer exits only after writing its notes artifact at the workspace
root. The campaign twice saw exit code 0 with the artifact absent and
only the brief's REQUIRED clause standing guard. The engine now
machine-marks the gap: once the exit code is read, an exited writer
without its notes file carries an additive mark naming the gap. State
and exit code stay the measured values.

## Why this holds

Exit code 0 is not completion. A prose guard degrades silently: the
brief's REQUIRED clause stood as the only guard twice and failed
twice. The additive mark turns the missing artifact into an engine
observation at exit read, not an audit-time discovery. Present notes
change nothing, so the gate cannot fire on a compliant writer.

## How to apply

- Write the notes artifact before exiting. A partial artifact naming the state beats silence.
- A REQUIRED clause in prose is a request. The machine mark is the gate.
- The mark is additive: measured fields stay measured, and the mark names the gap only.
- Failed and crashed writers keep the failure vocabulary. The mark belongs to exited writers only.
