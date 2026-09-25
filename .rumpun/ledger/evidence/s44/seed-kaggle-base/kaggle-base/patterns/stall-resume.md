# Stall resume

A hung cycle costs one cycle, not the scope.

Rule: when a cycle stops on a hang, its successor resumes the identical
scope. Every worker budget rises to the parent's budget times 1.5, rounded
up to whole minutes. The successor's header cites the hang it resumes, so
the record shows scope continuity and the budget cause. A clean cycle
drafts its successor identically to the base template — the 1.5x raise
fires only on hangs.

Generalized from: the stall-resume pattern of a prior verification
campaign — a drafting rule that retired a manual re-scope ritual after
three recorded hand-resumes preceded the mechanization.
