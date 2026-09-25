# The band-mask guard

An outcome band must state the evidence that would show the work landed.

Rule: when a cycle's metric counts integration (shipped units wired into
the deliverable), the cycle's expected band must say where that
integration shows: the suite, the tests, the repro that must pass. A band
that never defines integration masks value: units ship while the record
claims nothing measurable, and audits cannot catch the gap.

The guard warns at lint time when an integration-shaped metric pairs with
a band carrying none of the integration-evidence tokens. Auditors treat
the warning as a masking signal, so vague bands cannot silently recur.

Generalized from: the band-mask-guard pattern of a prior verification
campaign — a lint warning that closed an audit's value-masking finding by
demanding integration evidence inside expected bands.
